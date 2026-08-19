package api

import (
    "context"
    "encoding/json"
    "errors"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "sync"
    "time"

    "github.com/liuxb99/openworker/go-runtime/internal/casecontroller"
)

var nativeCaseContinueRoutes sync.Map

func ensureNativeCaseContinueRoute(s *Server){if _,loaded:=nativeCaseContinueRoutes.LoadOrStore(s,struct{}{});!loaded{s.mux.HandleFunc("POST /v1/cases/continue",s.caseContinue)}}

type caseContinueRequest struct {
    CaseID string `json:"case_id"`
    Machine string `json:"machine"`
    WorkspaceRoot string `json:"workspace_root"`
    OpenWorkerRoot string `json:"openworker_root,omitempty"`
    ManifestPath string `json:"manifest_path,omitempty"`
    SpecPath string `json:"spec_path,omitempty"`
}

func (s *Server) caseContinue(w http.ResponseWriter,r *http.Request){
    var req caseContinueRequest;dec:=json.NewDecoder(http.MaxBytesReader(w,r.Body,256<<10));dec.DisallowUnknownFields();if err:=dec.Decode(&req);err!=nil{writeErr(w,400,err);return}
    req.CaseID=strings.TrimSpace(req.CaseID);req.Machine=strings.TrimSpace(req.Machine);req.WorkspaceRoot=strings.TrimSpace(req.WorkspaceRoot);req.OpenWorkerRoot=strings.TrimSpace(req.OpenWorkerRoot);req.ManifestPath=strings.TrimSpace(req.ManifestPath);req.SpecPath=strings.TrimSpace(req.SpecPath)
    if req.CaseID==""{writeErr(w,400,errors.New("case_id is required"));return}
    if req.Machine==""{req.Machine=s.machine};if !strings.EqualFold(req.Machine,s.machine){writeErr(w,409,errors.New("case continue must execute on assigned local machine"));return}
    if req.WorkspaceRoot==""||!filepath.IsAbs(req.WorkspaceRoot){writeErr(w,400,errors.New("absolute workspace_root required"));return}
    ctx,cancel:=context.WithTimeout(r.Context(),15*time.Second);defer cancel()

    var refresh any
    refreshRequested:=req.OpenWorkerRoot!=""||req.ManifestPath!=""||req.SpecPath!=""
    if refreshRequested{
        if req.OpenWorkerRoot==""||req.ManifestPath==""||req.SpecPath==""{writeErr(w,400,errors.New("openworker_root, manifest_path and spec_path must be supplied together for definition refresh"));return}
        root,err:=filepath.Abs(req.OpenWorkerRoot);if err!=nil||!filepath.IsAbs(root){writeErr(w,400,errors.New("absolute openworker_root required for definition refresh"));return}
        if st,err:=os.Stat(root);err!=nil||!st.IsDir(){writeErr(w,400,errors.New("openworker_root unavailable for definition refresh"));return}
        manifest,err:=requireBootstrapFile(root,req.ManifestPath);if err!=nil{writeErr(w,400,err);return}
        spec,err:=requireBootstrapFile(root,req.SpecPath);if err!=nil{writeErr(w,400,err);return}
        refreshed,err:=casecontroller.RefreshDefinition(req.CaseID,s.machine,req.WorkspaceRoot,manifest,spec);if err!=nil{writeJSON(w,http.StatusConflict,map[string]any{"ok":false,"case_id":req.CaseID,"machine":s.machine,"workspace_root":req.WorkspaceRoot,"controller":"go-native","python_controller_used":false,"stage":"go_native_definition_refresh_failed","error":err.Error(),"authority":"openworker-go-native-case-controller","github_action_used":false});return}
        refresh=refreshed
    }

    result,err:=casecontroller.Continue(ctx,req.CaseID,s.machine,req.WorkspaceRoot,"http://127.0.0.1:8848",nil)
    if err!=nil{writeJSON(w,http.StatusConflict,map[string]any{"ok":false,"case_id":req.CaseID,"machine":s.machine,"workspace_root":req.WorkspaceRoot,"controller":"go-native","python_controller_used":false,"stage":"go_native_continue_failed","definition_refresh":refresh,"error":err.Error(),"authority":"openworker-go-native-case-controller","github_action_used":false});return}
    detail,_:=json.Marshal(map[string]any{"definition_refresh":refresh,"result":result});_=s.store.RecordClusterControl(result.WorkID,"go_case_continue",s.machine,string(detail))
    writeJSON(w,http.StatusAccepted,map[string]any{"ok":true,"case_id":req.CaseID,"machine":s.machine,"workspace_root":req.WorkspaceRoot,"controller":"go-native","python_controller_used":false,"stage":"go_native_continue_accepted","definition_refresh":refresh,"result":result,"authority":"openworker-go-native-case-controller","github_action_used":false})
}
