package casecontroller

import (
    "encoding/json"
    "os"
    "path/filepath"
    "testing"
)

func TestBuildCase0005VisualFanoutPlan(t *testing.T) {
    workspace := t.TempDir()
    if err := os.MkdirAll(filepath.Join(workspace,"visual-assets"),0o755); err != nil { t.Fatal(err) }
    req := map[string]any{"requirements":[]map[string]any{
        {"asset_id":"char-snow-white","role":"character_master"},
        {"asset_id":"scene-forest","role":"scene_concept"},
        {"asset_id":"shot-001","role":"shot_storyboard"},
    }}
    raw,_ := json.Marshal(req)
    if err := os.WriteFile(filepath.Join(workspace,"visual-assets","requirements.json"),raw,0o644); err != nil { t.Fatal(err) }
    w := Worklist{CaseID:"0005",Revision:14,Steps:[]Step{
        {StepID:"0005-027",Status:"SUCCEEDED"},
        {StepID:"0005-030",Status:"PENDING",AllowedActions:[]string{"image.comfyx.storyboard-real"}},
        {StepID:"0005-040",Status:"PENDING",AllowedActions:[]string{"image.comfyx.storyboard-real"}},
    }}
    got,err := buildCase0005VisualFanoutPlan(w,workspace,"DESKTOP-ODAQN0D")
    if err != nil { t.Fatal(err) }
    if got.Schema!="openworker.case0005-visual-fanout-plan/v1" || len(got.Children)!=2 { t.Fatalf("unexpected plan %#v",got) }
    if got.Children[0].ParentStepID!="0005-030" || got.Children[1].ParentStepID!="0005-040" { t.Fatalf("unexpected parent ordering %#v",got.Children) }
    for _,child := range got.Children {
        if child.CapabilityID!="image.comfyx.storyboard-real" { t.Fatalf("unexpected capability %#v",child) }
        if child.WorkID=="" { t.Fatal("missing deterministic work_id") }
        if child.Inputs["requirements_relpath"]!="visual-assets/requirements.json" { t.Fatalf("unexpected requirements path %#v",child.Inputs) }
    }
}

func TestBuildCase0005VisualFanoutRequiresApproval(t *testing.T) {
    w := Worklist{CaseID:"0005",Revision:14,Steps:[]Step{{StepID:"0005-027",Status:"PENDING"},{StepID:"0005-030",AllowedActions:[]string{"image.comfyx.storyboard-real"}},{StepID:"0005-040",AllowedActions:[]string{"image.comfyx.storyboard-real"}}}}
    if _,err := buildCase0005VisualFanoutPlan(w,t.TempDir(),"DESKTOP-ODAQN0D"); err==nil { t.Fatal("expected approval gate failure") }
}
