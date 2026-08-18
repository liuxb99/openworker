"""Thin Python control-plane adapter for the local OpenWorker Go execution node and cluster."""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any
import httpx

@dataclass(slots=True)
class OpenWorkerNodeClient:
    base_url: str = "http://127.0.0.1:8787"
    timeout: float = 10.0
    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        with httpx.Client(base_url=self.base_url.rstrip("/"), timeout=self.timeout) as client:
            response=client.request(method,path,**kwargs);response.raise_for_status();return response.json()
    def node_status(self)->dict[str,Any]: return self._request("GET","/v1/node/status")
    def case_bootstrap(self,payload:dict[str,Any])->dict[str,Any]: return self._request("POST","/v1/cases/bootstrap",json=payload)
    def submit(self,payload:dict[str,Any])->dict[str,Any]: return self._request("POST","/v1/jobs",json=payload)
    def jobs(self,limit:int=100)->dict[str,Any]: return self._request("GET","/v1/jobs",params={"limit":limit})
    def job_status(self,job_id:str)->dict[str,Any]: return self._request("GET",f"/v1/jobs/{job_id}")
    def job_progress(self,job_id:str)->dict[str,Any]: return self._request("GET",f"/v1/jobs/{job_id}/progress")
    def update_job_progress(self,job_id:str,payload:dict[str,Any])->dict[str,Any]: return self._request("POST",f"/v1/jobs/{job_id}/progress",json=payload)
    def cancel(self,job_id:str)->dict[str,Any]: return self._request("POST",f"/v1/jobs/{job_id}/cancel")
    def retry(self,job_id:str)->dict[str,Any]: return self._request("POST",f"/v1/jobs/{job_id}/retry")
    def drain(self,mode:str="queued")->dict[str,Any]:
        if mode not in {"queued","all"}: raise ValueError("mode must be queued or all")
        return self._request("POST","/v1/queue/drain",params={"mode":mode})
    def cluster_status(self)->dict[str,Any]: return self._request("GET","/v1/cluster/status")
    def cluster_capabilities(self)->dict[str,Any]: return self._request("GET","/v1/cluster/capabilities")
    def cluster_jobs(self,limit:int=100)->dict[str,Any]: return self._request("GET","/v1/cluster/jobs",params={"limit":limit})
    def cluster_agents(self)->dict[str,Any]: return self._request("GET","/v1/cluster/agents")
    def cluster_job_status(self,job_id:str)->dict[str,Any]: return self._request("GET",f"/v1/cluster/jobs/{job_id}")
    def cluster_job_cancel(self,job_id:str)->dict[str,Any]: return self._request("POST",f"/v1/cluster/jobs/{job_id}/cancel")
    def cluster_job_retry(self,job_id:str)->dict[str,Any]: return self._request("POST",f"/v1/cluster/jobs/{job_id}/retry")
    def cluster_drain(self,machine:str,mode:str="queued")->dict[str,Any]:
        if not machine: raise ValueError("machine required")
        if mode not in {"queued","all"}: raise ValueError("mode must be queued or all")
        return self._request("POST","/v1/cluster/queue/drain",params={"machine":machine,"mode":mode})
    def cluster_route(self,machine:str="any",capabilities:list[str]|None=None)->dict[str,Any]:
        return self._request("GET","/v1/cluster/route",params={"machine":machine,"capabilities":",".join(capabilities or [])})
    def cluster_submit(self,job:dict[str,Any],required_capabilities:list[str]|None=None)->dict[str,Any]:
        return self._request("POST","/v1/cluster/jobs",json={"job":job,"required_capabilities":required_capabilities or []})
    def cluster_dispatches(self,limit:int=100)->dict[str,Any]: return self._request("GET","/v1/cluster/dispatches",params={"limit":limit})
    def cluster_dispatch(self,job_id:str)->dict[str,Any]: return self._request("GET",f"/v1/cluster/dispatches/{job_id}")
    def cluster_control_events(self,job_id:str|None=None,limit:int=100)->dict[str,Any]:
        p={"limit":limit}
        if job_id: p["job_id"]=job_id
        return self._request("GET","/v1/cluster/control-events",params=p)
    def cluster_endpoints(self)->dict[str,Any]: return self._request("GET","/v1/cluster/endpoints")
    def cluster_connectivity(self,limit:int=200)->dict[str,Any]: return self._request("GET","/v1/cluster/connectivity",params={"limit":limit})
    def supervisor_session(self,supervisor_id:str,session_id:str,model:str,current_goal:str="")->dict[str,Any]:
        return self._request("POST","/v1/supervisor/session",json={"supervisor_id":supervisor_id,"session_id":session_id,"model":model,"current_goal":current_goal})
    def supervisor_heartbeat(self,supervisor_id:str,session_id:str,current_goal:str="")->dict[str,Any]:
        return self._request("POST","/v1/supervisor/heartbeat",json={"supervisor_id":supervisor_id,"session_id":session_id,"current_goal":current_goal})
    def supervisor_snapshot(self,supervisor_id:str)->dict[str,Any]: return self._request("GET","/v1/supervisor/snapshot",params={"supervisor_id":supervisor_id})
    def supervisor_jobs(self,supervisor_id:str)->dict[str,Any]: return self._request("GET","/v1/supervisor/jobs",params={"supervisor_id":supervisor_id})
    def supervisor_attention(self,supervisor_id:str)->dict[str,Any]: return self._request("GET","/v1/supervisor/attention",params={"supervisor_id":supervisor_id})
    def supervisor_recover(self,supervisor_id:str,session_id:str="")->dict[str,Any]: return self._request("POST","/v1/supervisor/recover",json={"supervisor_id":supervisor_id,"session_id":session_id})
    def supervisor_decision(self,payload:dict[str,Any])->dict[str,Any]: return self._request("POST","/v1/supervisor/decision",json=payload)
    def supervisor_decisions(self,supervisor_id:str,limit:int=100)->dict[str,Any]: return self._request("GET","/v1/supervisor/decisions",params={"supervisor_id":supervisor_id,"limit":limit})
