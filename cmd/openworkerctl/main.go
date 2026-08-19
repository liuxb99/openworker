package main

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

const defaultServer = "http://127.0.0.1:8848"

type client struct { base string; http *http.Client }

func main() {
    server := flag.String("server", defaultServer, "local go-tool supervisor URL (localhost only)")
    flag.Parse()
    if err := validateServer(*server); err != nil { fatal(err) }
    args := flag.Args()
    if len(args) < 2 { usage() }
    c := client{base: strings.TrimRight(*server, "/"), http: &http.Client{Timeout: 60 * time.Second}}
    var out any
    var err error
    switch args[0] + " " + args[1] {
    case "supervisor status":
        machine := localMachine()
        out, err = c.get("/api/execution/local-supervisor/status?machine=" + url.QueryEscape(machine) + "&limit=200")
    case "case status":
        if len(args) != 3 { usage() }
        cfg, e := caseConfig(args[2]); if e != nil { fatal(e) }
        if e = requireLocalMachine(cfg.Machine); e != nil { fatal(e) }
        out, err = c.get("/api/openworker/case/status?case_id="+url.QueryEscape(cfg.CaseID)+"&machine="+url.QueryEscape(cfg.Machine)+"&workspace_root="+url.QueryEscape(cfg.Workspace))
    case "case continue":
        if len(args) != 3 { usage() }
        cfg, e := caseConfig(args[2]); if e != nil { fatal(e) }
        if e = requireLocalMachine(cfg.Machine); e != nil { fatal(e) }
        if e = c.requireOperational(cfg.Machine); e != nil { fatal(e) }
        out, err = c.post("/api/openworker/case/dispatch", cfg.controlPayload())
    case "queue clear":
        machine := localMachine()
        if len(args) == 3 { machine = strings.TrimSpace(args[2]) } else if len(args) != 2 { usage() }
        if e := requireLocalMachine(machine); e != nil { fatal(e) }
        out, err = c.post("/api/execution/local-work/clear", map[string]any{"assigned_host": machine})
    default:
        usage()
    }
    if err != nil { fatal(err) }
    enc := json.NewEncoder(os.Stdout); enc.SetEscapeHTML(false); enc.SetIndent("", "  ")
    if err := enc.Encode(out); err != nil { fatal(err) }
}

type caseCfg struct { CaseID, Machine, Workspace, OpenWorkerRoot, Controller, Manifest, Spec, Python string }

func caseConfig(id string) (caseCfg, error) {
    id = strings.TrimSpace(id)
    if id != "0005" { return caseCfg{}, fmt.Errorf("unsupported case %q; openworkerctl is fail-closed", id) }
    root := strings.TrimSpace(os.Getenv("OPENWORKER_ROOT")); if root == "" { root = discoverRoot() }
    if root == "" { return caseCfg{}, fmt.Errorf("OPENWORKER_ROOT is not configured and checkout was not discovered") }
    py := strings.TrimSpace(os.Getenv("OPENWORKER_PYTHON")); if py == "" { py = discoverPython() }
    if py == "" { return caseCfg{}, fmt.Errorf("Python executable not found") }
    return caseCfg{CaseID:"0005", Machine:"DESKTOP-ODAQN0D", Workspace:`D:\AI-Work\jobs\0005-SNOW-WHITE`, OpenWorkerRoot:root, Controller:"coworker.case0005_verified_local_controller", Manifest:filepath.Join(root,"case-worklists","0005.json"), Spec:filepath.Join(root,"case-specs","0005.json"), Python:py}, nil
}

func (c caseCfg) controlPayload() map[string]any { return map[string]any{
    "case_id":c.CaseID,"machine":c.Machine,"workspace_root":c.Workspace,"openworker_root":c.OpenWorkerRoot,"controller_module":c.Controller,"manifest_path":c.Manifest,"spec_path":c.Spec,"python_exe":c.Python,
    "env":map[string]string{"GTR_WORK_QUEUE_URL":defaultServer,"GTR_LOCAL_WORKERS":"4","OPENWORKER_ROOT":c.OpenWorkerRoot},
} }

func (c client) requireOperational(machine string) error {
    v, err := c.get("/api/execution/local-supervisor/status?machine="+url.QueryEscape(machine)+"&limit=200"); if err != nil { return err }
    m, ok := v.(map[string]any); if !ok { return fmt.Errorf("invalid supervisor status response") }
    if strings.TrimSpace(fmt.Sprint(m["status"])) != "OPERATIONAL" { return fmt.Errorf("local supervisor is not OPERATIONAL") }
    if b, _ := m["operational"].(bool); !b { return fmt.Errorf("local supervisor operational=false") }
    if strings.TrimSpace(fmt.Sprint(m["route_label"])) != "LOCAL_SUPERVISOR" { return fmt.Errorf("unexpected supervisor route") }
    if b, _ := m["github_action_used_for_business_execution"].(bool); b { return fmt.Errorf("GitHub business execution is forbidden") }
    return nil
}

func (c client) get(path string) (any,error) { return c.do(http.MethodGet,path,nil) }
func (c client) post(path string, body any) (any,error) { b,e:=json.Marshal(body);if e!=nil{return nil,e};return c.do(http.MethodPost,path,b) }
func (c client) do(method,path string,body []byte)(any,error){
    var r io.Reader; if body != nil { r=bytes.NewReader(body) }
    req,e:=http.NewRequest(method,c.base+path,r);if e!=nil{return nil,e};if body!=nil{req.Header.Set("Content-Type","application/json")}
    resp,e:=c.http.Do(req);if e!=nil{return nil,e};defer resp.Body.Close();data,e:=io.ReadAll(io.LimitReader(resp.Body,16<<20));if e!=nil{return nil,e}
    if resp.StatusCode/100!=2{return nil,fmt.Errorf("HTTP %d: %s",resp.StatusCode,strings.TrimSpace(string(data)))}
    var out any;if e:=json.Unmarshal(data,&out);e!=nil{return nil,fmt.Errorf("invalid JSON response: %w",e)};return out,nil
}

func validateServer(raw string) error { u,e:=url.Parse(strings.TrimSpace(raw));if e!=nil{return e};if u.Scheme!="http"{return fmt.Errorf("server must use http localhost")};h:=strings.ToLower(u.Hostname());if h!="127.0.0.1"&&h!="localhost"&&h!="::1"{return fmt.Errorf("server must be localhost; got %q",u.Hostname())};if u.Port()!="8848"{return fmt.Errorf("server port must be 8848")};if u.Path!=""&&u.Path!="/"{return fmt.Errorf("server must not contain a path")};return nil }
func localMachine() string { h,e:=os.Hostname();if e!=nil{fatal(e)};return strings.TrimSpace(h) }
func requireLocalMachine(expected string) error { actual:=localMachine();if !strings.EqualFold(actual,strings.TrimSpace(expected)){return fmt.Errorf("machine mismatch: local=%q expected=%q",actual,expected)};return nil }
func discoverRoot() string { for _,p:=range []string{`C:\github-runners\openworker\_work\openworker\openworker`,`D:\AI\openworker`,`D:\AIWork\openworker`,`D:\PyWork\openworker`}{if st,e:=os.Stat(filepath.Join(p,"case-specs","0005.json"));e==nil&&!st.IsDir(){if a,e:=filepath.Abs(p);e==nil{return a}}};return "" }
func discoverPython() string { for _,p:=range []string{`C:\Python314\python.exe`,`C:\Python313\python.exe`,`C:\Python312\python.exe`,`C:\Python311\python.exe`,`C:\Python310\python.exe`}{if st,e:=os.Stat(p);e==nil&&!st.IsDir(){return p}};return "" }
func usage(){fmt.Fprintln(os.Stderr,"usage: openworkerctl [--server http://127.0.0.1:8848] supervisor status | case status 0005 | case continue 0005 | queue clear [MACHINE]");os.Exit(2)}
func fatal(err error){fmt.Fprintln(os.Stderr,"OPENWORKERCTL_FAIL:",err);os.Exit(1)}
