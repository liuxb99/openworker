package casecontroller

import (
    "bufio"
    "encoding/json"
    "errors"
    "fmt"
    "os"
    "path/filepath"
    "strings"
    "time"
)

const Schema = "openworker.go-case-controller/v1"

type Step struct {
    StepID       string         `json:"step_id"`
    Dependencies []string       `json:"dependencies"`
    Status       string         `json:"status"`
    Evidence     map[string]any `json:"evidence"`
}

type Worklist struct {
    SchemaVersion string `json:"schema_version"`
    CaseID string `json:"case_id"`
    WorkspaceRoot string `json:"workspace_root"`
    AssignedHost string `json:"assigned_host"`
    Revision int `json:"revision"`
    Steps []Step `json:"steps"`
}

type BootstrapResult struct {
    Schema string `json:"schema"`
    CaseID string `json:"case_id"`
    Machine string `json:"machine"`
    WorkspaceRoot string `json:"workspace_root"`
    Revision int `json:"revision"`
    ReadyStepIDs []string `json:"ready_step_ids"`
    LedgerPath string `json:"ledger_path"`
    Controller string `json:"controller"`
    PythonRequired bool `json:"python_required"`
    CompletedAt time.Time `json:"completed_at"`
}

type ledgerEvent struct {
    Schema string `json:"schema"`
    Timestamp time.Time `json:"timestamp"`
    CaseID string `json:"case_id"`
    Machine string `json:"machine"`
    EventType string `json:"event_type"`
    WorkspaceRoot string `json:"workspace_root"`
    Revision int `json:"revision,omitempty"`
    ReadyStepIDs []string `json:"ready_step_ids,omitempty"`
    Detail string `json:"detail,omitempty"`
}

func Bootstrap(caseID, machine, workspaceRoot, manifestPath string) (BootstrapResult, error) {
    if strings.TrimSpace(caseID) != "0005" { return BootstrapResult{}, fmt.Errorf("unsupported case %q", caseID) }
    b, err := os.ReadFile(manifestPath); if err != nil { return BootstrapResult{}, err }
    var w Worklist
    if err := json.Unmarshal(b, &w); err != nil { return BootstrapResult{}, fmt.Errorf("decode worklist: %w", err) }
    if w.CaseID != caseID { return BootstrapResult{}, errors.New("worklist case_id mismatch") }
    if !strings.EqualFold(w.AssignedHost, machine) { return BootstrapResult{}, fmt.Errorf("assigned_host mismatch: %s", w.AssignedHost) }
    if !samePath(w.WorkspaceRoot, workspaceRoot) { return BootstrapResult{}, fmt.Errorf("workspace_root mismatch worklist=%s request=%s", w.WorkspaceRoot, workspaceRoot) }
    if w.Revision <= 0 || len(w.Steps) == 0 { return BootstrapResult{}, errors.New("invalid worklist revision/steps") }
    if err := validateGraph(w.Steps); err != nil { return BootstrapResult{}, err }
    marker := filepath.Join(workspaceRoot, ".openworker")
    if err := os.MkdirAll(marker, 0o755); err != nil { return BootstrapResult{}, fmt.Errorf("materialize workspace: %w", err) }
    ledger := filepath.Join(marker, "case-supervisor-ledger.jsonl")
    ready := readySteps(w.Steps)
    if err := appendLedger(ledger, ledgerEvent{Schema:"openworker.case-supervisor-ledger/v1",Timestamp:time.Now().UTC(),CaseID:caseID,Machine:machine,EventType:"go_controller_bootstrap_start",WorkspaceRoot:workspaceRoot,Revision:w.Revision}); err != nil { return BootstrapResult{}, err }
    if err := appendLedger(ledger, ledgerEvent{Schema:"openworker.case-supervisor-ledger/v1",Timestamp:time.Now().UTC(),CaseID:caseID,Machine:machine,EventType:"go_controller_bootstrap_completed",WorkspaceRoot:workspaceRoot,Revision:w.Revision,ReadyStepIDs:ready,Detail:"native Go bootstrap; Python controller not required"}); err != nil { return BootstrapResult{}, err }
    return BootstrapResult{Schema:Schema,CaseID:caseID,Machine:machine,WorkspaceRoot:workspaceRoot,Revision:w.Revision,ReadyStepIDs:ready,LedgerPath:ledger,Controller:"go-native",PythonRequired:false,CompletedAt:time.Now().UTC()}, nil
}

func validateGraph(steps []Step) error {
    ids := map[string]bool{}
    for _, s := range steps { if s.StepID == "" || ids[s.StepID] { return fmt.Errorf("invalid/duplicate step_id %q", s.StepID) }; ids[s.StepID]=true }
    for _, s := range steps { for _, d := range s.Dependencies { if !ids[d] { return fmt.Errorf("step %s depends on unknown %s", s.StepID,d) } } }
    return nil
}

func readySteps(steps []Step) []string {
    done := map[string]bool{}
    for _, s := range steps { if strings.EqualFold(s.Status,"SUCCEEDED") || strings.EqualFold(s.Status,"COMPLETED") { done[s.StepID]=true } }
    out:=[]string{}
    for _, s := range steps {
        if !strings.EqualFold(s.Status,"PENDING") { continue }
        ok:=true; for _,d:=range s.Dependencies { if !done[d] { ok=false;break } }
        if ok { out=append(out,s.StepID) }
    }
    return out
}

func appendLedger(path string, ev ledgerEvent) error {
    f,err:=os.OpenFile(path,os.O_CREATE|os.O_WRONLY|os.O_APPEND,0o644);if err!=nil{return err};defer f.Close()
    w:=bufio.NewWriter(f);if err:=json.NewEncoder(w).Encode(ev);err!=nil{return err};if err:=w.Flush();err!=nil{return err};return f.Sync()
}

func samePath(a,b string) bool { aa,_:=filepath.Abs(filepath.Clean(a));bb,_:=filepath.Abs(filepath.Clean(b));return strings.EqualFold(aa,bb) }
