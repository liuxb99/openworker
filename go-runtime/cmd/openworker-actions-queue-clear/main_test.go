package main

import (
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"reflect"
	"strings"
	"testing"
	"time"
)

func TestFirstNonEmpty(t *testing.T) {
	if got := firstNonEmpty("", "  ", "token-a", "token-b"); got != "token-a" {
		t.Fatalf("got %q", got)
	}
}

func TestThreeStageDeleteOnlyForStuckRun(t *testing.T) {
	now := time.Date(2026, 8, 20, 12, 0, 0, 0, time.UTC)
	var mutations []string
	listed := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if strings.Contains(r.URL.Path, "/actions/runs") && r.Method == http.MethodGet {
			listed++
			runs := []workflowRun{}
			if listed == 1 {
				runs = []workflowRun{{ID: 7, Name: "ghost", Status: "queued", CreatedAt: now.Add(-time.Hour)}}
			}
			_ = json.NewEncoder(w).Encode(runsResponse{WorkflowRuns: runs})
			return
		}
		mutations = append(mutations, r.Method+" "+r.URL.Path)
		if strings.HasSuffix(r.URL.Path, "/cancel") || strings.HasSuffix(r.URL.Path, "/force-cancel") {
			http.Error(w, "stuck", http.StatusInternalServerError)
			return
		}
		w.WriteHeader(http.StatusNoContent)
	}))
	defer srv.Close()
	c := githubClient{repo: "o/r", baseURL: srv.URL, http: srv.Client(), now: func() time.Time { return now }}
	out, err := clearQueue(c, 0, time.Second, time.Millisecond, 30*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	want := []string{"POST /repos/o/r/actions/runs/7/cancel", "POST /repos/o/r/actions/runs/7/force-cancel", "DELETE /repos/o/r/actions/runs/7"}
	if !reflect.DeepEqual(mutations, want) {
		t.Fatalf("mutations=%v", mutations)
	}
	if out.Outcome != "PASS" || !reflect.DeepEqual(out.DeletedIDs, []int64{7}) {
		t.Fatalf("out=%+v", out)
	}
}

func TestDoesNotDeleteRunBelowStuckThreshold(t *testing.T) {
	now := time.Date(2026, 8, 20, 12, 0, 0, 0, time.UTC)
	listed := 0
	deletes := 0
	srv := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		if r.Method == http.MethodGet {
			listed++
			runs := []workflowRun{}
			if listed == 1 {
				runs = []workflowRun{{ID: 8, Status: "queued", CreatedAt: now.Add(-time.Minute)}}
			}
			_ = json.NewEncoder(w).Encode(runsResponse{WorkflowRuns: runs})
			return
		}
		if r.Method == http.MethodDelete {
			deletes++
		}
		http.Error(w, "no", http.StatusInternalServerError)
	}))
	defer srv.Close()
	c := githubClient{repo: "o/r", baseURL: srv.URL, http: srv.Client(), now: func() time.Time { return now }}
	out, err := clearQueue(c, 0, time.Second, time.Millisecond, 30*time.Minute)
	if err != nil {
		t.Fatal(err)
	}
	if deletes != 0 || out.Operations[0].Delete.Outcome != "not_stuck" {
		t.Fatalf("unexpected delete: %+v", out.Operations[0])
	}
}
