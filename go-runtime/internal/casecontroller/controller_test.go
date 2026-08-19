package casecontroller

import (
    "os"
    "path/filepath"
    "runtime"
    "testing"
)

func writeFixture(t *testing.T, workspace string)(string,string){t.Helper();root:=t.TempDir();manifest:=filepath.Join(root,"0005.json");spec:=filepath.Join(root,"spec.json");body:=`{"schema_version":"openworker-case-worklist/v1","case_id":"0005","workspace_root":"`+workspace+`","assigned_host":"DESKTOP-ODAQN0D","revision":13,"steps":[{"step_id":"0005-010","dependencies":[],"allowed_actions":["comfyx-studio.director.preproduction"],"status":"PENDING","evidence":{}}]}`;if err:=os.WriteFile(manifest,[]byte(body),0o644);err!=nil{t.Fatal(err)};if err:=os.WriteFile(spec,[]byte(`{"case_id":"0005","title":"Snow White","source_story":"story"}`),0o644);err!=nil{t.Fatal(err)};return manifest,spec}
func TestBootstrapCase0005(t *testing.T){if runtime.GOOS=="windows"{t.Skip("portable fixture uses temp workspace path")};workspace:=filepath.Join(t.TempDir(),"workspace");manifest,spec:=writeFixture(t,workspace);got,err:=Bootstrap("0005","DESKTOP-ODAQN0D",workspace,manifest,spec);if err!=nil{t.Fatal(err)};if got.PythonRequired{t.Fatal("native Go bootstrap must not require Python")};if got.Revision!=13||len(got.ReadyStepIDs)!=1||got.ReadyStepIDs[0]!="0005-010"{t.Fatalf("unexpected result: %#v",got)};for _,p:=range[]string{got.LedgerPath,got.WorklistSnapshot,got.SpecSnapshot,got.ControllerSnapshot}{if _,err:=os.Stat(p);err!=nil{t.Fatal(err)}}}
func TestBootstrapRejectsWrongMachine(t *testing.T){workspace:=filepath.Join(t.TempDir(),"workspace");manifest,spec:=writeFixture(t,workspace);if _,err:=Bootstrap("0005","OTHER",workspace,manifest,spec);err==nil{t.Fatal("expected machine mismatch")}}
