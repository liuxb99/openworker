package api

import (
 "database/sql"
 "encoding/json"
 "errors"
 "net/http"
 "strings"
 "time"

 "github.com/liuxb99/openworker/go-runtime/internal/model"
 "github.com/liuxb99/openworker/go-runtime/internal/store"
)

type supervisorSessionRequest struct{SupervisorID string `json:"supervisor_id"`;SessionID string `json:"session_id"`;Model string `json:"model"`;CurrentGoal string `json:"current_goal,omitempty"`}
type supervisorHeartbeatRequest struct{SupervisorID string `json:"supervisor_id"`;SessionID string `json:"session_id"`;CurrentGoal string `json:"current_goal,omitempty"`}
type supervisorDecisionRequest struct{DecisionID string `json:"decision_id"`;SupervisorID string `json:"supervisor_id"`;SessionID string `json:"session_id"`;JobID string `json:"job_id,omitempty"`;DecisionType string `json:"decision_type"`;ReasonCode string `json:"reason_code"`;InputStateHash string `json:"input_state_hash,omitempty"`;Result string `json:"result,omitempty"`}

func(s *Server)supervisorRoutes(){
 s.mux.HandleFunc("POST /v1/supervisor/session",s.supervisorSession)
 s.mux.HandleFunc("POST /v1/supervisor/heartbeat",s.supervisorHeartbeat)
 s.mux.HandleFunc("GET /v1/supervisor/snapshot",s.supervisorSnapshot)
 s.mux.HandleFunc("GET /v1/supervisor/jobs",s.supervisorJobs)
 s.mux.HandleFunc("POST /v1/supervisor/recover",s.supervisorRecover)
 s.mux.HandleFunc("POST /v1/supervisor/decision",s.supervisorDecision)
 s.mux.HandleFunc("GET /v1/supervisor/decisions",s.supervisorDecisions)
}

func(s *Server)supervisorSession(w http.ResponseWriter,r *http.Request){var req supervisorSessionRequest;d:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20));d.DisallowUnknownFields();if err:=d.Decode(&req);err!=nil{writeErr(w,400,err);return};v,err:=s.store.StartSupervisorSession(store.SupervisorSession{SessionID:req.SessionID,SupervisorID:req.SupervisorID,Machine:s.machine,Model:req.Model,State:"active"},req.CurrentGoal);if err!=nil{writeErr(w,409,err);return};writeJSON(w,201,v)}
func(s *Server)supervisorHeartbeat(w http.ResponseWriter,r *http.Request){var req supervisorHeartbeatRequest;if err:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20)).Decode(&req);err!=nil{writeErr(w,400,err);return};if err:=s.store.SupervisorHeartbeat(req.SupervisorID,req.SessionID,req.CurrentGoal);err!=nil{writeErr(w,409,err);return};v,_:=s.store.SupervisorByID(req.SupervisorID);writeJSON(w,200,v)}
func(s *Server)supervisorSnapshot(w http.ResponseWriter,r *http.Request){id:=strings.TrimSpace(r.URL.Query().Get("supervisor_id"));if id==""{writeErr(w,400,errors.New("supervisor_id required"));return};v,err:=s.store.SupervisorSnapshotByID(id);if errors.Is(err,sql.ErrNoRows){writeErr(w,404,err);return};if err!=nil{writeErr(w,500,err);return};writeJSON(w,200,v)}
func(s *Server)supervisorJobs(w http.ResponseWriter,r *http.Request){id:=strings.TrimSpace(r.URL.Query().Get("supervisor_id"));if id==""{writeErr(w,400,errors.New("supervisor_id required"));return};sup,err:=s.store.SupervisorByID(id);if err!=nil{writeErr(w,404,err);return};jobs,err:=s.store.List(1000);if err!=nil{writeErr(w,500,err);return};owned:=[]model.Job{};for _,j:=range jobs{if strings.EqualFold(j.Machine,sup.Machine){owned=append(owned,j)}};writeJSON(w,200,map[string]any{"supervisor_id":id,"machine":sup.Machine,"jobs":owned,"count":len(owned)})}
func(s *Server)supervisorRecover(w http.ResponseWriter,r *http.Request){var req struct{SupervisorID string `json:"supervisor_id"`;SessionID string `json:"session_id"`};if err:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20)).Decode(&req);err!=nil{writeErr(w,400,err);return};sup,err:=s.store.SupervisorByID(req.SupervisorID);if err!=nil{writeErr(w,404,err);return};if req.SessionID!=""&&sup.CurrentSessionID!=req.SessionID{writeErr(w,409,errors.New("session_id is not current supervisor session"));return};jobs,err:=s.store.List(1000);if err!=nil{writeErr(w,500,err);return};snap:=store.SupervisorSnapshot{SupervisorID:sup.SupervisorID,Machine:sup.Machine,CurrentGoal:sup.CurrentGoal,OwnedJobs:[]string{},WatchedJobs:[]string{},BlockedJobs:[]string{},FailedJobs:[]string{},RecentCompletedJobs:[]string{},NextAttention:[]string{},UpdatedAt:time.Now().UTC()};if old,e:=s.store.SupervisorSnapshotByID(req.SupervisorID);e==nil{snap.WatchedJobs=old.WatchedJobs;snap.LastDecision=old.LastDecision}
 for _,j:=range jobs{if !strings.EqualFold(j.Machine,sup.Machine){continue};snap.OwnedJobs=append(snap.OwnedJobs,j.JobID);switch j.Status{case model.StatusFailed,model.StatusTimedOut,model.StatusStale:snap.FailedJobs=append(snap.FailedJobs,j.JobID);snap.NextAttention=append(snap.NextAttention,j.JobID);case model.StatusSucceeded:snap.RecentCompletedJobs=append(snap.RecentCompletedJobs,j.JobID);case model.StatusQueued:if j.AgentSlot==0{snap.BlockedJobs=append(snap.BlockedJobs,j.JobID)}}}
 if len(snap.RecentCompletedJobs)>20{snap.RecentCompletedJobs=snap.RecentCompletedJobs[:20]};decisions,_:=s.store.SupervisorDecisions(req.SupervisorID,1);if len(decisions)>0{snap.LastDecision=decisions[0].DecisionType+":"+decisions[0].ReasonCode};if err:=s.store.SaveSupervisorSnapshot(snap);err!=nil{writeErr(w,500,err);return};writeJSON(w,200,map[string]any{"supervisor":sup,"snapshot":snap,"recovered":true})}
func(s *Server)supervisorDecision(w http.ResponseWriter,r *http.Request){var req supervisorDecisionRequest;d:=json.NewDecoder(http.MaxBytesReader(w,r.Body,1<<20));d.DisallowUnknownFields();if err:=d.Decode(&req);err!=nil{writeErr(w,400,err);return};sup,err:=s.store.SupervisorByID(req.SupervisorID);if err!=nil{writeErr(w,404,err);return};if sup.CurrentSessionID!=req.SessionID{writeErr(w,409,errors.New("decision session is not current supervisor session"));return};v:=store.SupervisorDecision{DecisionID:req.DecisionID,SupervisorID:req.SupervisorID,SessionID:req.SessionID,Machine:s.machine,JobID:req.JobID,DecisionType:req.DecisionType,ReasonCode:req.ReasonCode,InputStateHash:req.InputStateHash,Result:req.Result};if err:=s.store.RecordSupervisorDecision(v);err!=nil{writeErr(w,409,err);return};writeJSON(w,201,v)}
func(s *Server)supervisorDecisions(w http.ResponseWriter,r *http.Request){id:=strings.TrimSpace(r.URL.Query().Get("supervisor_id"));if id==""{writeErr(w,400,errors.New("supervisor_id required"));return};rows,err:=s.store.SupervisorDecisions(id,queryInt(r,"limit",100));if err!=nil{writeErr(w,500,err);return};writeJSON(w,200,map[string]any{"decisions":rows,"count":len(rows)})}
