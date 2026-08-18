package runtime_test

import (
	"fmt"
	"path/filepath"
	gort "runtime"
	"strings"
	"testing"
	"time"

	"github.com/liuxb99/openworker/go-runtime/internal/model"
	owruntime "github.com/liuxb99/openworker/go-runtime/internal/runtime"
	"github.com/liuxb99/openworker/go-runtime/internal/store"
)

func slowCommand() string {
	if gort.GOOS=="windows" { return `powershell -NoProfile -Command "Start-Sleep -Seconds 2"` }
	return `sleep 2`
}
func failingCommand() string {
	if gort.GOOS=="windows" { return `powershell -NoProfile -Command "[Console]::Error.WriteLine('boom-detail'); exit 7"` }
	return `sh -c 'echo boom-detail 1>&2; exit 7'`
}

func waitStatus(t *testing.T, st *store.Store, want map[model.Status]int, timeout time.Duration){
	deadline:=time.Now().Add(timeout)
	for time.Now().Before(deadline){
		jobs,err:=st.List(100);if err!=nil{t.Fatal(err)}
		counts:=map[model.Status]int{};for _,j:=range jobs{counts[j.Status]++}
		ok:=true;for s,n:=range want{if counts[s]!=n{ok=false;break}}
		if ok{return};time.Sleep(100*time.Millisecond)
	}
	jobs,_:=st.List(100);t.Fatalf("statuses not reached, jobs=%#v",jobs)
}

func TestFourWorkersRunAndFifthQueues(t *testing.T){
	root:=t.TempDir();st,err:=store.Open(filepath.Join(root,"node.sqlite3"));if err!=nil{t.Fatal(err)};defer st.Close()
	rt:=owruntime.New(st,4,filepath.Join(root,"logs"),"TESTHOST");if err:=rt.Start();err!=nil{t.Fatal(err)};defer rt.Stop()
	cwd:=t.TempDir()
	for i:=1;i<=5;i++{_,err:=st.Submit(model.SubmitRequest{JobID:fmt.Sprintf("OWJ-%d",i),DispatchID:fmt.Sprintf("OWD-%d",i),Machine:"TESTHOST",Command:slowCommand(),CWD:cwd,TimeoutSec:10},"TESTHOST");if err!=nil{t.Fatal(err)}}
	waitStatus(t,st,map[model.Status]int{model.StatusRunning:4,model.StatusQueued:1},5*time.Second)
	waitStatus(t,st,map[model.Status]int{model.StatusSucceeded:5},10*time.Second)
}

func TestSharedResourceLockSerializesJobs(t *testing.T){
	root:=t.TempDir();st,err:=store.Open(filepath.Join(root,"node.sqlite3"));if err!=nil{t.Fatal(err)};defer st.Close()
	rt:=owruntime.New(st,2,filepath.Join(root,"logs"),"TESTHOST");if err:=rt.Start();err!=nil{t.Fatal(err)};defer rt.Stop()
	cwd:=t.TempDir();lock:=[]string{"workspace:"+cwd}
	for i:=1;i<=2;i++{_,err:=st.Submit(model.SubmitRequest{JobID:fmt.Sprintf("LOCK-%d",i),DispatchID:fmt.Sprintf("LOCK-D-%d",i),Machine:"TESTHOST",Command:slowCommand(),CWD:cwd,TimeoutSec:10,Locks:lock},"TESTHOST");if err!=nil{t.Fatal(err)}}
	waitStatus(t,st,map[model.Status]int{model.StatusRunning:1,model.StatusQueued:1},5*time.Second)
	waitStatus(t,st,map[model.Status]int{model.StatusSucceeded:2},10*time.Second)
}

func TestCancelQueuedJob(t *testing.T){
	root:=t.TempDir();st,err:=store.Open(filepath.Join(root,"node.sqlite3"));if err!=nil{t.Fatal(err)};defer st.Close()
	rt:=owruntime.New(st,1,filepath.Join(root,"logs"),"TESTHOST");if err:=rt.Start();err!=nil{t.Fatal(err)};defer rt.Stop()
	cwd:=t.TempDir()
	_,_=st.Submit(model.SubmitRequest{JobID:"OWJ-A",DispatchID:"OWD-A",Machine:"TESTHOST",Command:slowCommand(),CWD:cwd,TimeoutSec:10},"TESTHOST")
	_,_=st.Submit(model.SubmitRequest{JobID:"OWJ-B",DispatchID:"OWD-B",Machine:"TESTHOST",Command:slowCommand(),CWD:cwd,TimeoutSec:10},"TESTHOST")
	waitStatus(t,st,map[model.Status]int{model.StatusRunning:1,model.StatusQueued:1},5*time.Second)
	if err:=rt.Cancel("OWJ-B");err!=nil{t.Fatal(err)}
	j,err:=st.Get("OWJ-B");if err!=nil{t.Fatal(err)};if j.Status!=model.StatusCancelled{t.Fatalf("expected cancelled, got %s",j.Status)}
}

func TestFailedJobPersistsExplainableExecutionSummary(t *testing.T){
	root:=t.TempDir();st,err:=store.Open(filepath.Join(root,"node.sqlite3"));if err!=nil{t.Fatal(err)};defer st.Close()
	rt:=owruntime.New(st,1,filepath.Join(root,"logs"),"TESTHOST");if err:=rt.Start();err!=nil{t.Fatal(err)};defer rt.Stop()
	cwd:=t.TempDir()
	_,err=st.Submit(model.SubmitRequest{JobID:"FAIL-1",DispatchID:"FAIL-D-1",Machine:"TESTHOST",Command:failingCommand(),CWD:cwd,WorkspaceRoot:cwd,TimeoutSec:10},"TESTHOST");if err!=nil{t.Fatal(err)}
	waitStatus(t,st,map[model.Status]int{model.StatusFailed:1},5*time.Second)
	events,err:=st.Events("FAIL-1",100);if err!=nil{t.Fatal(err)}
	found:=false
	for _,e:=range events{if e.EventType=="execution_summary"{found=true;if !strings.Contains(e.Detail,"\"succeeded\":false"){t.Fatalf("missing succeeded=false: %s",e.Detail)};if !strings.Contains(e.Detail,"boom-detail"){t.Fatalf("missing stderr tail: %s",e.Detail)};if !strings.Contains(e.Detail,"\"next_action\""){t.Fatalf("missing next_action: %s",e.Detail)}}}
	if !found{t.Fatal("execution_summary event not found")}
}
