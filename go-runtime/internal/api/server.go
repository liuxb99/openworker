package api

import (
	"encoding/json"
	"errors"
	"net/http"
	"strconv"
	"strings"

	"github.com/liuxb99/openworker/go-runtime/internal/model"
	owruntime "github.com/liuxb99/openworker/go-runtime/internal/runtime"
	"github.com/liuxb99/openworker/go-runtime/internal/store"
)

type Server struct {
	store *store.Store
	runtime *owruntime.Manager
	machine string
	mux *http.ServeMux
}

func New(st *store.Store, rt *owruntime.Manager, machine string) *Server {
	s:=&Server{store:st,runtime:rt,machine:machine,mux:http.NewServeMux()}
	s.routes();return s
}

func (s *Server) Handler() http.Handler { return s.mux }

func writeJSON(w http.ResponseWriter,status int,v any){w.Header().Set("Content-Type","application/json");w.WriteHeader(status);_ = json.NewEncoder(w).Encode(v)}
func writeErr(w http.ResponseWriter,status int,err error){writeJSON(w,status,map[string]any{"ok":false,"error":err.Error()})}

func (s *Server) routes(){
	s.mux.HandleFunc("GET /healthz",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,map[string]any{"ok":true,"machine":s.machine})})
	s.mux.HandleFunc("GET /v1/node/status",func(w http.ResponseWriter,r *http.Request){writeJSON(w,200,s.runtime.NodeStatus())})
	s.mux.HandleFunc("POST /v1/jobs",s.submit)
	s.mux.HandleFunc("GET /v1/jobs",s.list)
	s.mux.HandleFunc("GET /v1/jobs/{jobID}",s.get)
	s.mux.HandleFunc("POST /v1/jobs/{jobID}/cancel",s.cancel)
	s.mux.HandleFunc("POST /v1/queue/drain",s.drain)
}

func (s *Server) submit(w http.ResponseWriter,r *http.Request){
	var req model.SubmitRequest
	dec:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20));dec.DisallowUnknownFields();if err:=dec.Decode(&req);err!=nil{writeErr(w,400,err);return}
	if err:=owruntime.ValidateCWD(req.CWD);err!=nil{writeErr(w,400,err);return}
	ack,err:=s.store.Submit(req,s.machine);if err!=nil{writeErr(w,409,err);return};writeJSON(w,202,ack)
}

func (s *Server) list(w http.ResponseWriter,r *http.Request){limit:=100;if v:=r.URL.Query().Get("limit");v!=""{if n,err:=strconv.Atoi(v);err==nil{limit=n}};jobs,err:=s.store.List(limit);if err!=nil{writeErr(w,500,err);return};writeJSON(w,200,map[string]any{"jobs":jobs})}
func (s *Server) get(w http.ResponseWriter,r *http.Request){j,err:=s.store.Get(r.PathValue("jobID"));if err!=nil{writeErr(w,404,err);return};writeJSON(w,200,j)}
func (s *Server) cancel(w http.ResponseWriter,r *http.Request){if err:=s.runtime.Cancel(r.PathValue("jobID"));err!=nil{writeErr(w,404,err);return};j,_:=s.store.Get(r.PathValue("jobID"));writeJSON(w,200,j)}

func (s *Server) drain(w http.ResponseWriter,r *http.Request){
	mode:=strings.ToLower(r.URL.Query().Get("mode"));if mode==""{mode="queued"}
	if mode!="queued"{writeErr(w,400,errors.New("P0 only supports mode=queued; drain all is added after running-process receipt coverage"));return}
	ids,err:=s.runtime.DrainQueued();if err!=nil{writeErr(w,500,err);return};writeJSON(w,200,map[string]any{"ok":true,"mode":mode,"drained_job_ids":ids,"count":len(ids)})
}
