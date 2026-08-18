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

    "github.com/liuxb99/openworker/go-runtime/internal/model"
)

type caseBootstrapRequest struct {
    CaseID           string            `json:"case_id"`
    Machine          string            `json:"machine"`
    WorkspaceRoot    string            `json:"workspace_root"`
    OpenWorkerRoot   string            `json:"openworker_root"`
    ControllerModule string            `json:"controller_module"`
    ManifestPath     string            `json:"manifest_path"`
    SpecPath         string            `json:"spec_path"`
    PythonExe        string            `json:"python_exe,omitempty"`
    Env              map[string]string `json:"env,omitempty"`
}

func (s *Server) caseBootstrap(w http.ResponseWriter, r *http.Request) {
    var req caseBootstrapRequest
    d := json.NewDecoder(http.MaxBytesReader(w, r.Body, 1<<20))
    d.DisallowUnknownFields()
    if err := d.Decode(&req); err != nil {
        writeErr(w, http.StatusBadRequest, err)
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

    if req.CaseID == "" || req.WorkspaceRoot == "" || req.OpenWorkerRoot == "" || req.ControllerModule == "" || req.ManifestPath == "" || req.SpecPath == "" {
        writeErr(w, http.StatusBadRequest, errors.New("case_id, workspace_root, openworker_root, controller_module, manifest_path and spec_path are required"))
        return
    }
    if req.Machine == "" {
        req.Machine = s.machine
    }
    if !strings.EqualFold(req.Machine, s.machine) {
        writeErr(w, http.StatusConflict, fmt.Errorf("case bootstrap machine mismatch expected=%s actual=%s", req.Machine, s.machine))
        return
    }
    if !strings.HasPrefix(req.ControllerModule, "coworker.case") || strings.ContainsAny(req.ControllerModule, " \t\r\n\"'") {
        writeErr(w, http.StatusBadRequest, errors.New("controller_module must be a bounded coworker.case* Python module"))
        return
    }
    if req.PythonExe == "" {
        req.PythonExe = "python"
    }
    if strings.ContainsAny(req.PythonExe, "\r\n\"") {
        writeErr(w, http.StatusBadRequest, errors.New("python_exe contains unsupported characters"))
        return
    }

    workspace, err := filepath.Abs(req.WorkspaceRoot)
    if err != nil || !filepath.IsAbs(workspace) {
        writeErr(w, http.StatusBadRequest, errors.New("workspace_root must be absolute"))
        return
    }
    root, err := filepath.Abs(req.OpenWorkerRoot)
    if err != nil || !filepath.IsAbs(root) {
        writeErr(w, http.StatusBadRequest, errors.New("openworker_root must be absolute"))
        return
    }
    if st, err := os.Stat(root); err != nil || !st.IsDir() {
        writeErr(w, http.StatusBadRequest, fmt.Errorf("openworker_root is missing: %s", root))
        return
    }
    manifest, err := requireBootstrapFile(root, req.ManifestPath)
    if err != nil {
        writeErr(w, http.StatusBadRequest, err)
        return
    }
    spec, err := requireBootstrapFile(root, req.SpecPath)
    if err != nil {
        writeErr(w, http.StatusBadRequest, err)
        return
    }

    // Acceptance of a case is materialized immediately: the workspace exists
    // before the durable scheduler ACK is returned.
    if err := os.MkdirAll(filepath.Join(workspace, ".openworker"), 0o755); err != nil {
        writeErr(w, http.StatusInternalServerError, fmt.Errorf("create workspace: %w", err))
        return
    }

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
            writeErr(w, http.StatusBadRequest, errors.New("env contains invalid key/value"))
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
        writeErr(w, http.StatusConflict, err)
        return
    }
    s.store.RecordEvent(jobID, "case_bootstrap_accepted", "workspace materialized before durable ACK")
    writeJSON(w, http.StatusAccepted, map[string]any{
        "case_id": req.CaseID,
        "machine": s.machine,
        "workspace_root": workspace,
        "workspace_created": true,
        "controller_module": req.ControllerModule,
        "job": ack,
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
