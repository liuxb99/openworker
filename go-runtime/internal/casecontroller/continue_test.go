package casecontroller

import (
    "bytes"
    "context"
    "encoding/json"
    "io"
    "net/http"
    "os"
    "path/filepath"
    "testing"
)

type roundTripFunc func(*http.Request)(*http.Response,error)
func(f roundTripFunc)RoundTrip(r *http.Request)(*http.Response,error){return f(r)}

func TestContinueSubmitsDirectorToLocalQueue(t *testing.T){
    workspace:=filepath.Join(t.TempDir(),"workspace");marker:=filepath.Join(workspace,".openworker");if err:=os.MkdirAll(marker,0o755);err!=nil{t.Fatal(err)}
    worklist:=Worklist{SchemaVersion:"openworker-case-worklist/v1",CaseID:"0005",WorkspaceRoot:workspace,AssignedHost:"DESKTOP-ODAQN0D",Revision:13,Steps:[]Step{{StepID:"0005-010",Dependencies:[]string{},AllowedActions:[]string{"comfyx-studio.director.preproduction"},Status:"PENDING",Evidence:map[string]any{}}}}
    wb,_:=json.Marshal(worklist);if err:=os.WriteFile(filepath.Join(marker,"case-worklist.json"),wb,0o644);err!=nil{t.Fatal(err)}
    sb,_:=json.Marshal(map[string]any{"case_id":"0005","title":"Snow White","source_story":"A story"});if err:=os.WriteFile(filepath.Join(marker,"case-spec.json"),sb,0o644);err!=nil{t.Fatal(err)}
    var submitted map[string]any
    client:=&http.Client{Transport:roundTripFunc(func(r *http.Request)(*http.Response,error){
        if r.URL.String()!="http://127.0.0.1:8848/api/execution/local-work"{t.Fatalf("unexpected URL %s",r.URL)}
        if err:=json.NewDecoder(r.Body).Decode(&submitted);err!=nil{t.Fatal(err)}
        inputs,_:=submitted["inputs"].(map[string]any);if inputs["source_title"]!="Snow White"||inputs["source_story"]!="A story"{t.Fatalf("unexpected inputs %#v",inputs)}
        ack:=map[string]any{"work_id":submitted["work_id"],"assigned_host":"DESKTOP-ODAQN0D","capability_id":"comfyx-studio.director.preproduction","status":"pending","attempts":0};b,_:=json.Marshal(ack)
        return &http.Response{StatusCode:http.StatusCreated,Body:io.NopCloser(bytes.NewReader(b)),Header:make(http.Header)},nil
    })}
    got,err:=Continue(context.Background(),"0005","DESKTOP-ODAQN0D",workspace,"http://127.0.0.1:8848",client);if err!=nil{t.Fatal(err)}
    if got.StepID!="0005-010"||got.ActionID!="comfyx-studio.director.preproduction"||got.QueueStatus!="pending"||got.PythonControllerUsed{t.Fatalf("unexpected result %#v",got)}
    first:=got.WorkID;got2,err:=Continue(context.Background(),"0005","DESKTOP-ODAQN0D",workspace,"http://127.0.0.1:8848",client);if err!=nil{t.Fatal(err)};if got2.WorkID!=first{t.Fatalf("work_id not deterministic: %s vs %s",first,got2.WorkID)}
}
