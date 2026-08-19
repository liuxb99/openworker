package main

import (
	"bytes"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"io"
	"net/http"
	"os"
	"sort"
	"strings"
	"time"
)

type workflowRun struct {
	ID        int64     `json:"id"`
	Name      string    `json:"name"`
	Status    string    `json:"status"`
	CreatedAt time.Time `json:"created_at"`
}
type runsResponse struct {
	WorkflowRuns []workflowRun `json:"workflow_runs"`
}
type apiAttempt struct {
	Attempted  bool   `json:"attempted"`
	StatusCode int    `json:"status_code,omitempty"`
	Outcome    string `json:"outcome"`
	Error      string `json:"error,omitempty"`
}
type runOperation struct {
	RunID           int64      `json:"run_id"`
	Name            string     `json:"name"`
	Status          string     `json:"status"`
	CreatedAt       string     `json:"created_at"`
	Stuck           bool       `json:"stuck"`
	StuckAgeSeconds int64      `json:"stuck_age_seconds"`
	Cancel          apiAttempt `json:"cancel"`
	ForceCancel     apiAttempt `json:"force_cancel"`
	Delete          apiAttempt `json:"delete_stuck_run"`
}
type result struct {
	SchemaVersion     string         `json:"schema_version"`
	Repository        string         `json:"repository"`
	RunID             string         `json:"run_id,omitempty"`
	SourceSHA         string         `json:"source_sha,omitempty"`
	NonterminalBefore []workflowRun  `json:"nonterminal_before"`
	Operations        []runOperation `json:"operations"`
	CancelledIDs      []int64        `json:"cancelled_ids"`
	DeletedIDs        []int64        `json:"deleted_ids"`
	RemainingAfter    []workflowRun  `json:"remaining_after"`
	Outcome           string         `json:"outcome"`
	VerifiedAt        string         `json:"verified_at"`
}
type githubClient struct {
	token, repo, baseURL string
	http                 *http.Client
	now                  func() time.Time
}

func main() {
	repo := flag.String("repo", strings.TrimSpace(os.Getenv("GITHUB_REPOSITORY")), "repository owner/name")
	token := flag.String("token", firstNonEmpty(os.Getenv("OPENWORKER_GITHUB_TOKEN"), os.Getenv("GH_TOKEN"), os.Getenv("GITHUB_TOKEN")), "token with Actions write")
	timeout := flag.Duration("timeout", 7*time.Minute, "verification timeout")
	poll := flag.Duration("poll", 5*time.Second, "verification poll interval")
	stuckAfter := flag.Duration("stuck-after", 30*time.Minute, "minimum age permitting delete after both cancels fail")
	exclude := flag.Int64("exclude-run-id", 0, "run id to preserve")
	runID := flag.String("run-id", os.Getenv("GITHUB_RUN_ID"), "evidence run id")
	sourceSHA := flag.String("source-sha", os.Getenv("GITHUB_SHA"), "evidence source SHA")
	flag.Parse()
	if strings.TrimSpace(*repo) == "" || !strings.Contains(*repo, "/") {
		fail(errors.New("-repo owner/name is required"))
	}
	if strings.TrimSpace(*token) == "" {
		fail(errors.New("GitHub token required"))
	}
	if *timeout <= 0 || *poll <= 0 || *stuckAfter < 0 {
		fail(errors.New("invalid duration"))
	}
	c := githubClient{token: strings.TrimSpace(*token), repo: strings.TrimSpace(*repo), baseURL: "https://api.github.com", http: &http.Client{Timeout: 20 * time.Second}, now: time.Now}
	out, err := clearQueue(c, *exclude, *timeout, *poll, *stuckAfter)
	if err != nil {
		fail(err)
	}
	out.RunID = *runID
	out.SourceSHA = *sourceSHA
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	_ = enc.Encode(out)
	if out.Outcome != "PASS" {
		os.Exit(1)
	}
}

func clearQueue(c githubClient, exclude int64, timeout, poll, stuckAfter time.Duration) (result, error) {
	before, err := c.nonterminalRuns()
	if err != nil {
		return result{}, err
	}
	out := result{SchemaVersion: "openworker.github-actions-queue-clear/v2", Repository: c.repo, NonterminalBefore: filterRuns(before, exclude)}
	for _, run := range out.NonterminalBefore {
		op := runOperation{RunID: run.ID, Name: run.Name, Status: run.Status, CreatedAt: run.CreatedAt.UTC().Format(time.RFC3339)}
		op.StuckAgeSeconds = int64(c.now().Sub(run.CreatedAt).Seconds())
		op.Stuck = op.StuckAgeSeconds >= int64(stuckAfter.Seconds())
		op.Cancel = c.mutate(http.MethodPost, fmt.Sprintf("/repos/%s/actions/runs/%d/cancel", c.repo, run.ID))
		if op.Cancel.Outcome == "success" {
			out.CancelledIDs = append(out.CancelledIDs, run.ID)
		} else {
			op.ForceCancel = c.mutate(http.MethodPost, fmt.Sprintf("/repos/%s/actions/runs/%d/force-cancel", c.repo, run.ID))
			if op.ForceCancel.Outcome == "success" {
				out.CancelledIDs = append(out.CancelledIDs, run.ID)
			} else if op.Stuck {
				op.Delete = c.mutate(http.MethodDelete, fmt.Sprintf("/repos/%s/actions/runs/%d", c.repo, run.ID))
				if op.Delete.Outcome == "success" {
					out.DeletedIDs = append(out.DeletedIDs, run.ID)
				}
			} else {
				op.Delete = apiAttempt{Outcome: "not_stuck"}
			}
		}
		out.Operations = append(out.Operations, op)
	}
	sort.Slice(out.CancelledIDs, func(i, j int) bool { return out.CancelledIDs[i] < out.CancelledIDs[j] })
	sort.Slice(out.DeletedIDs, func(i, j int) bool { return out.DeletedIDs[i] < out.DeletedIDs[j] })
	deadline := c.now().Add(timeout)
	for {
		runs, e := c.nonterminalRuns()
		if e != nil {
			return out, e
		}
		out.RemainingAfter = filterRuns(runs, exclude)
		if len(out.RemainingAfter) == 0 || !c.now().Before(deadline) {
			break
		}
		time.Sleep(poll)
	}
	out.Outcome = "PASS"
	if len(out.RemainingAfter) != 0 {
		out.Outcome = "FAIL"
	}
	out.VerifiedAt = c.now().UTC().Format(time.RFC3339)
	return out, nil
}
func filterRuns(runs []workflowRun, exclude int64) []workflowRun {
	out := make([]workflowRun, 0, len(runs))
	for _, r := range runs {
		if r.ID != exclude {
			out = append(out, r)
		}
	}
	return out
}
func (c githubClient) nonterminalRuns() ([]workflowRun, error) {
	var all []workflowRun
	for page := 1; ; page++ {
		var rr runsResponse
		path := fmt.Sprintf("%s/repos/%s/actions/runs?per_page=100&page=%d", c.baseURL, c.repo, page)
		if err := c.doJSON(http.MethodGet, path, nil, &rr); err != nil {
			return nil, err
		}
		for _, r := range rr.WorkflowRuns {
			if !strings.EqualFold(strings.TrimSpace(r.Status), "completed") {
				all = append(all, r)
			}
		}
		if len(rr.WorkflowRuns) < 100 {
			break
		}
	}
	sort.Slice(all, func(i, j int) bool { return all[i].ID < all[j].ID })
	return all, nil
}
func (c githubClient) mutate(method, path string) apiAttempt {
	a := apiAttempt{Attempted: true}
	req, err := http.NewRequest(method, c.baseURL+path, bytes.NewReader(nil))
	if err != nil {
		a.Outcome = "error"
		a.Error = err.Error()
		return a
	}
	c.headers(req)
	resp, err := c.http.Do(req)
	if err != nil {
		a.Outcome = "error"
		a.Error = err.Error()
		return a
	}
	defer resp.Body.Close()
	body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
	a.StatusCode = resp.StatusCode
	if resp.StatusCode/100 == 2 || resp.StatusCode == http.StatusConflict || resp.StatusCode == http.StatusNotFound {
		a.Outcome = "success"
		return a
	}
	a.Outcome = "failed"
	a.Error = strings.TrimSpace(string(body))
	return a
}
func (c githubClient) doJSON(method, path string, body io.Reader, out any) error {
	req, err := http.NewRequest(method, path, body)
	if err != nil {
		return err
	}
	c.headers(req)
	resp, err := c.http.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()
	data, err := io.ReadAll(io.LimitReader(resp.Body, 8<<20))
	if err != nil {
		return err
	}
	if resp.StatusCode/100 != 2 {
		return fmt.Errorf("GitHub HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(data)))
	}
	if out != nil {
		return json.Unmarshal(data, out)
	}
	return nil
}
func (c githubClient) headers(req *http.Request) {
	req.Header.Set("Authorization", "Bearer "+c.token)
	req.Header.Set("Accept", "application/vnd.github+json")
	req.Header.Set("X-GitHub-Api-Version", "2022-11-28")
	req.Header.Set("User-Agent", "OpenWorker-actions-queue-clear")
}
func firstNonEmpty(v ...string) string {
	for _, s := range v {
		if strings.TrimSpace(s) != "" {
			return strings.TrimSpace(s)
		}
	}
	return ""
}
func fail(err error) {
	fmt.Fprintln(os.Stderr, "OPENWORKER_ACTIONS_QUEUE_CLEAR_FAIL:", err)
	os.Exit(1)
}
