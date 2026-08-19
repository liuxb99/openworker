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
    ID     int64  `json:"id"`
    Name   string `json:"name"`
    Status string `json:"status"`
}

type runsResponse struct {
    WorkflowRuns []workflowRun `json:"workflow_runs"`
}

type result struct {
    SchemaVersion    string        `json:"schema_version"`
    Repository       string        `json:"repository"`
    NonterminalBefore int          `json:"nonterminal_before"`
    CancelledIDs     []int64       `json:"cancelled_ids"`
    RemainingAfter   []workflowRun `json:"remaining_after"`
    Outcome          string        `json:"outcome"`
    VerifiedAt       string        `json:"verified_at"`
}

type githubClient struct {
    token string
    repo  string
    http  *http.Client
}

func main() {
    repo := flag.String("repo", strings.TrimSpace(os.Getenv("GITHUB_REPOSITORY")), "GitHub repository owner/name")
    token := flag.String("token", firstNonEmpty(os.Getenv("OPENWORKER_GITHUB_TOKEN"), os.Getenv("GH_TOKEN"), os.Getenv("GITHUB_TOKEN")), "GitHub token with Actions write permission")
    timeout := flag.Duration("timeout", 90*time.Second, "maximum time to wait for queue to become empty")
    poll := flag.Duration("poll", 2*time.Second, "verification poll interval")
    exclude := flag.Int64("exclude-run-id", 0, "workflow run id to preserve")
    flag.Parse()

    if strings.TrimSpace(*repo) == "" || !strings.Contains(*repo, "/") {
        fail(errors.New("-repo owner/name is required (or set GITHUB_REPOSITORY)"))
    }
    if strings.TrimSpace(*token) == "" {
        fail(errors.New("GitHub token required: OPENWORKER_GITHUB_TOKEN, GH_TOKEN, GITHUB_TOKEN, or -token"))
    }
    if *timeout <= 0 || *poll <= 0 {
        fail(errors.New("timeout and poll must be positive"))
    }

    c := githubClient{
        token: strings.TrimSpace(*token),
        repo:  strings.TrimSpace(*repo),
        http:  &http.Client{Timeout: 20 * time.Second},
    }

    before, err := c.nonterminalRuns()
    if err != nil {
        fail(err)
    }

    cancelled := make([]int64, 0, len(before))
    for _, run := range before {
        if run.ID == *exclude {
            continue
        }
        if err := c.cancelRun(run.ID); err != nil {
            fail(fmt.Errorf("cancel run %d (%s): %w", run.ID, run.Name, err))
        }
        cancelled = append(cancelled, run.ID)
    }
    sort.Slice(cancelled, func(i, j int) bool { return cancelled[i] < cancelled[j] })

    deadline := time.Now().Add(*timeout)
    var remaining []workflowRun
    for {
        remaining, err = c.nonterminalRuns()
        if err != nil {
            fail(err)
        }
        filtered := remaining[:0]
        for _, run := range remaining {
            if run.ID != *exclude {
                filtered = append(filtered, run)
            }
        }
        remaining = filtered
        if len(remaining) == 0 {
            break
        }
        if time.Now().After(deadline) {
            break
        }
        time.Sleep(*poll)
    }

    outcome := "PASS"
    if len(remaining) != 0 {
        outcome = "FAIL"
    }
    out := result{
        SchemaVersion:     "openworker.github-actions-queue-clear/v1",
        Repository:        c.repo,
        NonterminalBefore: len(before),
        CancelledIDs:      cancelled,
        RemainingAfter:    remaining,
        Outcome:           outcome,
        VerifiedAt:        time.Now().UTC().Format(time.RFC3339),
    }
    enc := json.NewEncoder(os.Stdout)
    enc.SetIndent("", "  ")
    _ = enc.Encode(out)
    if outcome != "PASS" {
        os.Exit(1)
    }
}

func (c githubClient) nonterminalRuns() ([]workflowRun, error) {
    var all []workflowRun
    for page := 1; ; page++ {
        var rr runsResponse
        path := fmt.Sprintf("https://api.github.com/repos/%s/actions/runs?per_page=100&page=%d", c.repo, page)
        if err := c.doJSON(http.MethodGet, path, nil, &rr); err != nil {
            return nil, err
        }
        for _, run := range rr.WorkflowRuns {
            if !strings.EqualFold(strings.TrimSpace(run.Status), "completed") {
                all = append(all, run)
            }
        }
        if len(rr.WorkflowRuns) < 100 {
            break
        }
    }
    sort.Slice(all, func(i, j int) bool { return all[i].ID < all[j].ID })
    return all, nil
}

func (c githubClient) cancelRun(id int64) error {
    path := fmt.Sprintf("https://api.github.com/repos/%s/actions/runs/%d/cancel", c.repo, id)
    req, err := http.NewRequest(http.MethodPost, path, bytes.NewReader(nil))
    if err != nil {
        return err
    }
    c.headers(req)
    resp, err := c.http.Do(req)
    if err != nil {
        return err
    }
    defer resp.Body.Close()
    body, _ := io.ReadAll(io.LimitReader(resp.Body, 1<<20))
    if resp.StatusCode == http.StatusConflict || resp.StatusCode == http.StatusNotFound {
        // Race-safe: the run may already have completed/disappeared after listing.
        return nil
    }
    if resp.StatusCode/100 != 2 {
        return fmt.Errorf("GitHub HTTP %d: %s", resp.StatusCode, strings.TrimSpace(string(body)))
    }
    return nil
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
        if err := json.Unmarshal(data, out); err != nil {
            return err
        }
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
