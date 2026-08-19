package api

import (
    "context"
    "encoding/json"
    "errors"
    "fmt"
    "net/http"
    "path/filepath"
    "strings"
    "time"

    "github.com/liuxb99/openworker/go-runtime/internal/casecontroller"
)

type caseContinueRequest struct {
    CaseID string `json:"case_id"`
    Machine string `json:"machine"`
    WorkspaceRoot string `json:"workspace_root"`
}

func (s *Server) caseContinue(w http.ResponseWriter,r *http.Request){
    var req caseContinueRequest;dec:=json.NewDecoder(http.MaxBytesReader(w,r.Body,64<<10));dec.DisallowUnknownFields();if err:=dec.Decode(&req);err!=nil{writeErr(w,400,err);return}
    req.CaseID=strings.TrimSpace(req.CaseID);req.Machine=strings.TrimSpace(req.Machine);req.WorkspaceRoot=strings.TrimSpace(req.WorkspaceRoot)
    if req.CaseID!="0005"{writeErr(w,400,fmt.Errorf("unsupported native Go case %q",req.CaseID));return}
    if req.Machine==""{req.Machine=s.machine};if !strings.EqualFold(req.Machine,s.machine){writeErr(w,409,errors.New("case continue must execute on assigned local machine"));return}
    if req.WorkspaceRoot==""||!filepath.IsAbs(req.WorkspaceRoot){writeErr(w,400,errors.New("absolute workspace_root required"));return}
    ctx,cancel:=context.WithTimeout(r.Context(),15*time.Second);defer cancel()
    result,err:=casecontroller.Continue(ctx,req.CaseID,s.machine,req.WorkspaceRoot,"http://127.0.0.1:8848",nil)
    if err!=nil{writeJSON(w,http.StatusConflict,map[string]any{"ok":false,"case_id":req.CaseID,"machine":s.machine,"workspace_root":req.WorkspaceRoot,"controller":"go-native","python_controller_used":false,"stage":"go_native_continue_failed","error":err.Error(),"authority":"openworker-go-native-case-controller","github_action_used":false});return}
    detail,_:=json.Marshal(result);_=s.store.RecordClusterControl(result.WorkID,"go_case_continue",s.machine,string(detail))
    writeJSON(w,http.StatusAccepted,map[string]any{"ok":true,"case_id":req.CaseID,"machine":s.machine,"workspace_root":req.WorkspaceRoot,"controller":"go-native","python_controller_used":false,"stage":"go_native_continue_accepted","result":result,"authority":"openworker-go-native-case-controller","github_action_used":false})
}
