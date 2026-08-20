package api

import "net/http"

func (s *Server) dashboard(w http.ResponseWriter, r *http.Request) {
	w.Header().Set("Content-Type", "text/html; charset=utf-8")
	_, _ = w.Write([]byte(openworkerDashboardHTML))
}

const openworkerDashboardHTML = `<!doctype html>
<html lang="zh-Hant">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>OpenWorker 工作總控</title>
<style>
body{font-family:system-ui,-apple-system,"Segoe UI",sans-serif;margin:0;background:#111827;color:#e5e7eb}header{padding:18px 22px;background:#0b1220;position:sticky;top:0}h1{font-size:20px;margin:0 0 10px}.bar,.actions{display:flex;gap:8px;flex-wrap:wrap}input,select,button{background:#1f2937;color:#e5e7eb;border:1px solid #374151;border-radius:7px;padding:8px}button{cursor:pointer}.danger{border-color:#7f1d1d}.retry{border-color:#92400e}main{padding:18px}.meta{color:#9ca3af;margin-bottom:12px}.grid{display:grid;grid-template-columns:minmax(0,1.5fr) minmax(320px,1fr);gap:14px}.panel{background:#172033;border:1px solid #27344a;border-radius:10px;overflow:hidden}.detail-head{padding:10px 12px;border-bottom:1px solid #27344a}table{width:100%;border-collapse:collapse;font-size:13px}th,td{padding:9px;border-bottom:1px solid #27344a;text-align:left;vertical-align:top}tr:hover{background:#1d2940}.status{font-weight:700}.running,.starting{color:#fbbf24}.succeeded{color:#34d399}.failed,.timed_out{color:#fb7185}.queued_local,.accepted{color:#60a5fa}pre{white-space:pre-wrap;word-break:break-word;margin:0;padding:12px;font-size:12px;max-height:72vh;overflow:auto}.small{font-size:12px;color:#9ca3af}@media(max-width:900px){.grid{grid-template-columns:1fr}}
</style></head>
<body><header><h1>OpenWorker 工作總控</h1><div class="bar"><input id="filter" placeholder="篩選 case / job / dispatch / command" value="case0005"><select id="status"><option value="">全部狀態</option><option>queued_local</option><option>starting</option><option>running</option><option>succeeded</option><option>failed</option><option>timed_out</option><option>cancelled</option></select><button onclick="loadJobs()">重新整理</button><label class="small"><input type="checkbox" id="auto" checked> 3 秒自動更新</label></div></header>
<main><div class="meta" id="meta">載入中…</div><div class="grid"><div class="panel"><table><thead><tr><th>狀態</th><th>Job / Work</th><th>Slot/PID</th><th>時間</th></tr></thead><tbody id="jobs"></tbody></table></div><div class="panel"><div class="detail-head"><div class="actions"><button class="retry" onclick="jobAction('retry')">重試</button><button class="danger" onclick="jobAction('cancel')">取消</button></div></div><pre id="detail">點選左側工作查看完整記錄與 events。</pre></div></div></main>
<script>
let allJobs=[];let selected='';
function esc(s){return String(s??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]))}
function showTime(v){if(!v)return '';try{return new Date(v).toLocaleString()}catch{return v}}
async function loadJobs(){try{const r=await fetch('/v1/jobs?limit=500',{cache:'no-store'});const j=await r.json();allJobs=j.jobs||[];document.getElementById('meta').textContent='OpenWorker durable jobs: '+allJobs.length+' ｜ '+new Date().toLocaleString();render();if(selected)loadDetail(selected)}catch(e){document.getElementById('meta').textContent='讀取失敗: '+e}}
function render(){const q=document.getElementById('filter').value.toLowerCase();const st=document.getElementById('status').value;const rows=allJobs.filter(x=>(!st||x.status===st)&&(!q||JSON.stringify(x).toLowerCase().includes(q)));document.getElementById('jobs').innerHTML=rows.map(x=>'<tr data-job="'+esc(x.job_id)+'"><td class="status '+esc(x.status)+'">'+esc(x.status)+'</td><td><b>'+esc(x.job_id)+'</b><div class="small">'+esc(x.dispatch_id||'')+'</div><div class="small">'+esc(x.command||'')+'</div></td><td>slot '+esc(x.agent_slot||'-')+'<br>pid '+esc(x.pid||'-')+'</td><td>'+esc(showTime(x.started_at||x.accepted_at||x.created_at))+'<br><span class="small">'+esc(showTime(x.finished_at))+'</span></td></tr>').join('')||'<tr><td colspan="4">沒有符合條件的工作</td></tr>';document.querySelectorAll('tr[data-job]').forEach(tr=>tr.onclick=()=>loadDetail(tr.dataset.job))}
async function loadDetail(id){selected=id;try{const [jr,er]=await Promise.all([fetch('/v1/jobs/'+encodeURIComponent(id),{cache:'no-store'}),fetch('/v1/jobs/'+encodeURIComponent(id)+'/events?limit=500',{cache:'no-store'})]);const job=await jr.json();const events=await er.json();document.getElementById('detail').textContent=JSON.stringify({job,events:events.events||[]},null,2)}catch(e){document.getElementById('detail').textContent='讀取工作明細失敗: '+e}}
async function jobAction(kind){if(!selected){alert('請先選一張工作');return}if(kind==='cancel'&&!confirm('確定取消 '+selected+'？'))return;try{const r=await fetch('/v1/jobs/'+encodeURIComponent(selected)+'/'+kind,{method:'POST'});const body=await r.text();if(!r.ok)throw new Error('HTTP '+r.status+' '+body);await loadJobs();await loadDetail(selected)}catch(e){alert(kind+' 失敗: '+e)}}
document.getElementById('filter').addEventListener('input',render);document.getElementById('status').addEventListener('change',render);setInterval(()=>{if(document.getElementById('auto').checked)loadJobs()},3000);loadJobs();
</script></body></html>`
