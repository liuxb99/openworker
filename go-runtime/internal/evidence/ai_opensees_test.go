package evidence

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
)

func testWrite(t *testing.T, path string, data []byte) { t.Helper(); if err:=os.WriteFile(path,data,0o644);err!=nil{t.Fatalf("write %s: %v",path,err)} }
func testHash(data []byte) string { sum:=sha256.Sum256(data); return hex.EncodeToString(sum[:]) }

func TestValidateAIOpenSeesWorkspace(t *testing.T) {
	root:=t.TempDir(); mctSHA:=testHash([]byte("real-mct-placeholder-for-validator-test")); generation:=int64(3); catalogRoot:=filepath.Join(root,"authority-catalog")
	if err:=os.MkdirAll(catalogRoot,0o755);err!=nil{t.Fatal(err)}
	runtime:=AIOpenSeesRuntimeState{SchemaVersion:AIOpenSeesRuntimeSchema,Ready:true,Generation:generation,CatalogRoot:catalogRoot,EntryCount:3,SnapshotValid:true}
	runtimeData,err:=json.Marshal(runtime);if err!=nil{t.Fatal(err)}
	contents:=map[string][]byte{
		"analysis-geometry.json":[]byte(`{"schema_version":"ai-opensees/analysis-geometry/v0.2"}`),
		"analysis-deformed.obj":[]byte("o deformed\nv 0 0 0\n"),
		"analysis-deformation.svg":[]byte(`<svg xmlns="http://www.w3.org/2000/svg"><line x1="0" y1="0" x2="1" y2="1"/></svg>`),
		"analysis.tcl":[]byte("model BasicBuilder -ndm 3 -ndf 6\n"),
		"node_displacements.csv":[]byte("node_id,ux,uy,uz,rx,ry,rz\n1,0,0,0,0,0,0\n"),
		"node_reactions.csv":[]byte("node_id,fx,fy,fz,mx,my,mz\n1,0,0,0,0,0,0\n"),
		"opensees.stdout.log":{},"opensees.stderr.log":{},"authority-runtime-state.json":runtimeData,
	}
	for name,data:=range contents{testWrite(t,filepath.Join(root,name),data)}
	analysis:=AIOpenSeesAnalysisResult{SchemaVersion:AIOpenSeesResultSchema,Status:"complete",SourceSHA256:mctSHA,AuthorityRuntimeUsed:true,AuthorityGeneration:generation,AuthorityCatalogRoot:catalogRoot,AuthorityEntryCount:3,GeometryJSONPath:filepath.Join(root,"analysis-geometry.json"),GeometryJSONSHA256:testHash(contents["analysis-geometry.json"]),DeformedOBJPath:filepath.Join(root,"analysis-deformed.obj"),DeformedOBJSHA256:testHash(contents["analysis-deformed.obj"]),DeformationSVGPath:filepath.Join(root,"analysis-deformation.svg"),DeformationSVGSHA256:testHash(contents["analysis-deformation.svg"]),DisplacementCSVPath:filepath.Join(root,"node_displacements.csv"),DisplacementCSVSHA256:testHash(contents["node_displacements.csv"]),ReactionCSVPath:filepath.Join(root,"node_reactions.csv"),ReactionCSVSHA256:testHash(contents["node_reactions.csv"])}
	analysisData,err:=json.Marshal(analysis);if err!=nil{t.Fatal(err)};testWrite(t,filepath.Join(root,"analysis-result.json"),analysisData);contents["analysis-result.json"]=analysisData
	required:=[]string{"analysis-result.json","analysis-geometry.json","analysis-deformed.obj","analysis-deformation.svg","analysis.tcl","node_displacements.csv","node_reactions.csv","opensees.stdout.log","opensees.stderr.log","authority-runtime-state.json"}
	artifacts:=make([]AIOpenSeesArtifact,0,len(required));for _,name:=range required{data:=contents[name];artifacts=append(artifacts,AIOpenSeesArtifact{Name:name,Path:filepath.Join(root,name),Bytes:int64(len(data)),SHA256:testHash(data)})}
	receipt:=AIOpenSeesOperatorEvidence{SchemaVersion:AIOpenSeesReceiptSchema,CapabilityID:AIOpenSeesCapabilityID,Repository:AIOpenSeesRepository,CommitSHA:testHash([]byte("commit")),RunID:"123",RunAttempt:"1",AssignedHostname:AIOpenSeesHost,MCTPath:`D:\jobs\real.mct`,MCTSHA256:mctSHA,RuntimeConfig:`D:\jobs\runtime.config`,AuthorityGeneration:generation,AuthorityCatalogRoot:catalogRoot,AuthorityEntryCount:3,OpenSeesExecutable:`C:\OpenSees\OpenSees.exe`,Workspace:root,Status:"complete",Artifacts:artifacts}
	receiptData,err:=json.Marshal(receipt);if err!=nil{t.Fatal(err)};testWrite(t,filepath.Join(root,"operator-evidence.json"),receiptData)
	report:=ValidateAIOpenSeesWorkspace(root);if !report.Accepted{t.Fatalf("expected accepted evidence, blockers=%v",report.Blockers)};if report.VerifiedArtifacts!=10||report.AuthorityGeneration!=generation||report.AssignedHostname!=AIOpenSeesHost{t.Fatalf("unexpected report: %+v",report)}
	testWrite(t,filepath.Join(root,"analysis-deformation.svg"),[]byte("tampered"));tampered:=ValidateAIOpenSeesWorkspace(root);if tampered.Accepted{t.Fatal("tampered SVG must not be accepted")};found:=false;for _,blocker:=range tampered.Blockers{if blocker=="ARTIFACT_SHA256_MISMATCH:analysis-deformation.svg"{found=true;break}};if !found{t.Fatalf("expected SVG tamper blocker, got %v",tampered.Blockers)}
}
