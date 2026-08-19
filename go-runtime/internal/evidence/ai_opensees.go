package evidence

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"strings"
)

const (
	AIOpenSeesCapabilityID  = "structural.ai_opensees.authority.analyze"
	AIOpenSeesRepository    = "liuxb99/AI-OpenSees"
	AIOpenSeesHost          = "O87"
	AIOpenSeesResultSchema  = "ai-opensees/analysis-result/v0.4"
	AIOpenSeesReceiptSchema = "ai-opensees/operator-evidence/v0.1"
)

type AIOpenSeesArtifact struct {
	Name   string `json:"name"`
	Path   string `json:"path"`
	Bytes  int64  `json:"bytes"`
	SHA256 string `json:"sha256"`
}

type AIOpenSeesOperatorEvidence struct {
	SchemaVersion       string               `json:"schema_version"`
	CapabilityID        string               `json:"capability_id,omitempty"`
	Repository          string               `json:"repository"`
	CommitSHA           string               `json:"commit_sha"`
	RunID               string               `json:"run_id"`
	RunAttempt          string               `json:"run_attempt"`
	AssignedHostname    string               `json:"assigned_hostname"`
	MCTPath             string               `json:"mct_path"`
	MCTSHA256           string               `json:"mct_sha256"`
	RuntimeConfig       string               `json:"runtime_config"`
	AuthorityGeneration int64                `json:"authority_generation"`
	OpenSeesExecutable  string               `json:"opensees_executable"`
	Workspace           string               `json:"workspace"`
	Status              string               `json:"status"`
	Artifacts           []AIOpenSeesArtifact `json:"artifacts"`
}

type AIOpenSeesAnalysisResult struct {
	SchemaVersion         string `json:"schema_version"`
	Status                string `json:"status"`
	SourceSHA256          string `json:"source_sha256"`
	AuthorityRuntimeUsed  bool   `json:"authority_runtime_used"`
	AuthorityGeneration   int64  `json:"authority_generation"`
	GeometryJSONPath      string `json:"geometry_json_path"`
	GeometryJSONSHA256    string `json:"geometry_json_sha256"`
	DeformedOBJPath       string `json:"deformed_obj_path"`
	DeformedOBJSHA256     string `json:"deformed_obj_sha256"`
	DisplacementCSVPath   string `json:"displacement_csv_path"`
	DisplacementCSVSHA256 string `json:"displacement_csv_sha256"`
	ReactionCSVPath       string `json:"reaction_csv_path"`
	ReactionCSVSHA256     string `json:"reaction_csv_sha256"`
}

type AIOpenSeesEvidenceReport struct {
	SchemaVersion       string   `json:"schema_version"`
	Accepted            bool     `json:"accepted"`
	Workspace           string   `json:"workspace"`
	AssignedHostname    string   `json:"assigned_hostname,omitempty"`
	RunID               string   `json:"run_id,omitempty"`
	AuthorityGeneration int64    `json:"authority_generation,omitempty"`
	VerifiedArtifacts   int      `json:"verified_artifacts"`
	Blockers            []string `json:"blockers"`
}

func sha256File(path string) (string, int64, error) {
	f, err := os.Open(path)
	if err != nil {
		return "", 0, err
	}
	defer f.Close()
	stat, err := f.Stat()
	if err != nil {
		return "", 0, err
	}
	h := sha256.New()
	if _, err := io.Copy(h, f); err != nil {
		return "", 0, err
	}
	return hex.EncodeToString(h.Sum(nil)), stat.Size(), nil
}

func readJSON(path string, target any) error {
	data, err := os.ReadFile(path)
	if err != nil {
		return err
	}
	if len(data) == 0 {
		return fmt.Errorf("empty JSON file")
	}
	if err := json.Unmarshal(data, target); err != nil {
		return err
	}
	return nil
}

func isSHA256(value string) bool {
	if len(value) != 64 {
		return false
	}
	_, err := hex.DecodeString(value)
	return err == nil
}

func samePath(a, b string) bool {
	if strings.TrimSpace(a) == "" || strings.TrimSpace(b) == "" {
		return false
	}
	ca, errA := filepath.Abs(filepath.Clean(a))
	cb, errB := filepath.Abs(filepath.Clean(b))
	if errA != nil || errB != nil {
		return false
	}
	return strings.EqualFold(ca, cb)
}

func ValidateAIOpenSeesWorkspace(workspace string) AIOpenSeesEvidenceReport {
	report := AIOpenSeesEvidenceReport{
		SchemaVersion: "openworker/ai-opensees-evidence-report/v0.1",
		Workspace:     filepath.Clean(workspace),
		Blockers:      []string{},
	}
	add := func(code string) { report.Blockers = append(report.Blockers, code) }

	if strings.TrimSpace(workspace) == "" {
		add("WORKSPACE_EMPTY")
		return report
	}

	receiptPath := filepath.Join(workspace, "operator-evidence.json")
	resultPath := filepath.Join(workspace, "analysis-result.json")
	var receipt AIOpenSeesOperatorEvidence
	if err := readJSON(receiptPath, &receipt); err != nil {
		add("OPERATOR_EVIDENCE_INVALID:" + err.Error())
		return report
	}
	var result AIOpenSeesAnalysisResult
	if err := readJSON(resultPath, &result); err != nil {
		add("ANALYSIS_RESULT_INVALID:" + err.Error())
		return report
	}

	report.AssignedHostname = receipt.AssignedHostname
	report.RunID = receipt.RunID
	report.AuthorityGeneration = receipt.AuthorityGeneration

	if receipt.SchemaVersion != AIOpenSeesReceiptSchema {
		add("OPERATOR_EVIDENCE_SCHEMA_MISMATCH")
	}
	if receipt.CapabilityID != "" && receipt.CapabilityID != AIOpenSeesCapabilityID {
		add("CAPABILITY_ID_MISMATCH")
	}
	if receipt.Repository != AIOpenSeesRepository {
		add("REPOSITORY_MISMATCH")
	}
	if !strings.EqualFold(receipt.AssignedHostname, AIOpenSeesHost) {
		add("ASSIGNED_HOST_MISMATCH")
	}
	if receipt.Status != "complete" {
		add("OPERATOR_STATUS_NOT_COMPLETE")
	}
	if receipt.AuthorityGeneration < 1 {
		add("AUTHORITY_GENERATION_INVALID")
	}
	if !isSHA256(receipt.MCTSHA256) {
		add("MCT_SHA256_INVALID")
	}
	if !samePath(receipt.Workspace, workspace) {
		add("WORKSPACE_RECEIPT_MISMATCH")
	}

	if result.SchemaVersion != AIOpenSeesResultSchema {
		add("ANALYSIS_RESULT_SCHEMA_MISMATCH")
	}
	if result.Status != "complete" {
		add("ANALYSIS_STATUS_NOT_COMPLETE")
	}
	if !result.AuthorityRuntimeUsed {
		add("ANALYSIS_AUTHORITY_RUNTIME_NOT_USED")
	}
	if result.AuthorityGeneration != receipt.AuthorityGeneration {
		add("AUTHORITY_GENERATION_MISMATCH")
	}
	if result.SourceSHA256 != receipt.MCTSHA256 {
		add("SOURCE_SHA256_MISMATCH")
	}

	artifactByName := map[string]AIOpenSeesArtifact{}
	for _, artifact := range receipt.Artifacts {
		if artifact.Name == "" || artifact.Path == "" || !isSHA256(artifact.SHA256) {
			add("ARTIFACT_RECEIPT_INVALID:" + artifact.Name)
			continue
		}
		if _, exists := artifactByName[artifact.Name]; exists {
			add("ARTIFACT_RECEIPT_DUPLICATE:" + artifact.Name)
			continue
		}
		artifactByName[artifact.Name] = artifact
	}

	required := []string{
		"analysis-result.json",
		"analysis-geometry.json",
		"analysis-deformed.obj",
		"analysis.tcl",
		"node_displacements.csv",
		"node_reactions.csv",
		"opensees.stdout.log",
		"opensees.stderr.log",
		"authority-runtime-state.json",
	}
	for _, name := range required {
		artifact, ok := artifactByName[name]
		if !ok {
			add("ARTIFACT_RECEIPT_MISSING:" + name)
			continue
		}
		expectedPath := filepath.Join(workspace, name)
		if !samePath(artifact.Path, expectedPath) {
			add("ARTIFACT_PATH_MISMATCH:" + name)
			continue
		}
		hash, bytes, err := sha256File(expectedPath)
		if err != nil {
			add("ARTIFACT_READ_FAILED:" + name)
			continue
		}
		if hash != strings.ToLower(artifact.SHA256) {
			add("ARTIFACT_SHA256_MISMATCH:" + name)
			continue
		}
		if bytes != artifact.Bytes {
			add("ARTIFACT_SIZE_MISMATCH:" + name)
			continue
		}
		if bytes == 0 && name != "opensees.stdout.log" && name != "opensees.stderr.log" {
			add("ARTIFACT_EMPTY:" + name)
			continue
		}
		report.VerifiedArtifacts++
	}

	checks := []struct {
		name string
		path string
		hash string
	}{
		{"analysis-geometry.json", result.GeometryJSONPath, result.GeometryJSONSHA256},
		{"analysis-deformed.obj", result.DeformedOBJPath, result.DeformedOBJSHA256},
		{"node_displacements.csv", result.DisplacementCSVPath, result.DisplacementCSVSHA256},
		{"node_reactions.csv", result.ReactionCSVPath, result.ReactionCSVSHA256},
	}
	for _, check := range checks {
		artifact, ok := artifactByName[check.name]
		if !ok {
			continue
		}
		if !samePath(check.path, filepath.Join(workspace, check.name)) {
			add("ANALYSIS_ARTIFACT_PATH_MISMATCH:" + check.name)
		}
		if !isSHA256(check.hash) || strings.ToLower(check.hash) != strings.ToLower(artifact.SHA256) {
			add("ANALYSIS_ARTIFACT_SHA256_MISMATCH:" + check.name)
		}
	}

	report.Accepted = len(report.Blockers) == 0 && report.VerifiedArtifacts == len(required)
	return report
}
