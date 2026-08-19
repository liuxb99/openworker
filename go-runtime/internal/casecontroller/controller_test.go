package casecontroller

import (
    "os"
    "path/filepath"
    "runtime"
    "testing"
)

func TestBootstrapCase0005(t *testing.T) {
    if runtime.GOOS == "windows" { t.Skip("portable fixture uses temp workspace path") }
    root:=t.TempDir(); workspace:=filepath.Join(root,"workspace"); manifest:=filepath.Join(root,"0005.json")
    body:=`{"schema_version":"openworker-case-worklist/v1","case_id":"0005","workspace_root":"`+workspace+`","assigned_host":"DESKTOP-ODAQN0D","revision":13,"steps":[{"step_id":"0005-010","dependencies":[],"status":"PENDING","evidence":{}}]}`
    if err:=os.WriteFile(manifest,[]byte(body),0o644);err!=nil{t.Fatal(err)}
    got,err:=Bootstrap("0005","DESKTOP-ODAQN0D",workspace,manifest);if err!=nil{t.Fatal(err)}
    if got.PythonRequired { t.Fatal("native Go bootstrap must not require Python") }
    if got.Revision!=13 || len(got.ReadyStepIDs)!=1 || got.ReadyStepIDs[0]!="0005-010" { t.Fatalf("unexpected result: %#v",got) }
    if _,err:=os.Stat(got.LedgerPath);err!=nil{t.Fatal(err)}
}

func TestBootstrapRejectsWrongMachine(t *testing.T) {
    root:=t.TempDir();workspace:=filepath.Join(root,"workspace");manifest:=filepath.Join(root,"0005.json")
    body:=`{"schema_version":"openworker-case-worklist/v1","case_id":"0005","workspace_root":"`+workspace+`","assigned_host":"DESKTOP-ODAQN0D","revision":13,"steps":[{"step_id":"0005-010","dependencies":[],"status":"PENDING","evidence":{}}]}`
    _=os.WriteFile(manifest,[]byte(body),0o644)
    if _,err:=Bootstrap("0005","OTHER",workspace,manifest);err==nil{t.Fatal("expected machine mismatch")}
}
