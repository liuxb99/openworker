package api

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"

	"github.com/liuxb99/openworker/go-runtime/internal/buildinfo"
	"github.com/liuxb99/openworker/go-runtime/internal/model"
	owruntime "github.com/liuxb99/openworker/go-runtime/internal/runtime"
	"github.com/liuxb99/openworker/go-runtime/internal/store"
)

type Server struct{store *store.Store;runtime *owruntime.Manager;machine string;mux *http.ServeMux}
func New(st *store.Store,rt *owruntime.Manager,machine string)*Server{s:=&Server{store:st,runtime:rt,machine:machine,mux:http.NewServeMux()};s.routes();return s}
func(s *Server)Handler()http.Handler{return s.mux}
func writeJSON(w http.ResponseWriter,status int,v any){w.Header().Set("Content-Type","application/json");w.WriteHeader(status);_=json.NewEncoder(w).Encode(v)}
func writeErr(w http.ResponseWriter,status int,e error){writeJSON(w,status,map[string]any{"ok":false,"error":e.Error()})}
func(s *Server)routes(){
	s.mux.HandleFunc("GET /healthz",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,map[string]any{"ok":true,"machine":s.machine,"build":buildinfo.Snapshot()})})
	s.mux.HandleFunc("GET /v1/node/info",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,map[string]any{"machine":s.machine,"build":buildinfo.Snapshot()})})
	s.mux.HandleFunc("GET /v1/node/status",func(w http.ResponseWriter,r *http.Request){v:=s.runtime.NodeStatus();v["build"]=buildinfo.Snapshot();writeJSON(w,200,v)})
	s.mux.HandleFunc("POST /v1/jobs",s.submit);s.mux.HandleFunc("GET /v1/jobs",s.list);s.mux.HandleFunc("GET /v1/jobs/{jobID}",s.get)
	s.mux.HandleFunc("GET /v1/jobs/{jobID}/events",s.events)
	s.mux.HandleFunc("POST /v1/jobs/{jobID}/cancel",s.cancel);s.mux.HandleFunc("POST /v1/jobs/{jobID}/retry",s.retry);s.mux.HandleFunc("POST /v1/queue/drain",s.drain)
}
func(s *Server)submit(w http.ResponseWriter,r *http.Request){var req model.SubmitRequest;d:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20));d.DisallowUnknownFields();if e:=d.Decode(&req);e!=nil{writeErr(w,400,e);return};if e:=owruntime.ValidateCWD(req.CWD);e!=nil{writeErr(w,400,e);return};ack,e:=s.store.Submit(req,s.machine);if e!=nil{writeErr(w,409,e);return};writeJSON(w,202,ack)}
func(s *Server)list(w http.ResponseWriter,r *http.Request){limit:=100;if v:=r.URL.Query().Get("limit");v!=""{if n,e:=strconv.Atoi(v);e==nil{limit=n}};jobs,e:=s.store.List(limit);if e!=nil{writeErr(w,500,e);return};writeJSON(w,200,map[string]any{"jobs":jobs})}
func(s *Server)get(w http.ResponseWriter,r *http.Request){j,e:=s.store.Get(r.PathValue("jobID"));if e!=nil{writeErr(w,404,e);return};writeJSON(w,200,j)}
func(s *Server)events(w http.ResponseWriter,r *http.Request){limit:=100;if v:=r.URL.Query().Get("limit");v!=""{if n,e:=strconv.Atoi(v);e==nil{limit=n}};events,e:=s.store.Events(r.PathValue("jobID"),limit);if e!=nil{writeErr(w,500,e);return};writeJSON(w,200,map[string]any{"job_id":r.PathValue("jobID"),"events":events})}
func(s *Server)cancel(w http.ResponseWriter,r *http.Request){id:=r.PathValue("jobID");if e:=s.runtime.Cancel(id);e!=nil{writeErr(w,404,e);return};j,_:=s.store.Get(id);writeJSON(w,200,j)}
func(s *Server)retry(w http.ResponseWriter,r *http.Request){id:=r.PathValue("jobID");if e:=s.runtime.Retry(id);e!=nil{writeErr(w,409,e);return};j,_:=s.store.Get(id);writeJSON(w,202,j)}
func(s *Server)drain(w http.ResponseWriter,r *http.Request){mode:=strings.ToLower(r.URL.Query().Get("mode"));if mode==""{mode="queued"};var ids []string;var e error;switch mode{case"queued":ids,e=s.runtime.DrainQueued();case"all":ids,e=s.runtime.DrainAll();default:e=errors.New("mode must be queued or all")};if e!=nil{writeErr(w,500,e);return};writeJSON(w,200,map[string]any{"ok":true,"mode":mode,"drained_job_ids":ids,"count":len(ids)})}
