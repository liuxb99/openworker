package evidence

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func testWrite(t *testing.T, path string, data []byte) {
	t.Helper()
	if err := os.WriteFile(path, data, 0o644); err != nil {
		t.Fatalf("write %s: %v", path, err)
	}
}

func testHash(data []byte) string {
	sum := sha256.Sum256(data)
	return hex.EncodeToString(sum[:])
}

func TestValidateAIOpenSeesWorkspace(t *testing.T) {
	root := t.TempDir()
	mctSHA := testHash([]byte("real-mct-placeholder-for-validator-test"))
	generation := int64(3)

	contents := map[string][]byte{
		"analysis-geometry.json":       []byte(`{"schema_version":"ai-opensees/analysis-geometry/v0.1"}`),
		"analysis-deformed.obj":        []byte("o deformed\nv 0 0 0\n"),
		"analysis.tcl":                 []byte("model BasicBuilder -ndm 3 -ndf 6\n"),
		"node_displacements.csv":       []byte("node_id,ux,uy,uz,rx,ry,rz\n1,0,0,0,0,0,0\n"),
		"node_reactions.csv":           []byte("node_id,fx,fy,fz,mx,my,mz\n1,0,0,0,0,0,0\n"),
		"opensees.stdout.log":          []byte{},
		"opensees.stderr.log":          []byte{},
		"authority-runtime-state.json": []byte(`{"ready":true,"generation":3,"snapshot_valid":true}`),
	}
	for name, data := range contents {
		testWrite(t, filepath.Join(root, name), data)
	}

	analysis := AIOpenSeesAnalysisResult{
		SchemaVersion:         AIOpenSeesResultSchema,
		Status:                "complete",
		SourceSHA256:          mctSHA,
		AuthorityRuntimeUsed:  true,
		AuthorityGeneration:   generation,
		GeometryJSONPath:      filepath.Join(root, "analysis-geometry.json"),
		GeometryJSONSHA256:    testHash(contents["analysis-geometry.json"]),
		DeformedOBJPath:       filepath.Join(root, "analysis-deformed.obj"),
		DeformedOBJSHA256:     testHash(contents["analysis-deformed.obj"]),
		DisplacementCSVPath:   filepath.Join(root, "node_displacements.csv"),
		DisplacementCSVSHA256: testHash(contents["node_displacements.csv"]),
		ReactionCSVPath:       filepath.Join(root, "node_reactions.csv"),
		ReactionCSVSHA256:     testHash(contents["node_reactions.csv"]),
	}
	analysisData, err := json.Marshal(analysis)
	if err != nil { t.Fatal(err) }
	testWrite(t, filepath.Join(root, "analysis-result.json"), analysisData)
	contents["analysis-result.json"] = analysisData

	artifacts := make([]AIOpenSeesArtifact, 0, 9)
	for _, name := range []string{
		"analysis-result.json",
		"analysis-geometry.json",
		"analysis-deformed.obj",
		"analysis.tcl",
		"node_displacements.csv",
		"node_reactions.csv",
		"opensees.stdout.log",
		"opensees.stderr.log",
		"authority-runtime-state.json",
	} {
		data := contents[name]
		artifacts = append(artifacts, AIOpenSeesArtifact{
			Name: name, Path: filepath.Join(root, name), Bytes: int64(len(data)), SHA256: testHash(data),
		})
	}
	receipt := AIOpenSeesOperatorEvidence{
		SchemaVersion:       AIOpenSeesReceiptSchema,
		CapabilityID:        AIOpenSeesCapabilityID,
		Repository:          AIOpenSeesRepository,
		CommitSHA:           testHash([]byte("commit")),
		RunID:               "123",
		RunAttempt:          "1",
		AssignedHostname:    AIOpenSeesHost,
		MCTPath:             `D:\jobs\real.mct`,
		MCTSHA256:           mctSHA,
		RuntimeConfig:       `D:\jobs\runtime.config`,
		AuthorityGeneration: generation,
		OpenSeesExecutable:  `C:\OpenSees\OpenSees.exe`,
		Workspace:           root,
		Status:              "complete",
		Artifacts:           artifacts,
	}
	receiptData, err := json.Marshal(receipt)
	if err != nil { t.Fatal(err) }
	testWrite(t, filepath.Join(root, "operator-evidence.json"), receiptData)

	report := ValidateAIOpenSeesWorkspace(root)
	if !report.Accepted {
		t.Fatalf("expected accepted evidence, blockers=%v", report.Blockers)
	}
	if report.VerifiedArtifacts != 9 || report.AuthorityGeneration != generation || report.AssignedHostname != AIOpenSeesHost {
		t.Fatalf("unexpected report: %+v", report)
	}

	testWrite(t, filepath.Join(root, "analysis-deformed.obj"), []byte("tampered"))
	tampered := ValidateAIOpenSeesWorkspace(root)
	if tampered.Accepted {
		t.Fatal("tampered artifact must not be accepted")
	}
	found := false
	for _, blocker := range tampered.Blockers {
		if blocker == "ARTIFACT_SHA256_MISMATCH:analysis-deformed.obj" {
			found = true
			break
		}
	}
	if !found {
		t.Fatalf("expected tamper blocker, got %v", tampered.Blockers)
	}
}
