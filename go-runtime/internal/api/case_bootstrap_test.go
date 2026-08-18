package api

import (
    "encoding/json"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "testing"

    "github.com/liuxb99/openworker/go-runtime/internal/store"
)

func TestCaseBootstrapCreatesWorkspaceBeforeDurableAck(t *testing.T) {
    base := t.TempDir()
    root := filepath.Join(base, "openworker")
    if err := os.MkdirAll(filepath.Join(root, "case-worklists"), 0o755); err != nil { t.Fatal(err) }
    if err := os.MkdirAll(filepath.Join(root, "case-specs"), 0o755); err != nil { t.Fatal(err) }
    manifest := filepath.Join(root, "case-worklists", "0005.json")
    spec := filepath.Join(root, "case-specs", "0005.json")
    if err := os.WriteFile(manifest, []byte(`{"case_id":"0005"}`), 0o644); err != nil { t.Fatal(err) }
    if err := os.WriteFile(spec, []byte(`{"case_id":"0005"}`), 0o644); err != nil { t.Fatal(err) }
    workspace := filepath.Join(base, "jobs", "0005-SNOW-WHITE")
    if _, err := os.Stat(workspace); !os.IsNotExist(err) { t.Fatalf("workspace must start absent: %v", err) }

    st, err := store.Open(filepath.Join(base, "node.sqlite3"))
    if err != nil { t.Fatal(err) }
    defer st.Close()
    s := New(st, nil, "DESKTOP-ODAQN0D", "http://oda:8787")
    w := req(t, s.Handler(), http.MethodPost, "/v1/cases/bootstrap", map[string]any{
        "case_id": "0005",
        "machine": "DESKTOP-ODAQN0D",
        "workspace_root": workspace,
        "openworker_root": root,
        "controller_module": "coworker.case0005_controller",
        "manifest_path": "case-worklists/0005.json",
        "spec_path": "case-specs/0005.json",
    })
    if w.Code != http.StatusAccepted { t.Fatalf("bootstrap status=%d body=%s", w.Code, w.Body.String()) }
    if st, err := os.Stat(filepath.Join(workspace, ".openworker")); err != nil || !st.IsDir() {
        t.Fatalf("workspace must exist before ACK: stat=%v err=%v", st, err)
    }
    var got struct {
        CaseID string `json:"case_id"`
        Machine string `json:"machine"`
        WorkspaceCreated bool `json:"workspace_created"`
        Job struct {
            JobID string `json:"job_id"`
            Accepted bool `json:"accepted"`
        } `json:"job"`
    }
    if err := json.Unmarshal(w.Body.Bytes(), &got); err != nil { t.Fatal(err) }
    if got.CaseID != "0005" || got.Machine != "DESKTOP-ODAQN0D" || !got.WorkspaceCreated || !got.Job.Accepted || got.Job.JobID == "" {
        t.Fatalf("unexpected bootstrap ACK: %+v", got)
    }
    job, err := st.Get(got.Job.JobID)
    if err != nil { t.Fatal(err) }
    if job.WorkspaceRoot != workspace || job.Machine != "DESKTOP-ODAQN0D" {
        t.Fatalf("durable job mismatch: %+v", job)
    }
    if !strings.Contains(job.Command, "coworker.case0005_controller") || !strings.Contains(job.Command, `"`+workspace+`"`) {
        t.Fatalf("bootstrap command not bounded to Case 0005 workspace: %s", job.Command)
    }
}

func TestCaseBootstrapRejectsWrongMachineBeforeWorkspaceCreation(t *testing.T) {
    base := t.TempDir()
    root := filepath.Join(base, "openworker")
    if err := os.MkdirAll(filepath.Join(root, "case-worklists"), 0o755); err != nil { t.Fatal(err) }
    if err := os.MkdirAll(filepath.Join(root, "case-specs"), 0o755); err != nil { t.Fatal(err) }
    if err := os.WriteFile(filepath.Join(root, "case-worklists", "0005.json"), []byte(`{}`), 0o644); err != nil { t.Fatal(err) }
    if err := os.WriteFile(filepath.Join(root, "case-specs", "0005.json"), []byte(`{}`), 0o644); err != nil { t.Fatal(err) }
    workspace := filepath.Join(base, "jobs", "wrong")
    st, err := store.Open(filepath.Join(base, "node.sqlite3"))
    if err != nil { t.Fatal(err) }
    defer st.Close()
    s := New(st, nil, "DESKTOP-ODAQN0D", "http://oda:8787")
    w := req(t, s.Handler(), http.MethodPost, "/v1/cases/bootstrap", map[string]any{
        "case_id": "0005", "machine": "DESKTOP-OTHER", "workspace_root": workspace,
        "openworker_root": root, "controller_module": "coworker.case0005_controller",
        "manifest_path": "case-worklists/0005.json", "spec_path": "case-specs/0005.json",
    })
    if w.Code != http.StatusConflict { t.Fatalf("wrong-machine status=%d body=%s", w.Code, w.Body.String()) }
    if _, err := os.Stat(workspace); !os.IsNotExist(err) { t.Fatalf("wrong-machine request must not create workspace: %v", err) }
}
