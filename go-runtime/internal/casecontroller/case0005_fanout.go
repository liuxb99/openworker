package casecontroller

import (
    "encoding/json"
    "fmt"
    "os"
    "path/filepath"
    "sort"
    "strings"
)

type case0005VisualRequirement struct {
    AssetID string `json:"asset_id"`
    Role string `json:"role"`
}

type case0005VisualRequirements struct {
    Requirements []case0005VisualRequirement `json:"requirements"`
}

type case0005FanoutChild struct {
    ParentStepID string `json:"parent_step_id"`
    WorkID string `json:"work_id"`
    CapabilityID string `json:"capability_id"`
    Inputs map[string]any `json:"inputs"`
}

type case0005FanoutPlan struct {
    Schema string `json:"schema"`
    CaseID string `json:"case_id"`
    Revision int `json:"revision"`
    Children []case0005FanoutChild `json:"children"`
}

// buildCase0005VisualFanoutPlan creates the complete queue-owned child plan for
// 0005-030 and 0005-040. It is intentionally side-effect free: callers must
// submit all children to the existing :8848 durable queue before observing
// terminal state. The function never executes image generation itself.
func buildCase0005VisualFanoutPlan(w Worklist, workspaceRoot, machine string) (case0005FanoutPlan, error) {
    if w.CaseID != "0005" { return case0005FanoutPlan{}, fmt.Errorf("visual fanout only supports Case0005") }
    approved := findStep(w.Steps, "0005-027")
    if approved == nil || !strings.EqualFold(approved.Status, "SUCCEEDED") {
        return case0005FanoutPlan{}, fmt.Errorf("visual fanout requires succeeded 0005-027")
    }
    charStep := findStep(w.Steps, "0005-030")
    sceneStep := findStep(w.Steps, "0005-040")
    if charStep == nil || sceneStep == nil { return case0005FanoutPlan{}, fmt.Errorf("visual fanout parent steps are missing") }
    if len(charStep.AllowedActions) != 1 || charStep.AllowedActions[0] != "image.comfyx.storyboard-real" {
        return case0005FanoutPlan{}, fmt.Errorf("0005-030 action contract mismatch")
    }
    if len(sceneStep.AllowedActions) != 1 || sceneStep.AllowedActions[0] != "image.comfyx.storyboard-real" {
        return case0005FanoutPlan{}, fmt.Errorf("0005-040 action contract mismatch")
    }

    requirementsPath := filepath.Join(workspaceRoot, "visual-assets", "requirements.json")
    raw, err := os.ReadFile(requirementsPath)
    if err != nil { return case0005FanoutPlan{}, fmt.Errorf("read visual requirements: %w", err) }
    var plan case0005VisualRequirements
    if err := json.Unmarshal(raw, &plan); err != nil { return case0005FanoutPlan{}, fmt.Errorf("decode visual requirements: %w", err) }
    if len(plan.Requirements) == 0 { return case0005FanoutPlan{}, fmt.Errorf("visual requirements are empty") }

    seen := map[string]bool{}
    children := make([]case0005FanoutChild, 0, len(plan.Requirements))
    for _, req := range plan.Requirements {
        assetID := strings.TrimSpace(req.AssetID)
        role := strings.TrimSpace(req.Role)
        if assetID == "" { return case0005FanoutPlan{}, fmt.Errorf("visual requirement contains empty asset_id") }
        if seen[strings.ToLower(assetID)] { return case0005FanoutPlan{}, fmt.Errorf("duplicate visual asset_id %q", assetID) }
        seen[strings.ToLower(assetID)] = true

        parent := ""
        switch role {
        case "character_master": parent = "0005-030"
        case "scene_concept": parent = "0005-040"
        default: continue
        }
        capability := "image.comfyx.storyboard-real"
        workID := executionID(w.CaseID, parent+"-"+assetID, capability, w.Revision)
        children = append(children, case0005FanoutChild{
            ParentStepID: parent,
            WorkID: workID,
            CapabilityID: capability,
            Inputs: map[string]any{
                "workspace_root": workspaceRoot,
                "assigned_host": machine,
                "asset_id": assetID,
                "requirements_relpath": filepath.ToSlash(filepath.Join("visual-assets", "requirements.json")),
            },
        })
    }
    if len(children) == 0 { return case0005FanoutPlan{}, fmt.Errorf("no character_master or scene_concept fanout children") }
    sort.Slice(children, func(i, j int) bool {
        if children[i].ParentStepID != children[j].ParentStepID { return children[i].ParentStepID < children[j].ParentStepID }
        return children[i].WorkID < children[j].WorkID
    })
    return case0005FanoutPlan{Schema:"openworker.case0005-visual-fanout-plan/v1",CaseID:w.CaseID,Revision:w.Revision,Children:children}, nil
}
