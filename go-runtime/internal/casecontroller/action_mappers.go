package casecontroller

import (
	"encoding/json"
	"fmt"
	"path/filepath"
	"strings"
)

type actionMapContext struct {
	Step          *Step
	Worklist      Worklist
	WorkspaceRoot string
	Machine       string
	SpecPath      string
}

type actionMapper func(actionMapContext) (map[string]any, error)

var actionMappers = map[string]actionMapper{
	"cad.build_story_index":                mapStoryIndex,
	"comfyx-studio.director.preproduction": mapDirectorPreproduction,
	"comfyx-studio.storyboard.plan":        mapStoryboardPlan,
	"presentation.openmaic":                mapPresentationOpenMAIC,
	"openworker.case.publish-artifacts":     mapCasePublishArtifacts,
	"openworker.review.await-drive":         mapDriveApprovalGate,
}

// actionDispatchAliases separates the worklist-facing action contract from the
// local executor capability. Most actions are identical; aliases are explicit
// and fail-closed so manifest-driven Cases do not silently route to the wrong
// leaf executor.
var actionDispatchAliases = map[string]string{
	"cad.build_story_index": "dwg.story_index.execute.case-worklist",
}

func mapActionInputs(step *Step, w Worklist, workspaceRoot, machine, specPath string) (string, map[string]any, error) {
	if step == nil {
		return "", nil, fmt.Errorf("step is required")
	}
	if len(step.AllowedActions) != 1 {
		return "", nil, fmt.Errorf("step %s requires exactly one allowed action", step.StepID)
	}
	action := strings.TrimSpace(step.AllowedActions[0])
	if action == "" {
		return "", nil, fmt.Errorf("step %s has empty allowed action", step.StepID)
	}
	mapper, ok := actionMappers[action]
	if !ok {
		return "", nil, fmt.Errorf("no registered action mapper for capability %q", action)
	}
	inputs, err := mapper(actionMapContext{Step: step, Worklist: w, WorkspaceRoot: workspaceRoot, Machine: machine, SpecPath: specPath})
	if err != nil {
		return "", nil, fmt.Errorf("map capability %s for step %s: %w", action, step.StepID, err)
	}
	dispatchAction := action
	if alias := strings.TrimSpace(actionDispatchAliases[action]); alias != "" {
		dispatchAction = alias
	}
	return dispatchAction, inputs, nil
}

func dependencyStep(ctx actionMapContext, index int) (*Step, error) {
	if index < 0 || index >= len(ctx.Step.Dependencies) {
		return nil, fmt.Errorf("step %s dependency[%d] unavailable", ctx.Step.StepID, index)
	}
	id := ctx.Step.Dependencies[index]
	parent := findStep(ctx.Worklist.Steps, id)
	if parent == nil {
		return nil, fmt.Errorf("dependency %s missing from worklist", id)
	}
	if !strings.EqualFold(parent.Status, "SUCCEEDED") && !strings.EqualFold(parent.Status, "PASSED") && !strings.EqualFold(parent.Status, "COMPLETED") {
		return nil, fmt.Errorf("dependency %s is not terminal-success: %s", id, parent.Status)
	}
	return parent, nil
}

func evidenceFile(ctx actionMapContext, parent *Step, key string) (string, error) {
	raw := strings.TrimSpace(fmt.Sprint(parent.Evidence[key]))
	if raw == "" {
		return "", fmt.Errorf("dependency %s evidence missing %s", parent.StepID, key)
	}
	return workspaceRelativeExistingFile(ctx.WorkspaceRoot, raw, key)
}

func mapStoryIndex(ctx actionMapContext) (map[string]any, error) {
	spec, err := readCaseSpec(ctx.SpecPath, ctx.Worklist.CaseID)
	if err != nil { return nil, err }
	raw, ok := spec["story_index_build_params"]
	if !ok { return nil, fmt.Errorf("case spec missing story_index_build_params") }
	params, err := json.Marshal(raw)
	if err != nil { return nil, fmt.Errorf("encode story_index_build_params: %w", err) }
	return map[string]any{"method":"cad.build_story_index","params_json":string(params),"workspace_root":ctx.WorkspaceRoot,"assigned_host":ctx.Machine,"case_step":ctx.Step.StepID}, nil
}

func mapDirectorPreproduction(ctx actionMapContext) (map[string]any, error) {
	spec, err := readCaseSpec(ctx.SpecPath, ctx.Worklist.CaseID)
	if err != nil { return nil, err }
	title := strings.TrimSpace(fmt.Sprint(spec["title"]))
	story := strings.TrimSpace(fmt.Sprint(spec["source_story"]))
	if title == "" || story == "" { return nil, fmt.Errorf("director inputs require title and source_story") }
	return map[string]any{"workspace_root":ctx.WorkspaceRoot,"assigned_host":ctx.Machine,"case_id":ctx.Worklist.CaseID,"source_title":title,"source_story":story}, nil
}

func mapStoryboardPlan(ctx actionMapContext) (map[string]any, error) {
	parent, err := dependencyStep(ctx, 0); if err != nil { return nil, err }
	rel, err := evidenceFile(ctx, parent, "director_plan"); if err != nil { return nil, err }
	return map[string]any{"workspace_root":ctx.WorkspaceRoot,"assigned_host":ctx.Machine,"director_plan_relpath":rel}, nil
}

func mapPresentationOpenMAIC(ctx actionMapContext) (map[string]any, error) {
	parent, err := dependencyStep(ctx, 0); if err != nil { return nil, err }
	rel, err := evidenceFile(ctx, parent, "storyboard_request"); if err != nil { return nil, err }
	return map[string]any{"workspace_root":ctx.WorkspaceRoot,"assigned_host":ctx.Machine,"request_relpath":rel,"output_relpath":filepath.Join("presentation","storyboard-text-only.pptx")}, nil
}

func mapCasePublishArtifacts(ctx actionMapContext) (map[string]any, error) {
	parent, err := dependencyStep(ctx, 0); if err != nil { return nil, err }
	keys := []string{"storyboard_pptx","storyboard_manifest","reopen_receipt"}
	artifacts := make([]string, 0, len(keys))
	for _, key := range keys {
		rel, err := evidenceFile(ctx, parent, key); if err != nil { return nil, err }
		artifacts = append(artifacts, filepath.ToSlash(rel))
	}
	revisionID := fmt.Sprintf("case%s-%s-r%06d", safeID(ctx.Worklist.CaseID), safeID(ctx.Step.StepID), ctx.Worklist.Revision)
	workCode := strings.ToUpper(fmt.Sprintf("CASE%s-%s-R%06d", safeID(ctx.Worklist.CaseID), safeID(ctx.Step.StepID), ctx.Worklist.Revision))
	return map[string]any{"workspace_root":ctx.WorkspaceRoot,"assigned_host":ctx.Machine,"case_id":ctx.Worklist.CaseID,"step_id":ctx.Step.StepID,"revision_id":revisionID,"work_code":workCode,"artifacts":artifacts}, nil
}

func mapDriveApprovalGate(ctx actionMapContext) (map[string]any, error) {
	parent, err := dependencyStep(ctx, 0); if err != nil { return nil, err }
	if strings.TrimSpace(fmt.Sprint(parent.Evidence["drive_folder_id"])) == "" || strings.TrimSpace(fmt.Sprint(parent.Evidence["manifest_sha256"])) == "" {
		return nil, fmt.Errorf("publish dependency evidence incomplete")
	}
	return map[string]any{"workspace_root":ctx.WorkspaceRoot,"assigned_host":ctx.Machine,"step_id":ctx.Step.StepID,"evidence_relpath":filepath.ToSlash(filepath.Join("evidence",ctx.Step.StepID+"-drive-gate.json")),"timeout_seconds":43200}, nil
}
