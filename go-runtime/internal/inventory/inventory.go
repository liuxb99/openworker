package inventory

import (
	"os"
	"os/exec"
	"sort"
	"strings"
	"time"
)

type Tool struct { Name string `json:"name"`; Available bool `json:"available"`; Path string `json:"path,omitempty"` }
type GPU struct { Index string `json:"index"`; Name string `json:"name"`; MemoryMiB string `json:"memory_mib,omitempty"` }
type Snapshot struct { Capabilities []string `json:"capabilities"`; Tools []Tool `json:"tools"`; GPUs []GPU `json:"gpus"`; CollectedAt time.Time `json:"collected_at"` }

var defaultTools=[]string{"git","go","python","powershell","blender","nvidia-smi"}

func Collect() Snapshot {
	caps:=splitCSV(os.Getenv("OPENWORKER_NODE_CAPABILITIES"))
	tools:=make([]Tool,0,len(defaultTools))
	for _,name:=range defaultTools{p,err:=exec.LookPath(name);tools=append(tools,Tool{Name:name,Available:err==nil,Path:p})}
	return Snapshot{Capabilities:caps,Tools:tools,GPUs:collectGPUs(),CollectedAt:time.Now().UTC()}
}

func splitCSV(v string) []string { out:=[]string{};seen:=map[string]bool{};for _,x:=range strings.Split(v,","){x=strings.TrimSpace(x);if x!=""&&!seen[x]{seen[x]=true;out=append(out,x)}};sort.Strings(out);return out }

func collectGPUs() []GPU {
	cmd:=exec.Command("nvidia-smi","--query-gpu=index,name,memory.total","--format=csv,noheader,nounits")
	b,err:=cmd.Output();if err!=nil{return []GPU{}}
	out:=[]GPU{}
	for _,line:=range strings.Split(strings.TrimSpace(string(b)),"\n"){
		parts:=strings.Split(line,",");if len(parts)<2{continue}
		g:=GPU{Index:strings.TrimSpace(parts[0]),Name:strings.TrimSpace(parts[1])};if len(parts)>2{g.MemoryMiB=strings.TrimSpace(parts[2])};out=append(out,g)
	}
	return out
}
