package controlcli

import (
    "bytes"
    "encoding/json"
    "flag"
    "fmt"
    "io"
    "net/http"
    "net/url"
    "os"
    "path/filepath"
    "strings"
    "time"
)

const DefaultServer = "http://127.0.0.1:8848"

type client struct { base string; http *http.Client }
type caseCfg struct { CaseID, Machine, Workspace, OpenWorkerRoot, Manifest, Spec string }

func Main(program string) int { return Run(program, os.Args[1:], os.Stdout, os.Stderr) }

func Run(program string, args []string, stdout, stderr io.Writer) int {
    fs:=flag.NewFlagSet(program,flag.ContinueOnError);fs.SetOutput(stderr)
    server:=fs.String("server",DefaultServer,"localhost go-tool supervisor URL")
    if err:=fs.Parse(args);err!=nil{return 2}
    if err:=validateServer(*server);err!=nil{fmt.Fprintln(stderr,"OPENWORKER_FAIL:",err);return 1}
    a:=fs.Args();if len(a)<2{usage(stderr,program);return 2}
    c:=client{strings.TrimRight(*server,"/"),&http.Client{Timeout:60*time.Second}}
    var out any;var err error
    switch a[0]+" "+a[1] {
    case "supervisor status":
        if len(a)!=2{return usageCode(stderr,program)}
        m,e:=localMachine();if e!=nil{err=e;break}
        out,err=c.get("/api/execution/local-supervisor/status?machine="+url.QueryEscape(m)+"&limit=200")
    case "case status":
        if len(a)!=3{return usageCode(stderr,program)}
        var cfg caseCfg;cfg,err=caseConfig(a[2]);if err!=nil{break};if err=requireLocalMachine(cfg.Machine);err!=nil{break};out,err=c.caseStatus(cfg)
    case "case bootstrap":
        if len(a)!=3{return usageCode(stderr,program)}
        var cfg caseCfg;cfg,err=caseConfig(a[2]);if err!=nil{break};if err=requireLocalMachine(cfg.Machine);err!=nil{break};if err=c.requireOperational(cfg.Machine);err!=nil{break};out,err=c.post("/api/openworker/case/bootstrap",cfg.payload())
    case "case continue":
        if len(a)!=3{return usageCode(stderr,program)}
        var cfg caseCfg;cfg,err=caseConfig(a[2]);if err!=nil{break};if err=requireLocalMachine(cfg.Machine);err!=nil{break};if err=c.requireOperational(cfg.Machine);err!=nil{break};out,err=c.post("/api/openworker/case/dispatch",cfg.payload())
    case "queue clear":
        m,e:=localMachine();if e!=nil{err=e;break};if len(a)==3{m=strings.TrimSpace(a[2])}else if len(a)!=2{return usageCode(stderr,program)};if err=requireLocalMachine(m);err!=nil{break};out,err=c.post("/api/execution/local-work/clear",map[string]any{"assigned_host":m})
    default:
        return usageCode(stderr,program)
    }
    if err!=nil{fmt.Fprintln(stderr,"OPENWORKER_FAIL:",err);return 1}
    enc:=json.NewEncoder(stdout);enc.SetEscapeHTML(false);enc.SetIndent("","  ");if err:=enc.Encode(out);err!=nil{fmt.Fprintln(stderr,"OPENWORKER_FAIL:",err);return 1};return 0
}

func(c client)caseStatus(cfg caseCfg)(any,error){return c.get("/api/openworker/case/status?case_id="+url.QueryEscape(cfg.CaseID)+"&machine="+url.QueryEscape(cfg.Machine)+"&workspace_root="+url.QueryEscape(cfg.Workspace))}
func caseConfig(id string)(caseCfg,error){id=strings.TrimSpace(id);if id!="0005"{return caseCfg{},fmt.Errorf("unsupported case %q; fail-closed",id)};root:=strings.TrimSpace(os.Getenv("OPENWORKER_ROOT"));if root==""{root=discoverRoot()};if root==""{return caseCfg{},fmt.Errorf("OpenWorker checkout not found")};return caseCfg{"0005","DESKTOP-ODAQN0D",`D:\AI-Work\jobs\0005-SNOW-WHITE`,root,filepath.Join(root,"case-worklists","0005.json"),filepath.Join(root,"case-specs","0005.json")},nil}
func(c caseCfg)payload()map[string]any{return map[string]any{"case_id":c.CaseID,"machine":c.Machine,"workspace_root":c.Workspace,"openworker_root":c.OpenWorkerRoot,"manifest_path":c.Manifest,"spec_path":c.Spec,"env":map[string]string{"GTR_WORK_QUEUE_URL":DefaultServer,"GTR_LOCAL_WORKERS":"4","OPENWORKER_ROOT":c.OpenWorkerRoot}}}
func(c client)requireOperational(machine string)error{v,e:=c.get("/api/execution/local-supervisor/status?machine="+url.QueryEscape(machine)+"&limit=200");if e!=nil{return e};m,ok:=v.(map[string]any);if !ok{return fmt.Errorf("invalid supervisor status")};if fmt.Sprint(m["status"])!="OPERATIONAL"{return fmt.Errorf("local supervisor is not OPERATIONAL")};if b,_:=m["operational"].(bool);!b{return fmt.Errorf("local supervisor operational=false")};if fmt.Sprint(m["route_label"])!="LOCAL_SUPERVISOR"{return fmt.Errorf("unexpected supervisor route")};if b,_:=m["github_action_used_for_business_execution"].(bool);b{return fmt.Errorf("GitHub business execution forbidden")};return nil}
func(c client)get(p string)(any,error){return c.do(http.MethodGet,p,nil)}
func(c client)post(p string,v any)(any,error){b,e:=json.Marshal(v);if e!=nil{return nil,e};return c.do(http.MethodPost,p,b)}
func(c client)do(method,p string,b []byte)(any,error){var r io.Reader;if b!=nil{r=bytes.NewReader(b)};req,e:=http.NewRequest(method,c.base+p,r);if e!=nil{return nil,e};if b!=nil{req.Header.Set("Content-Type","application/json")};resp,e:=c.http.Do(req);if e!=nil{return nil,e};defer resp.Body.Close();data,e:=io.ReadAll(io.LimitReader(resp.Body,16<<20));if e!=nil{return nil,e};if resp.StatusCode/100!=2{return nil,fmt.Errorf("HTTP %d: %s",resp.StatusCode,strings.TrimSpace(string(data)))};var out any;if e=json.Unmarshal(data,&out);e!=nil{return nil,e};return out,nil}
func validateServer(raw string)error{u,e:=url.Parse(strings.TrimSpace(raw));if e!=nil{return e};h:=strings.ToLower(u.Hostname());if u.Scheme!="http"||(h!="127.0.0.1"&&h!="localhost"&&h!="::1")||u.Port()!="8848"||(u.Path!=""&&u.Path!="/"){return fmt.Errorf("server must be http localhost:8848 without path")};return nil}
func localMachine()(string,error){h,e:=os.Hostname();return strings.TrimSpace(h),e}
func requireLocalMachine(w string)error{a,e:=localMachine();if e!=nil{return e};if !strings.EqualFold(a,strings.TrimSpace(w)){return fmt.Errorf("machine mismatch local=%q expected=%q",a,w)};return nil}
func discoverRoot()string{for _,p:=range[]string{`C:\github-runners\openworker\_work\openworker\openworker`,`D:\AI\openworker`,`D:\AIWork\openworker`,`D:\PyWork\openworker`}{if st,e:=os.Stat(filepath.Join(p,"case-specs","0005.json"));e==nil&&!st.IsDir(){return p}};return ""}
func usageCode(w io.Writer,p string)int{usage(w,p);return 2}
func usage(w io.Writer,p string){fmt.Fprintf(w,"usage: %s supervisor status | case bootstrap 0005 | case status 0005 | case continue 0005 | queue clear [MACHINE]\n",p)}
