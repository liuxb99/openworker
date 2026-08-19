package casecontroller

import (
    "bytes"
    "context"
    "encoding/json"
    "fmt"
    "io"
    "net/http"
    "os"
    "path/filepath"
    "strings"
    "time"
)

type fanoutState struct {
    Schema string `json:"schema"`
    CaseID string `json:"case_id"`
    Revision int `json:"revision"`
    ParentStepIDs []string `json:"parent_step_ids"`
    Children []fanoutChild `json:"children"`
    SubmittedAt time.Time `json:"submitted_at"`
}

func readFanoutState(path string)(fanoutState,bool,error){
    b,err:=os.ReadFile(path);if os.IsNotExist(err){return fanoutState{},false,nil};if err!=nil{return fanoutState{},false,err}
    var s fanoutState;if err:=json.Unmarshal(b,&s);err!=nil{return fanoutState{},false,fmt.Errorf("decode fanout state: %w",err)}
    if strings.TrimSpace(s.CaseID)==""||len(s.Children)==0{return fanoutState{},false,fmt.Errorf("invalid fanout state")}
    return s,true,nil
}

func persistFanoutState(path string,s fanoutState)error{b,err:=json.MarshalIndent(s,"","  ");if err!=nil{return err};return atomicWrite(path,append(b,'\n'))}

func submitFanoutPlan(ctx context.Context,client *http.Client,queueURL string,plan fanoutPlan)(fanoutState,map[string]any,error){
    statuses:=map[string]any{}
    for _,child:=range plan.Children{
        submit:=map[string]any{"work_id":child.WorkID,"assigned_host":child.Inputs["assigned_host"],"capability_id":child.CapabilityID,"inputs":child.Inputs}
        body,_:=json.Marshal(submit)
        req,err:=http.NewRequestWithContext(ctx,http.MethodPost,strings.TrimRight(queueURL,"/")+"/api/execution/local-work",bytes.NewReader(body));if err!=nil{return fanoutState{},nil,err};req.Header.Set("Content-Type","application/json")
        resp,err:=client.Do(req);if err!=nil{return fanoutState{},nil,fmt.Errorf("submit fanout child %s: %w",child.WorkID,err)}
        raw,readErr:=io.ReadAll(io.LimitReader(resp.Body,2<<20));resp.Body.Close();if readErr!=nil{return fanoutState{},nil,readErr}
        if resp.StatusCode/100!=2{return fanoutState{},nil,fmt.Errorf("fanout child %s HTTP %d: %s",child.WorkID,resp.StatusCode,strings.TrimSpace(string(raw)))}
        var item map[string]any;if err:=json.Unmarshal(raw,&item);err!=nil{return fanoutState{},nil,fmt.Errorf("decode child %s ACK: %w",child.WorkID,err)}
        if strings.TrimSpace(fmt.Sprint(item["work_id"]))!=child.WorkID{return fanoutState{},nil,fmt.Errorf("fanout child ACK identity mismatch %s",child.WorkID)}
        statuses[child.WorkID]=item
    }
    return fanoutState{Schema:"openworker.case-fanout-state/v1",CaseID:plan.CaseID,Revision:plan.Revision,ParentStepIDs:plan.ParentStepIDs,Children:plan.Children,SubmittedAt:time.Now().UTC()},statuses,nil
}

func reconcileFanout(ctx context.Context,client *http.Client,queueURL,workspaceRoot,worklistPath,ledgerPath string,w *Worklist,s fanoutState)(bool,map[string]any,error){
    if w==nil{return false,nil,fmt.Errorf("worklist is required")}
    if s.CaseID!=w.CaseID||s.Revision!=w.Revision{return false,nil,fmt.Errorf("fanout authority mismatch")}
    summary:=map[string]any{}
    allCompleted:=true
    childEvidence:=map[string][]map[string]any{}
    for _,child:=range s.Children{
        item,err:=getQueueWork(ctx,client,queueURL,child.WorkID);if err!=nil{return false,nil,fmt.Errorf("read fanout child %s: %w",child.WorkID,err)}
        summary[child.WorkID]=item
        status:=strings.ToLower(strings.TrimSpace(fmt.Sprint(item["status"])))
        switch status{
        case "pending","claimed","running":allCompleted=false
        case "completed":
            ev,err:=completedEvidence(item);if err!=nil{return false,nil,fmt.Errorf("fanout child %s evidence: %w",child.WorkID,err)}
            ev["_fanout_work_id"]=child.WorkID;ev["_fanout_evidence_prefix"]=child.EvidencePrefix
            childEvidence[child.ParentStepID]=append(childEvidence[child.ParentStepID],ev)
        case "failed":
            parent:=findStep(w.Steps,child.ParentStepID);if parent==nil{return false,nil,fmt.Errorf("fanout parent %s missing",child.ParentStepID)}
            blocker:=strings.TrimSpace(fmt.Sprint(item["error"]));if blocker==""{blocker="fanout child failed without error detail"}
            parent.Status="FAILED";parent.Blocker=fmt.Sprintf("child %s: %s",child.WorkID,blocker)
            if err:=persistWorklist(worklistPath,*w);err!=nil{return false,nil,err}
            _=appendLedger(ledgerPath,ledgerEvent{Schema:"openworker.case-supervisor-ledger/v1",Timestamp:time.Now().UTC(),CaseID:w.CaseID,Machine:w.AssignedHost,EventType:"go_fanout_child_failed",WorkspaceRoot:workspaceRoot,Revision:w.Revision,StepID:parent.StepID,ActionID:child.CapabilityID,WorkID:child.WorkID,Detail:parent.Blocker})
            return false,summary,fmt.Errorf("fanout child %s failed: %s",child.WorkID,blocker)
        default:return false,summary,fmt.Errorf("fanout child %s unsupported status %q",child.WorkID,status)
        }
    }
    if !allCompleted{return false,summary,nil}

    for _,parentID:=range s.ParentStepIDs{
        parent:=findStep(w.Steps,parentID);if parent==nil{return false,summary,fmt.Errorf("fanout parent %s missing",parentID)}
        evs:=childEvidence[parentID];if len(evs)==0{return false,summary,fmt.Errorf("fanout parent %s has no completed child evidence",parentID)}
        prefix:=strings.TrimSpace(parent.FanoutEvidencePrefix);if prefix==""{return false,summary,fmt.Errorf("fanout parent %s missing evidence prefix",parentID)}
        receipts:=make([]any,0,len(evs));images:=make([]string,0,len(evs));hashes:=make([]string,0,len(evs))
        for _,ev:=range evs{
            receipt,ok:=ev["receipt"].(map[string]any);if !ok{return false,summary,fmt.Errorf("fanout parent %s child receipt missing",parentID)}
            data,ok:=receipt["data"].(map[string]any);if !ok{return false,summary,fmt.Errorf("fanout parent %s receipt data missing",parentID)}
            rel:=strings.TrimSpace(fmt.Sprint(data["workspace_relpath"]));if rel==""{return false,summary,fmt.Errorf("fanout parent %s workspace_relpath missing",parentID)}
            artifact,ok:=data["workspace_artifact"].(map[string]any);if !ok{return false,summary,fmt.Errorf("fanout parent %s workspace_artifact missing",parentID)}
            sha:=strings.TrimSpace(fmt.Sprint(artifact["sha256"]));if sha==""{return false,summary,fmt.Errorf("fanout parent %s sha256 missing",parentID)}
            receipts=append(receipts,receipt);images=append(images,filepath.Join(workspaceRoot,filepath.FromSlash(rel)));hashes=append(hashes,sha)
        }
        evidence:=map[string]any{prefix+"_receipts":receipts,prefix+"_images":images,prefix+"_sha256":hashes}
        if err:=validateAcceptance(*parent,evidence);err!=nil{return false,summary,fmt.Errorf("fanout parent %s acceptance: %w",parentID,err)}
        parent.Status="SUCCEEDED";parent.Evidence=evidence;parent.Blocker=""
        _=appendLedger(ledgerPath,ledgerEvent{Schema:"openworker.case-supervisor-ledger/v1",Timestamp:time.Now().UTC(),CaseID:w.CaseID,Machine:w.AssignedHost,EventType:"go_fanout_parent_reconciled_completed",WorkspaceRoot:workspaceRoot,Revision:w.Revision,StepID:parentID,Detail:fmt.Sprintf("%d durable children completed",len(evs))})
    }
    if err:=persistWorklist(worklistPath,*w);err!=nil{return false,summary,err}
    return true,summary,nil
}
