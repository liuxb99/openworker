package main

import (
	"bytes"
	"encoding/binary"
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
	"unicode/utf16"
)

const defaultServer = "http://127.0.0.1:8848"

type client struct {
	base string
	http *http.Client
}

type caseCfg struct {
	CaseID, Machine, Workspace, OpenWorkerRoot, Controller, Manifest, Spec, Python string
}

func main() {
	server := flag.String("server", defaultServer, "localhost go-tool supervisor URL")
	flag.Parse()
	if err := validateServer(*server); err != nil {
		fatal(err)
	}
	a := flag.Args()
	if len(a) < 2 {
		usage()
	}
	c := client{strings.TrimRight(*server, "/"), &http.Client{Timeout: 60 * time.Second}}
	var out any
	var err error

	switch a[0] + " " + a[1] {
	case "supervisor status":
		if len(a) != 2 { usage() }
		m := localMachine()
		out, err = c.get("/api/execution/local-supervisor/status?machine=" + url.QueryEscape(m) + "&limit=200")
	case "case status":
		if len(a) != 3 { usage() }
		cfg, e := caseConfig(a[2]); if e != nil { fatal(e) }
		if e = requireLocalMachine(cfg.Machine); e != nil { fatal(e) }
		out, err = c.caseStatus(cfg)
	case "case diagnose":
		if len(a) != 3 { usage() }
		cfg, e := caseConfig(a[2]); if e != nil { fatal(e) }
		if e = requireLocalMachine(cfg.Machine); e != nil { fatal(e) }
		out, err = c.caseDiagnose(cfg)
	case "case continue":
		if len(a) != 3 { usage() }
		cfg, e := caseConfig(a[2]); if e != nil { fatal(e) }
		if e = requireLocalMachine(cfg.Machine); e != nil { fatal(e) }
		if e = c.requireOperational(cfg.Machine); e != nil { fatal(e) }
		out, err = c.post("/api/openworker/case/dispatch", cfg.payload())
	case "queue clear":
		m := localMachine()
		if len(a) == 3 { m = strings.TrimSpace(a[2]) } else if len(a) != 2 { usage() }
		if e := requireLocalMachine(m); e != nil { fatal(e) }
		out, err = c.post("/api/execution/local-work/clear", map[string]any{"assigned_host": m})
	default:
		usage()
	}
	if err != nil { fatal(err) }
	enc := json.NewEncoder(os.Stdout)
	enc.SetEscapeHTML(false)
	enc.SetIndent("", "  ")
	if err := enc.Encode(out); err != nil { fatal(err) }
}

func (c client) caseStatus(cfg caseCfg) (any, error) {
	return c.get("/api/openworker/case/status?case_id=" + url.QueryEscape(cfg.CaseID) + "&machine=" + url.QueryEscape(cfg.Machine) + "&workspace_root=" + url.QueryEscape(cfg.Workspace))
}

func (c client) caseDiagnose(cfg caseCfg) (any, error) {
	v, err := c.caseStatus(cfg)
	if err != nil { return nil, err }
	root, ok := v.(map[string]any)
	if !ok { return nil, fmt.Errorf("invalid case status payload") }
	explain, _ := root["latest_job_explain"].(map[string]any)
	job, _ := explain["job"].(map[string]any)
	if job == nil { return nil, fmt.Errorf("latest case job not found") }

	stderrPath := strings.TrimSpace(fmt.Sprint(job["stderr_path"]))
	stdoutPath := strings.TrimSpace(fmt.Sprint(job["stdout_path"]))
	stderrText, stderrErr := readBoundedCaseLog(stderrPath)
	stdoutText, stdoutErr := readBoundedCaseLog(stdoutPath)

	return map[string]any{
		"schema": "openworkerctl.case-diagnose/v1",
		"case_id": cfg.CaseID,
		"machine": cfg.Machine,
		"workspace_root": cfg.Workspace,
		"job_id": job["job_id"],
		"status": job["status"],
		"exit_code": job["exit_code"],
		"started_at": job["started_at"],
		"finished_at": job["finished_at"],
		"stderr_path": stderrPath,
		"stdout_path": stdoutPath,
		"stderr_text": stderrText,
		"stdout_text": stdoutText,
		"stderr_read_error": errorString(stderrErr),
		"stdout_read_error": errorString(stdoutErr),
		"execution_summary": explain["execution_summary"],
		"authority": "openworker-local-durable-ledger+bounded-local-log-read",
		"github_action_used_for_business_execution": false,
		"diagnosed_at": time.Now().UTC().Format(time.RFC3339Nano),
	}, nil
}

func readBoundedCaseLog(path string) (string, error) {
	if path == "" || path == "<nil>" { return "", nil }
	clean, err := filepath.Abs(filepath.Clean(path)); if err != nil { return "", err }
	allowed, err := filepath.Abs(filepath.Join(os.Getenv("ProgramData"), "OpenWorker", "node", "logs")); if err != nil { return "", err }
	rel, err := filepath.Rel(allowed, clean); if err != nil { return "", err }
	if rel == ".." || strings.HasPrefix(rel, ".."+string(os.PathSeparator)) || filepath.IsAbs(rel) {
		return "", fmt.Errorf("log path escapes allowed root: %s", clean)
	}
	f, err := os.Open(clean); if err != nil { return "", err }
	defer f.Close()
	st, err := f.Stat(); if err != nil { return "", err }
	const max = int64(64 << 10)
	start := st.Size() - max
	if start < 0 { start = 0 }
	if _, err := f.Seek(start, io.SeekStart); err != nil { return "", err }
	data, err := io.ReadAll(io.LimitReader(f, max)); if err != nil { return "", err }
	return decodeText(data), nil
}

func decodeText(b []byte) string {
	if len(b) >= 2 && b[0] == 0xff && b[1] == 0xfe { return decodeUTF16(b[2:], binary.LittleEndian) }
	if len(b) >= 2 && b[0] == 0xfe && b[1] == 0xff { return decodeUTF16(b[2:], binary.BigEndian) }
	if bytes.Count(b, []byte{0}) > len(b)/8 {
		return decodeUTF16(b, binary.LittleEndian)
	}
	return strings.ToValidUTF8(string(b), "�")
}

func decodeUTF16(b []byte, order binary.ByteOrder) string {
	if len(b)%2 == 1 { b = b[:len(b)-1] }
	u := make([]uint16, len(b)/2)
	for i := range u { u[i] = order.Uint16(b[i*2:]) }
	return string(utf16.Decode(u))
}

func errorString(err error) string { if err == nil { return "" }; return err.Error() }

func caseConfig(id string) (caseCfg, error) {
	id = strings.TrimSpace(id)
	if id != "0005" { return caseCfg{}, fmt.Errorf("unsupported case %q; fail-closed", id) }
	root := strings.TrimSpace(os.Getenv("OPENWORKER_ROOT")); if root == "" { root = discoverRoot() }
	if root == "" { return caseCfg{}, fmt.Errorf("OpenWorker checkout not found") }
	py := strings.TrimSpace(os.Getenv("OPENWORKER_PYTHON")); if py == "" { py = discoverPython() }
	if py == "" { return caseCfg{}, fmt.Errorf("Python executable not found") }
	return caseCfg{"0005", "DESKTOP-ODAQN0D", `D:\AI-Work\jobs\0005-SNOW-WHITE`, root, "coworker.case0005_verified_local_controller", filepath.Join(root, "case-worklists", "0005.json"), filepath.Join(root, "case-specs", "0005.json"), py}, nil
}

func (c caseCfg) payload() map[string]any {
	return map[string]any{"case_id":c.CaseID,"machine":c.Machine,"workspace_root":c.Workspace,"openworker_root":c.OpenWorkerRoot,"controller_module":c.Controller,"manifest_path":c.Manifest,"spec_path":c.Spec,"python_exe":c.Python,"env":map[string]string{"GTR_WORK_QUEUE_URL":defaultServer,"GTR_LOCAL_WORKERS":"4","OPENWORKER_ROOT":c.OpenWorkerRoot}}
}

func (c client) requireOperational(machine string) error {
	v,e:=c.get("/api/execution/local-supervisor/status?machine="+url.QueryEscape(machine)+"&limit=200"); if e!=nil{return e}
	m,ok:=v.(map[string]any); if !ok{return fmt.Errorf("invalid supervisor status")}
	if fmt.Sprint(m["status"])!="OPERATIONAL"{return fmt.Errorf("local supervisor is not OPERATIONAL")}
	if b,_:=m["operational"].(bool);!b{return fmt.Errorf("local supervisor operational=false")}
	if fmt.Sprint(m["route_label"])!="LOCAL_SUPERVISOR"{return fmt.Errorf("unexpected supervisor route")}
	if b,_:=m["github_action_used_for_business_execution"].(bool);b{return fmt.Errorf("GitHub business execution forbidden")}
	return nil
}
func(c client)get(p string)(any,error){return c.do(http.MethodGet,p,nil)}
func(c client)post(p string,v any)(any,error){b,e:=json.Marshal(v);if e!=nil{return nil,e};return c.do(http.MethodPost,p,b)}
func(c client)do(method,p string,b []byte)(any,error){var r io.Reader;if b!=nil{r=bytes.NewReader(b)};req,e:=http.NewRequest(method,c.base+p,r);if e!=nil{return nil,e};if b!=nil{req.Header.Set("Content-Type","application/json")};resp,e:=c.http.Do(req);if e!=nil{return nil,e};defer resp.Body.Close();data,e:=io.ReadAll(io.LimitReader(resp.Body,16<<20));if e!=nil{return nil,e};if resp.StatusCode/100!=2{return nil,fmt.Errorf("HTTP %d: %s",resp.StatusCode,strings.TrimSpace(string(data)))};var out any;if e=json.Unmarshal(data,&out);e!=nil{return nil,e};return out,nil}
func validateServer(raw string)error{u,e:=url.Parse(strings.TrimSpace(raw));if e!=nil{return e};h:=strings.ToLower(u.Hostname());if u.Scheme!="http"||(h!="127.0.0.1"&&h!="localhost"&&h!="::1")||u.Port()!="8848"||(u.Path!=""&&u.Path!="/"){return fmt.Errorf("server must be http localhost:8848 without path")};return nil}
func localMachine()string{h,e:=os.Hostname();if e!=nil{fatal(e)};return strings.TrimSpace(h)}
func requireLocalMachine(w string)error{a:=localMachine();if !strings.EqualFold(a,strings.TrimSpace(w)){return fmt.Errorf("machine mismatch local=%q expected=%q",a,w)};return nil}
func discoverRoot()string{for _,p:=range[]string{`C:\github-runners\openworker\_work\openworker\openworker`,`D:\AI\openworker`,`D:\AIWork\openworker`,`D:\PyWork\openworker`}{if st,e:=os.Stat(filepath.Join(p,"case-specs","0005.json"));e==nil&&!st.IsDir(){return p}};return ""}
func discoverPython()string{for _,p:=range[]string{`C:\Python314\python.exe`,`C:\Python313\python.exe`,`C:\Python312\python.exe`,`C:\Python311\python.exe`,`C:\Python310\python.exe`}{if st,e:=os.Stat(p);e==nil&&!st.IsDir(){return p}};return ""}
func usage(){fmt.Fprintln(os.Stderr,"usage: openworkerctl supervisor status | case status 0005 | case diagnose 0005 | case continue 0005 | queue clear [MACHINE]");os.Exit(2)}
func fatal(e error){fmt.Fprintln(os.Stderr,"OPENWORKERCTL_FAIL:",e);os.Exit(1)}
