package runtime

import (
	"bufio"
	"context"
	"errors"
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	gort "runtime"
	"strconv"
	"strings"
	"sync"
	"time"

	"github.com/liuxb99/openworker/go-runtime/internal/locks"
	"github.com/liuxb99/openworker/go-runtime/internal/model"
	"github.com/liuxb99/openworker/go-runtime/internal/store"
	"github.com/liuxb99/openworker/go-runtime/internal/worktree"
)

type Manager struct {
	store *store.Store
	maxWorkers int
	logsDir string
	machine string
	locks *locks.Manager
	mu sync.Mutex
	cancel map[string]context.CancelFunc
	stop chan struct{}
	wg sync.WaitGroup
}

func New(st *store.Store,maxWorkers int,logsDir,machine string)*Manager{if maxWorkers<=0{maxWorkers=4};return &Manager{store:st,maxWorkers:maxWorkers,logsDir:logsDir,machine:machine,locks:locks.New(),cancel:map[string]context.CancelFunc{},stop:make(chan struct{})}}
func (m *Manager) Start()error{if err:=os.MkdirAll(m.logsDir,0o755);err!=nil{return err};_,_=m.store.RecoverStale();for i:=0;i<m.maxWorkers;i++{m.wg.Add(1);go m.worker(i+1)};return nil}
func (m *Manager) Stop(){close(m.stop);m.mu.Lock();for _,c:=range m.cancel{c()};m.mu.Unlock();m.wg.Wait()}

func (m *Manager) worker(slot int){defer m.wg.Done();ticker:=time.NewTicker(300*time.Millisecond);defer ticker.Stop();for{select{case<-m.stop:return;case<-ticker.C:job,err:=m.store.ClaimNext();if err!=nil||job==nil{continue};if !m.locks.TryAcquire(job.JobID,job.Locks){_=m.store.Requeue(job.JobID,"resource lock busy");continue};m.run(slot,*job)}}}
func commandForShell(ctx context.Context,command string)*exec.Cmd{if gort.GOOS=="windows"{return exec.CommandContext(ctx,"cmd.exe","/D","/S","/C",command)};return exec.CommandContext(ctx,"/bin/sh","-c",command)}

func (m *Manager) run(slot int,job model.Job){
	defer m.locks.Release(job.JobID)
	if job.Machine!=""&&job.Machine!="any"&&!strings.EqualFold(job.Machine,m.machine){_=m.store.Finish(job.JobID,model.StatusFailed,-1);return}
	execCWD:=job.CWD
	if job.UseWorktree{
		wt:=worktree.New(job.CWD);path,err:=wt.Ensure(slot,job.WorktreeRef);if err!=nil{_=m.store.Finish(job.JobID,model.StatusFailed,-1);return};execCWD=path
	}
	timeout:=time.Duration(job.TimeoutSec)*time.Second;ctx,cancel:=context.WithTimeout(context.Background(),timeout)
	m.mu.Lock();m.cancel[job.JobID]=cancel;m.mu.Unlock();defer func(){cancel();m.mu.Lock();delete(m.cancel,job.JobID);m.mu.Unlock()}()
	stdoutPath:=filepath.Join(m.logsDir,job.JobID+".stdout.log");stderrPath:=filepath.Join(m.logsDir,job.JobID+".stderr.log")
	stdout,err:=os.Create(stdoutPath);if err!=nil{_=m.store.Finish(job.JobID,model.StatusFailed,-1);return};defer stdout.Close();stderr,err:=os.Create(stderrPath);if err!=nil{_=m.store.Finish(job.JobID,model.StatusFailed,-1);return};defer stderr.Close()
	cmd:=commandForShell(ctx,job.Command);cmd.Dir=execCWD;cmd.Stdout=stdout;cmd.Stderr=stderr;cmd.Env=os.Environ();for k,v:=range job.Env{cmd.Env=append(cmd.Env,k+"="+v)}
	cmd.Env=append(cmd.Env,"OPENWORKER_JOB_ID="+job.JobID,"OPENWORKER_AGENT_SLOT="+strconv.Itoa(slot),"OPENWORKER_MACHINE="+m.machine,"GITHUB_WORKSPACE="+execCWD)
	if job.WorkspaceRoot!=""{cmd.Env=append(cmd.Env,"OPENWORKER_WORKSPACE="+job.WorkspaceRoot)}
	if err:=cmd.Start();err!=nil{_=m.store.Finish(job.JobID,model.StatusFailed,-1);return};_=m.store.MarkRunning(job.JobID,cmd.Process.Pid,stdoutPath,stderrPath)
	done:=make(chan error,1);go func(){done<-cmd.Wait()}();hb:=time.NewTicker(2*time.Second);defer hb.Stop()
	for{select{
	case err:=<-done:
		exit:=0;status:=model.StatusSucceeded;if err!=nil{status=model.StatusFailed;if ee:=new(exec.ExitError);errors.As(err,&ee){exit=ee.ExitCode()}else{exit=-1}};if ctx.Err()==context.DeadlineExceeded{status=model.StatusTimedOut;exit=-1};if ctx.Err()==context.Canceled{cur,_:=m.store.Get(job.JobID);if cur.Status==model.StatusCancelled{status=model.StatusCancelled}};_=m.store.Finish(job.JobID,status,exit);return
	case<-hb.C:_=m.store.Heartbeat(job.JobID)
	case<-ctx.Done():killProcessTree(cmd.Process.Pid)
	}}
}
func killProcessTree(pid int){if pid<=0{return};if gort.GOOS=="windows"{_=exec.Command("taskkill","/PID",strconv.Itoa(pid),"/T","/F").Run();return};if p,err:=os.FindProcess(pid);err==nil{_=p.Kill()}}
func (m *Manager) Cancel(jobID string)error{j,err:=m.store.Get(jobID);if err!=nil{return err};if j.Status==model.StatusSucceeded||j.Status==model.StatusFailed||j.Status==model.StatusTimedOut||j.Status==model.StatusCancelled{return nil};_=m.store.MarkCancelled(jobID);m.mu.Lock();cancel:=m.cancel[jobID];m.mu.Unlock();if cancel!=nil{cancel();if j.PID>0{killProcessTree(j.PID)}};m.locks.Release(jobID);return nil}
func (m *Manager) DrainQueued()([]string,error){return m.store.DrainQueued()}
func (m *Manager) NodeStatus()map[string]any{jobs,_:=m.store.List(1000);busy,queued:=0,0;for _,j:=range jobs{if j.Status==model.StatusRunning||j.Status==model.StatusStarting{busy++};if j.Status==model.StatusQueued{queued++}};return map[string]any{"machine":m.machine,"online":true,"max_workers":m.maxWorkers,"busy_workers":busy,"free_workers":max(0,m.maxWorkers-busy),"queued_jobs":queued,"resource_locks":m.locks.Snapshot(),"time":time.Now().UTC()}}
func ReadLastLines(path string,n int)([]string,error){f,err:=os.Open(path);if err!=nil{return nil,err};defer f.Close();s:=bufio.NewScanner(f);lines:=[]string{};for s.Scan(){lines=append(lines,s.Text());if len(lines)>n{lines=lines[1:]}};return lines,s.Err()}
func ValidateCWD(path string)error{if path==""{return fmt.Errorf("cwd required")};st,err:=os.Stat(path);if err!=nil{return err};if !st.IsDir(){return fmt.Errorf("cwd is not a directory: %s",path)};return nil}
