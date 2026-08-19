package casecontroller

import (
    "bytes"
    "context"
    "crypto/sha256"
    "encoding/hex"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "os"
    "path/filepath"
    "strings"
    "time"
)

type ContinueResult struct {
    Schema string `json:"schema"`
    CaseID string `json:"case_id"`
    Machine string `json:"machine"`
    WorkspaceRoot string `json:"workspace_root"`
    Revision int `json:"revision"`
    StepID string `json:"step_id"`
    ActionID string `json:"action_id"`
    WorkID string `json:"work_id"`
    QueueStatus string `json:"queue_status"`
    QueueItem map[string]any `json:"queue_item"`
    Controller string `json:"controller"`
    PythonControllerUsed bool `json:"python_controller_used"`
    SubmittedAt time.Time `json:"submitted_at"`
}

func Continue(ctx context.Context, caseID, machine, workspaceRoot, queueURL string, client *http.Client) (ContinueResult, error) {
    if strings.TrimSpace(caseID)!="0005" { return ContinueResult{}, fmt.Errorf("unsupported case %q",caseID) }
    if err:=validateQueueURL(queueURL);err!=nil{return ContinueResult{},err}
    marker:=filepath.Join(workspaceRoot,".openworker")
    worklistPath:=filepath.Join(marker,"case-worklist.json")
    specPath:=filepath.Join(marker,"case-spec.json")
    wb,err:=os.ReadFile(worklistPath);if err!=nil{return ContinueResult{},fmt.Errorf("read worklist snapshot: %w",err)}
    var w Worklist;if err:=json.Unmarshal(wb,&w);err!=nil{return ContinueResult{},fmt.Errorf("decode worklist snapshot: %w",err)}
    if w.CaseID!=caseID || !strings.EqualFold(w.AssignedHost,machine) || !samePath(w.WorkspaceRoot,workspaceRoot){return ContinueResult{},fmt.Errorf("case authority mismatch")}
    ready:=readySteps(w.Steps);if len(ready)==0{return ContinueResult{},fmt.Errorf("no ready steps")}
    if len(ready)>1{return ContinueResult{},fmt.Errorf("multiple ready steps require G3 fanout coordinator: %v",ready)}
    step:=findStep(w.Steps,ready[0]);if step==nil{return ContinueResult{},fmt.Errorf("ready step missing")}
    if step.StepID!="0005-010"{return ContinueResult{},fmt.Errorf("Go continue mapping not implemented for %s",step.StepID)}
    if len(step.AllowedActions)!=1 || step.AllowedActions[0]!="comfyx-studio.director.preproduction"{return ContinueResult{},fmt.Errorf("0005-010 action contract mismatch: %v",step.AllowedActions)}
    sb,err:=os.ReadFile(specPath);if err!=nil{return ContinueResult{},fmt.Errorf("read case spec snapshot: %w",err)}
    var spec map[string]any;if err:=json.Unmarshal(sb,&spec);err!=nil{return ContinueResult{},fmt.Errorf("decode case spec: %w",err)}
    if strings.TrimSpace(fmt.Sprint(spec["case_id"]))!=caseID{return ContinueResult{},fmt.Errorf("case spec case_id mismatch")}
    inputs:=map[string]any{"workspace_root":workspaceRoot,"assigned_host":machine,"case_id":caseID,"source_title":strings.TrimSpace(fmt.Sprint(spec["title"])),"source_story":strings.TrimSpace(fmt.Sprint(spec["source_story"]))}
    if inputs["source_title"]=="" || inputs["source_story"]==""{return ContinueResult{},fmt.Errorf("director inputs require source_title and source_story")}
    action:=step.AllowedActions[0];workID:=executionID(caseID,step.StepID,action,w.Revision)
    submit:=map[string]any{"work_id":workID,"assigned_host":machine,"capability_id":action,"inputs":inputs}
    body,_:=json.Marshal(submit)
    if err:=appendLedger(filepath.Join(marker,"case-supervisor-ledger.jsonl"),ledgerEvent{Schema:"openworker.case-supervisor-ledger/v1",Timestamp:time.Now().UTC(),CaseID:caseID,Machine:machine,EventType:"go_step_dispatch_start",WorkspaceRoot:workspaceRoot,Revision:w.Revision,StepID:step.StepID,ActionID:action,WorkID:workID});err!=nil{return ContinueResult{},err}
    if client==nil{client=&http.Client{Timeout:10*time.Second}}
    req,err:=http.NewRequestWithContext(ctx,http.MethodPost,strings.TrimRight(queueURL,"/")+"/api/execution/local-work",bytes.NewReader(body));if err!=nil{return ContinueResult{},err};req.Header.Set("Content-Type","application/json")
    resp,err:=client.Do(req);if err!=nil{return ContinueResult{},fmt.Errorf("submit local work: %w",err)};defer resp.Body.Close();raw,err:=io.ReadAll(io.LimitReader(resp.Body,2<<20));if err!=nil{return ContinueResult{},err};if resp.StatusCode/100!=2{return ContinueResult{},fmt.Errorf("local work HTTP %d: %s",resp.StatusCode,strings.TrimSpace(string(raw)))}
    var item map[string]any;if err:=json.Unmarshal(raw,&item);err!=nil{return ContinueResult{},fmt.Errorf("decode local work ACK: %w",err)}
    if strings.TrimSpace(fmt.Sprint(item["work_id"]))!=workID || !strings.EqualFold(strings.TrimSpace(fmt.Sprint(item["assigned_host"])),machine){return ContinueResult{},fmt.Errorf("local work ACK identity mismatch")}
    status:=strings.TrimSpace(fmt.Sprint(item["status"]));if status==""{return ContinueResult{},fmt.Errorf("local work ACK missing status")}
    result:=ContinueResult{Schema:"openworker.go-case-continue/v1",CaseID:caseID,Machine:machine,WorkspaceRoot:workspaceRoot,Revision:w.Revision,StepID:step.StepID,ActionID:action,WorkID:workID,QueueStatus:status,QueueItem:item,Controller:"go-native",PythonControllerUsed:false,SubmittedAt:time.Now().UTC()}
    rb,_:=json.MarshalIndent(result,"","  ");if err:=atomicWrite(filepath.Join(marker,"case-controller-last.json"),append(rb,'\n'));err!=nil{return ContinueResult{},err}
    if err:=appendLedger(filepath.Join(marker,"case-supervisor-ledger.jsonl"),ledgerEvent{Schema:"openworker.case-supervisor-ledger/v1",Timestamp:time.Now().UTC(),CaseID:caseID,Machine:machine,EventType:"go_step_durable_accepted",WorkspaceRoot:workspaceRoot,Revision:w.Revision,StepID:step.StepID,ActionID:action,WorkID:workID,Detail:"go-tool durable local-work accepted with idempotent work_id"});err!=nil{return ContinueResult{},err}
    return result,nil
}

func executionID(caseID,stepID,action string,revision int)string{sum:=sha256.Sum256([]byte(fmt.Sprintf("%s|%s|%s|%d",caseID,stepID,action,revision)));return fmt.Sprintf("case%s-%s-r%06d-%s",safeID(caseID),safeID(stepID),revision,hex.EncodeToString(sum[:4]))}
func safeID(v string)string{var b strings.Builder;for _,r:=range v{if (r>='a'&&r<='z')||(r>='A'&&r<='Z')||(r>='0'&&r<='9')||r=='-'||r=='_'{b.WriteRune(r)}};return b.String()}
func findStep(steps []Step,id string)*Step{for i:=range steps{if steps[i].StepID==id{return &steps[i]}};return nil}
func validateQueueURL(raw string)error{u,err:=url.Parse(strings.TrimSpace(raw));if err!=nil{return err};h:=strings.ToLower(u.Hostname());if u.Scheme!="http"||(h!="127.0.0.1"&&h!="localhost"&&h!="::1")||u.Port()!="8848"||(u.Path!=""&&u.Path!="/"){return fmt.Errorf("queue URL must be localhost:8848")};return nil}
