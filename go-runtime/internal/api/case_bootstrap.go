package api

import (
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "time"

    "github.com/liuxb99/openworker/go-runtime/internal/cluster"
    "github.com/liuxb99/openworker/go-runtime/internal/model"
)

type caseBootstrapRequest = cluster.CaseBootstrapRequest

type bootstrapDiagnostic struct {
    OK              bool              `json:"ok"`
    CaseID          string            `json:"case_id,omitempty"`
    Machine         string            `json:"machine,omitempty"`
    Stage           string            `json:"stage"`
    AttemptedAction string            `json:"attempted_action"`
    Reason          string            `json:"reason"`
    NextAction      string            `json:"next_action"`
    Checks          map[string]any    `json:"checks,omitempty"`
    ObservedAt      time.Time         `json:"observed_at"`
}

func (s *Server) bootstrapFail(w http.ResponseWriter, status int, req caseBootstrapRequest, stage, attempted string, err error, next string, checks map[string]any) {
    machine := strings.TrimSpace(req.Machine)
    if machine == "" {
        machine = s.machine
    }
    d := bootstrapDiagnostic{
        OK:              false,
        CaseID:          strings.TrimSpace(req.CaseID),
        Machine:         machine,
        Stage:           stage,
        AttemptedAction: attempted,
        Reason:          err.Error(),
        NextAction:      next,
        Checks:          checks,
        ObservedAt:      time.Now().UTC(),
    }
    detail, _ := json.Marshal(d)
    _ = s.store.RecordClusterControl("", "case_bootstrap_failed", machine, string(detail))
    writeJSON(w, status, d)
}

func (s *Server) caseBootstrap(w http.ResponseWriter, r *http.Request) {
    var req caseBootstrapRequest
    d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
    d.DisallowUnknownFields()
    if err := d.Decode(&req); err != nil {
        s.bootstrapFail(w, http.StatusBadRequest, req, "decode_request", "decode case bootstrap request", err, "fix request JSON and retry", nil)
        return
    }
    req.CaseID = strings.TrimSpace(req.CaseID)
    req.Machine = strings.TrimSpace(req.Machine)
    req.WorkspaceRoot = strings.TrimSpace(req.WorkspaceRoot)
    req.OpenWorkerRoot = strings.TrimSpace(req.OpenWorkerRoot)
    req.ControllerModule = strings.TrimSpace(req.ControllerModule)
    req.ManifestPath = strings.TrimSpace(req.ManifestPath)
    req.SpecPath = strings.TrimSpace(req.SpecPath)
    req.PythonExe = strings.TrimSpace(req.PythonExe)

    checks := map[string]any{
        "workspace_root":   req.WorkspaceRoot,
        "openworker_root":  req.OpenWorkerRoot,
        "manifest_path":    req.ManifestPath,
        "spec_path":        req.SpecPath,
        "controller_module": req.ControllerModule,
    }

    if req.CaseID == "" || req.WorkspaceRoot == "" || req.OpenWorkerRoot == "" || req.ControllerModule == "" || req.ManifestPath == "" || req.SpecPath == "" {
        s.bootstrapFail(w, http.StatusBadRequest, req, "validate_required_fields", "validate required bootstrap fields", errors.New("case_id, workspace_root, openworker_root, controller_module, manifest_path and spec_path are required"), "supply all required fields and retry", checks)
        return
    }
    if req.Machine == "" {
        req.Machine = s.machine
    }
    if !strings.HasPrefix(req.ControllerModule, "coworker.case") || strings.ContainsAny(req.ControllerModule, " \t\r\n\"'") {
        s.bootstrapFail(w, http.StatusBadRequest, req, "validate_controller", "validate bounded controller module", errors.New("controller_module must be a bounded coworker.case* Python module"), "use a coworker.case* module and retry", checks)
        return
    }
    if req.PythonExe == "" {
        req.PythonExe = "python"
    }
    if strings.ContainsAny(req.PythonExe, "\r\n\"") {
        s.bootstrapFail(w, http.StatusBadRequest, req, "validate_python", "validate python executable", errors.New("python_exe contains unsupported characters"), "fix python_exe and retry", checks)
        return
    }

    if !strings.EqualFold(req.Machine, s.machine) {
        if s.cluster == nil {
            s.bootstrapFail(w, http.StatusServiceUnavailable, req, "route_machine", "route bootstrap to requested machine", errors.New("cluster controller disabled"), "enable cluster routing or submit directly to the requested machine", checks)
            return
        }
        res, err := s.cluster.CaseBootstrap(req)
        if err != nil {
            s.bootstrapFail(w, http.StatusConflict, req, "route_machine", "forward bootstrap to requested machine", err, "inspect cluster endpoint/connectivity and retry", checks)
            return
        }
        _ = s.store.RecordClusterControl("", "case_bootstrap", res.Selected.NodeID, "forwarded to "+res.Selected.Endpoint)
        writeJSON(w, http.StatusAccepted, map[string]any{
            "case_id": req.CaseID,
            "requested_machine": req.Machine,
            "selected": res.Selected,
            "remote": res.Response,
            "authority": "openworker-cluster-to-local-supervisor",
            "github_action_used": false,
        })
        return
    }

    workspace, err := filepath.Abs(req.WorkspaceRoot)
    if err != nil || !filepath.IsAbs(workspace) {
        if err == nil { err = errors.New("workspace_root must be absolute") }
        s.bootstrapFail(w, http.StatusBadRequest, req, "resolve_workspace", "resolve absolute workspace path", err, "use an absolute local workspace path and retry", checks)
        return
    }
    checks["resolved_workspace_root"] = workspace

    root, err := filepath.Abs(req.OpenWorkerRoot)
    if err != nil || !filepath.IsAbs(root) {
        if err == nil { err = errors.New("openworker_root must be absolute") }
        s.bootstrapFail(w, http.StatusBadRequest, req, "resolve_openworker_root", "resolve absolute openworker root", err, "use an absolute OpenWorker checkout path and retry", checks)
        return
    }
    checks["resolved_openworker_root"] = root

    if st, statErr := os.Stat(root); statErr != nil || !st.IsDir() {
        reason := statErr
        if reason == nil { reason = fmt.Errorf("not a directory: %s", root) }
        checks["openworker_root_exists"] = false
        s.bootstrapFail(w, http.StatusBadRequest, req, "validate_openworker_root", "verify OpenWorker checkout exists", fmt.Errorf("openworker_root is missing: %s: %v", root, reason), "sync/fix the OpenWorker checkout path on this machine and retry", checks)
        return
    }
    checks["openworker_root_exists"] = true

    manifest, err := requireBootstrapFile(root, req.ManifestPath)
    if err != nil {
        checks["manifest_ok"] = false
        s.bootstrapFail(w, http.StatusBadRequest, req, "validate_manifest", "verify case worklist/manifest exists and is non-empty", err, "sync/fix the case manifest under openworker_root and retry", checks)
        return
    }
    checks["manifest_ok"] = true
    checks["resolved_manifest"] = manifest

    spec, err := requireBootstrapFile(root, req.SpecPath)
    if err != nil {
        checks["spec_ok"] = false
        s.bootstrapFail(w, http.StatusBadRequest, req, "validate_spec", "verify case spec exists and is non-empty", err, "sync/fix the case spec under openworker_root and retry", checks)
        return
    }
    checks["spec_ok"] = true
    checks["resolved_spec"] = spec

    workspaceMarker := filepath.Join(workspace, ".openworker")
    if err := os.MkdirAll(workspaceMarker, 0o755); err != nil {
        checks["workspace_created"] = false
        checks["workspace_marker"] = workspaceMarker
        s.bootstrapFail(w, http.StatusInternalServerError, req, "materialize_workspace", "create workspace and .openworker marker", fmt.Errorf("create workspace: %w", err), "fix filesystem/path permissions for the OpenWorker process identity and retry", checks)
        return
    }
    checks["workspace_created"] = true
    checks["workspace_marker"] = workspaceMarker

    now := time.Now().UTC()
    jobID := fmt.Sprintf("case%s-bootstrap-%d", safeCaseID(req.CaseID), now.UnixNano())
    dispatchID := "local-supervisor-" + jobID
    command := strings.Join([]string{
        quoteCmdArg(req.PythonExe), "-m", req.ControllerModule,
        "--node-url", quoteCmdArg("http://127.0.0.1:8787"),
        "bootstrap",
        "--workspace", quoteCmdArg(workspace),
        "--manifest", quoteCmdArg(manifest),
        "--spec", quoteCmdArg(spec),
    }, " ")
    env := map[string]string{}
    for k, v := range req.Env {
        k = strings.TrimSpace(k)
        if k == "" || strings.ContainsAny(k, "=\x00\r\n") || strings.ContainsAny(v, "\x00\r\n") {
            s.bootstrapFail(w, http.StatusBadRequest, req, "validate_env", "validate bootstrap environment", errors.New("env contains invalid key/value"), "remove invalid environment key/value and retry", checks)
            return
        }
        env[k] = v
    }
    env["OPENWORKER_ROOT"] = root
    env["OPENWORKER_CASE_ID"] = req.CaseID

    ack, err := s.store.Submit(model.SubmitRequest{
        JobID:         jobID,
        DispatchID:    dispatchID,
        Machine:       s.machine,
        Priority:      100,
        Command:       command,
        CWD:           root,
        WorkspaceRoot: workspace,
        Env:           env,
        TimeoutSec:    3600,
        Locks:         []string{"case:" + req.CaseID + ":bootstrap"},
    }, s.machine)
    if err != nil {
        checks["durable_submit"] = false
        s.bootstrapFail(w, http.StatusConflict, req, "durable_submit", "submit bootstrap job to local durable queue", err, "inspect queue/idempotency state and retry", checks)
        return
    }
    checks["durable_submit"] = true
    s.store.RecordEvent(jobID, "case_bootstrap_accepted", "workspace materialized before durable ACK")
    writeJSON(w, http.StatusAccepted, map[string]any{
        "ok": true,
        "case_id": req.CaseID,
        "machine": s.machine,
        "workspace_root": workspace,
        "workspace_created": true,
        "workspace_marker": workspaceMarker,
        "controller_module": req.ControllerModule,
        "attempted_action": "materialize workspace and submit bootstrap job",
        "stage": "accepted",
        "job": ack,
        "checks": checks,
        "authority": "openworker-local-supervisor",
        "github_action_used": false,
    })
}

func requireBootstrapFile(root, raw string) (string, error) {
    p := strings.TrimSpace(raw)
    if strings.ContainsAny(p, "\"\r\n") {
        return "", errors.New("bootstrap file path contains unsupported characters")
    }
    if !filepath.IsAbs(p) {
        p = filepath.Join(root, p)
    }
    p, err := filepath.Abs(p)
    if err != nil {
        return "", err
    }
    back, err := filepath.Rel(root, p)
    if err != nil || back == ".." || strings.HasPrefix(back, ".."+string(filepath.Separator)) {
        return "", errors.New("bootstrap manifest/spec must remain under openworker_root")
    }
    st, err := os.Stat(p)
    if err != nil || st.IsDir() || st.Size() <= 0 {
        return "", fmt.Errorf("bootstrap file missing or empty: %s", p)
    }
    return p, nil
}

func quoteCmdArg(v string) string {
    return "\"" + strings.ReplaceAll(v, "\"", "\"\"") + "\""
}

func safeCaseID(v string) string {
    var b strings.Builder
    for _, r := range strings.TrimSpace(v) {
        if (r >= 'a' && r <= 'z') || (r >= 'A' && r <= 'Z') || (r >= '0' && r <= '9') || r == '-' || r == '_' {
            b.WriteRune(r)
        }
    }
    if b.Len() == 0 {
        return "case"
    }
    return b.String()
}
