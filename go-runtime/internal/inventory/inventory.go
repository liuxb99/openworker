package inventory

import (
	"encoding/json"
	"os"
	"os/exec"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type Tool struct { Name string `json:"name"`; Available bool `json:"available"`; Path string `json:"path,omitempty"` }
type Root struct { Name string `json:"name"`; Env string `json:"env"`; Path string `json:"path,omitempty"`; Available bool `json:"available"`; Source string `json:"source,omitempty"` }
type GPU struct { Index string `json:"index"`; Name string `json:"name"`; MemoryMiB string `json:"memory_mib,omitempty"` }
type Snapshot struct { Capabilities []string `json:"capabilities"`; Tools []Tool `json:"tools"`; Roots []Root `json:"roots"`; GPUs []GPU `json:"gpus"`; CollectedAt time.Time `json:"collected_at"` }

var defaultTools=[]string{"git","go","python","powershell","blender","nvidia-smi"}
var authorityRoots=[]struct{Name,Env string}{
	{"openworker","OPENWORKER_ROOT"},
	{"go-tool-runtime","GO_TOOL_ROOT"},
	{"terrain-to-dxf","TERRAIN_ROOT"},
	{"scenex","SCENEX_ROOT"},
	{"engineering-os","ENGINEERING_OS_ROOT"},
	{"review-drive","OPENWORKER_REVIEW_DRIVE_ROOT"},
}

func Collect() Snapshot {
	caps:=splitCSV(os.Getenv("OPENWORKER_NODE_CAPABILITIES"))
	tools:=make([]Tool,0,len(defaultTools))
	for _,name:=range defaultTools{p,err:=exec.LookPath(name);tools=append(tools,Tool{Name:name,Available:err==nil,Path:p})}
	return Snapshot{Capabilities:caps,Tools:tools,Roots:collectRoots(),GPUs:collectGPUs(),CollectedAt:time.Now().UTC()}
}

func machineRootsFile() string {
	if v:=strings.TrimSpace(os.Getenv("OPENWORKER_MACHINE_ROOTS_FILE"));v!=""{return filepath.Clean(v)}
	if pd:=strings.TrimSpace(os.Getenv("ProgramData"));pd!=""{return filepath.Join(pd,"OpenWorker","machine-roots.json")}
	return filepath.Join(os.TempDir(),"openworker-machine-roots.json")
}

func readMachineRoots() map[string]string {
	data,err:=os.ReadFile(machineRootsFile());if err!=nil{return map[string]string{}}
	var raw map[string]string;if json.Unmarshal(data,&raw)!=nil{return map[string]string{}}
	out:=map[string]string{};for k,v:=range raw{if s:=strings.TrimSpace(v);s!=""{out[strings.ToUpper(strings.TrimSpace(k))]=s}}
	return out
}

func collectRoots() []Root {
	persisted:=readMachineRoots()
	out:=make([]Root,0,len(authorityRoots))
	for _,item:=range authorityRoots{
		r:=Root{Name:item.Name,Env:item.Env}
		value:=strings.TrimSpace(persisted[strings.ToUpper(item.Env)]);if value!=""{r.Source="machine-registry"}
		if env:=strings.TrimSpace(os.Getenv(item.Env));env!=""{value=env;r.Source="process-env"}
		if value!=""{
			if abs,err:=filepath.Abs(value);err==nil{r.Path=filepath.Clean(abs)}else{r.Path=filepath.Clean(value)}
			if info,err:=os.Stat(r.Path);err==nil&&info.IsDir(){r.Available=true}
		}
		out=append(out,r)
	}
	return out
}

func splitCSV(v string) []string { out:=[]string{};seen:=map[string]bool{};for _,x:=range strings.Split(v,","){x=strings.TrimSpace(x);if x!=""&&!seen[x]{seen[x]=true;out=append(out,x)}};sort.Strings(out);return out }

func collectGPUs() []GPU {
	cmd:=exec.Command("nvidia-smi","--query-gpu=index,name,memory.total","--format=csv,noheader,nounits")
	b,err:=cmd.Output();if err!=nil{return []GPU{}}
	out:=[]GPU{}
	for _,line:=range strings.Split(strings.TrimSpace(string(b)),"\n"){
		parts:=strings.Split(line,",");if len(parts)<2{continue}
		g:=GPU{Index:strings.TrimSpace(parts[0]),Name:strings.TrimSpace(parts[1])};if len(parts)>2{g.MemoryMiB=strings.TrimSpace(parts[2])};out=append(out,g)}
	return out
}
