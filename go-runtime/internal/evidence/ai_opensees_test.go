package evidence

import (
	"crypto/sha256"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
	"strings"
	"testing"
)

func testWrite(t *testing.T, path string, data []byte) { t.Helper(); if err:=os.WriteFile(path,data,0o644);err!=nil{t.Fatalf("write %s: %v",path,err)} }
func testHash(data []byte) string { sum:=sha256.Sum256(data); return hex.EncodeToString(sum[:]) }
func hasBlocker(report AIOpenSeesEvidenceReport, want string) bool { for _,b:=range report.Blockers { if b==want || strings.HasPrefix(b,want) { return true } }; return false }

func TestValidateAIOpenSeesWorkspace(t *testing.T) {
	root:=t.TempDir()
	mctData:=[]byte("real-mct-placeholder-for-validator-test"); mctSHA:=testHash(mctData); mctPath:=filepath.Join(root,"real.mct"); testWrite(t,mctPath,mctData)
	configData:=[]byte("schema_version=ai-opensees/mct-authority-runtime-config/v0.1\ncatalog_root=authority-catalog\nrequire_valid_snapshot=true\n"); configPath:=filepath.Join(root,"runtime.config"); testWrite(t,configPath,configData)
	exeData:=[]byte("real-opensees-executable-placeholder"); exePath:=filepath.Join(root,"OpenSees.exe"); testWrite(t,exePath,exeData)
	snapshot:=testHash([]byte("authority-snapshot")); generation:=int64(3); catalog:=filepath.Join(root,"authority-catalog"); if err:=os.MkdirAll(catalog,0o755);err!=nil{t.Fatal(err)}
	runtime:=AIOpenSeesRuntimeState{SchemaVersion:AIOpenSeesRuntimeSchema,Ready:true,Generation:generation,ConfigPath:configPath,CatalogRoot:catalog,EntryCount:3,ElasticMaterialAuthorityCount:1,PrismaticSectionAuthorityCount:1,StaticNodalLoadAuthorityCount:1,SnapshotSHA256:snapshot,SnapshotValid:true}
	runtimeData,_:=json.Marshal(runtime)
	contents:=map[string][]byte{
		"analysis-geometry.json":[]byte(`{"schema_version":"ai-opensees/analysis-geometry/v0.2"}`),
		"analysis-deformed.obj":[]byte("o deformed\nv 0 0 0\n"),
		"analysis-deformation.svg":[]byte(`<svg xmlns="http://www.w3.org/2000/svg"></svg>`),
		"analysis.tcl":[]byte("model BasicBuilder -ndm 3 -ndf 6\n"),
		"node_displacements.csv":[]byte("node_id,ux,uy,uz,rx,ry,rz\n1,0,0,0,0,0,0\n"),
		"node_reactions.csv":[]byte("node_id,fx,fy,fz,mx,my,mz\n1,0,0,0,0,0,0\n"),
		"opensees.stdout.log":{}, "opensees.stderr.log":{}, "authority-runtime-state.json":runtimeData,
	}
	for name,data:=range contents { testWrite(t,filepath.Join(root,name),data) }
	analysis:=AIOpenSeesAnalysisResult{SchemaVersion:AIOpenSeesResultSchema,Status:"complete",Solver:"OpenSees",SolverExecutable:exePath,SolverVersion:"OpenSees 3.7.1",RawExitCode:0,SourcePath:mctPath,SourceSHA256:mctSHA,AuthorityRuntimeUsed:true,AuthorityGeneration:generation,AuthorityConfigPath:configPath,AuthorityCatalogRoot:catalog,AuthorityEntryCount:3,AuthoritySnapshotSHA256:snapshot,ScriptPath:filepath.Join(root,"analysis.tcl"),ScriptSHA256:testHash(contents["analysis.tcl"]),StdoutPath:filepath.Join(root,"opensees.stdout.log"),StdoutSHA256:testHash(contents["opensees.stdout.log"]),StderrPath:filepath.Join(root,"opensees.stderr.log"),StderrSHA256:testHash(contents["opensees.stderr.log"]),GeometryJSONPath:filepath.Join(root,"analysis-geometry.json"),GeometryJSONSHA256:testHash(contents["analysis-geometry.json"]),DeformedOBJPath:filepath.Join(root,"analysis-deformed.obj"),DeformedOBJSHA256:testHash(contents["analysis-deformed.obj"]),DeformationSVGPath:filepath.Join(root,"analysis-deformation.svg"),DeformationSVGSHA256:testHash(contents["analysis-deformation.svg"]),DisplacementCSVPath:filepath.Join(root,"node_displacements.csv"),DisplacementCSVSHA256:testHash(contents["node_displacements.csv"]),ReactionCSVPath:filepath.Join(root,"node_reactions.csv"),ReactionCSVSHA256:testHash(contents["node_reactions.csv"])}
	analysisData,_:=json.Marshal(analysis); testWrite(t,filepath.Join(root,"analysis-result.json"),analysisData); contents["analysis-result.json"]=analysisData
	required:=[]string{"analysis-result.json","analysis-geometry.json","analysis-deformed.obj","analysis-deformation.svg","analysis.tcl","node_displacements.csv","node_reactions.csv","opensees.stdout.log","opensees.stderr.log","authority-runtime-state.json"}
	artifacts:=make([]AIOpenSeesArtifact,0,len(required)); for _,name:=range required { data:=contents[name]; artifacts=append(artifacts,AIOpenSeesArtifact{Name:name,Path:filepath.Join(root,name),Bytes:int64(len(data)),SHA256:testHash(data)}) }
	receipt:=AIOpenSeesOperatorEvidence{SchemaVersion:AIOpenSeesReceiptSchema,CapabilityID:AIOpenSeesCapabilityID,Repository:AIOpenSeesRepository,CommitSHA:"0123456789abcdef0123456789abcdef01234567",RunID:"123",RunAttempt:"1",AssignedHostname:AIOpenSeesHost,MCTPath:mctPath,MCTSHA256:mctSHA,RuntimeConfig:configPath,RuntimeConfigSHA256:testHash(configData),AuthorityGeneration:generation,AuthorityCatalogRoot:catalog,AuthorityEntryCount:3,ElasticMaterialAuthorityCount:1,PrismaticSectionAuthorityCount:1,StaticNodalLoadAuthorityCount:1,AuthoritySnapshotSHA256:snapshot,OpenSeesExecutable:exePath,OpenSeesExecutableSHA256:testHash(exeData),Solver:"OpenSees",SolverVersion:"OpenSees 3.7.1",SolverRawExitCode:0,Workspace:root,Status:"complete",Artifacts:artifacts}
	writeReceipt:=func(v AIOpenSeesOperatorEvidence){ data,_:=json.Marshal(v); testWrite(t,filepath.Join(root,"operator-evidence.json"),data) }
	writeAnalysis:=func(v AIOpenSeesAnalysisResult){ data,_:=json.Marshal(v); testWrite(t,filepath.Join(root,"analysis-result.json"),data) }
	writeRuntime:=func(v AIOpenSeesRuntimeState){ data,_:=json.Marshal(v); testWrite(t,filepath.Join(root,"authority-runtime-state.json"),data) }
	writeReceipt(receipt)
	if report:=ValidateAIOpenSeesWorkspace(root); !report.Accepted { t.Fatalf("expected accepted evidence, blockers=%v",report.Blockers) }

	missingMaterial:=receipt; missingMaterial.ElasticMaterialAuthorityCount=0; writeReceipt(missingMaterial); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"MATERIAL_AUTHORITY_COVERAGE_MISSING") { t.Fatalf("missing MATERIAL authority not blocked: %v",r.Blockers) }
	missingSection:=receipt; missingSection.PrismaticSectionAuthorityCount=0; writeReceipt(missingSection); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"SECTION_AUTHORITY_COVERAGE_MISSING") { t.Fatalf("missing SECTION authority not blocked: %v",r.Blockers) }
	missingLoad:=receipt; missingLoad.StaticNodalLoadAuthorityCount=0; writeReceipt(missingLoad); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"STATIC_NODAL_LOAD_AUTHORITY_COVERAGE_MISSING") { t.Fatalf("missing STATIC_NODAL_LOAD authority not blocked: %v",r.Blockers) }
	writeReceipt(receipt)
	runtimeDrift:=runtime; runtimeDrift.StaticNodalLoadAuthorityCount=0; writeRuntime(runtimeDrift); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"RUNTIME_STATIC_NODAL_LOAD_AUTHORITY_COUNT_MISMATCH") { t.Fatalf("runtime authority coverage drift not blocked: %v",r.Blockers) }; writeRuntime(runtime)

	badSolver:=receipt; badSolver.Solver="NotOpenSees"; writeReceipt(badSolver); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"SOLVER_IDENTITY_MISMATCH") { t.Fatalf("solver identity drift not blocked: %v",r.Blockers) }
	badVersion:=receipt; badVersion.SolverVersion=""; writeReceipt(badVersion); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"SOLVER_VERSION_EMPTY") { t.Fatalf("empty solver version not blocked: %v",r.Blockers) }
	badExit:=receipt; badExit.SolverRawExitCode=1; writeReceipt(badExit); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"SOLVER_RAW_EXIT_CODE_NONZERO") { t.Fatalf("nonzero solver exit not blocked: %v",r.Blockers) }
	writeReceipt(receipt)
	analysisDrift:=analysis; analysisDrift.SolverVersion="OpenSees other"; writeAnalysis(analysisDrift); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"SOLVER_VERSION_CROSS_BIND_MISMATCH") { t.Fatalf("solver version cross-bind drift not blocked: %v",r.Blockers) }
	writeAnalysis(analysis)
	testWrite(t,mctPath,[]byte("tampered-real-mct")); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"MCT_FILE_SHA256_MISMATCH") { t.Fatalf("MCT tamper not blocked: %v",r.Blockers) }; testWrite(t,mctPath,mctData)
	testWrite(t,configPath,[]byte("tampered-config")); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"RUNTIME_CONFIG_FILE_SHA256_MISMATCH") { t.Fatalf("config tamper not blocked: %v",r.Blockers) }; testWrite(t,configPath,configData)
	testWrite(t,exePath,[]byte("tampered-exe")); if r:=ValidateAIOpenSeesWorkspace(root); r.Accepted||!hasBlocker(r,"OPENSEES_EXECUTABLE_FILE_SHA256_MISMATCH") { t.Fatalf("solver executable tamper not blocked: %v",r.Blockers) }; testWrite(t,exePath,exeData)
}
