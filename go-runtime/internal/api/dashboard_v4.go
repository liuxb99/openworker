package api

import (
    "net/http"
    "strings"
)

func (s *Server) dashboardV4(w http.ResponseWriter, r *http.Request) {
    w.Header().Set("Content-Type", "text/html; charset=utf-8")
    html := openworkerDashboardV3HTML
    html = strings.Replace(html, "</style>", versionWidgetCSS+"</style>", 1)
    html = strings.Replace(html, "<header>", "<header><button id=\"versionBadge\" class=\"version-badge checking\" onclick=\"checkOpenWorkerVersion(true)\" title=\"點擊檢查更新\">OpenWorker · 檢查版本…</button>", 1)
    html = strings.Replace(html, "</body>", versionWidgetJS+"</body>", 1)
    _, _ = w.Write([]byte(html))
}

const versionWidgetCSS = `
.version-badge{position:absolute;right:18px;top:12px;z-index:8;font-size:12px;font-family:ui-monospace,SFMono-Regular,Consolas,monospace;padding:6px 9px;border-radius:999px;max-width:48vw;white-space:nowrap;overflow:hidden;text-overflow:ellipsis}.version-badge.current{border-color:#166534;color:#86efac}.version-badge.update{border-color:#b45309;color:#fde68a;box-shadow:0 0 0 1px rgba(245,158,11,.15)}.version-badge.error{border-color:#7f1d1d;color:#fca5a5}.version-badge.checking{color:#93c5fd}@media(max-width:760px){.version-badge{position:static;max-width:100%;margin-bottom:8px}}
`

const versionWidgetJS = `<script>
let owVersionState=null,owVersionTimer=null;
function shortSha(v){v=String(v||'').trim();return v&&v!=='unknown'?v.slice(0,8):'unknown'}
function workflowFor(machine){const m=String(machine||'').toUpperCase();if(m.includes('ODAQN0D'))return 'bootstrap-openworker-node-oda.yml';if(m.includes('O87PJNR'))return 'bootstrap-openworker-node-o87.yml';if(m.includes('UL7V2VV'))return 'bootstrap-openworker-node-ul7.yml';return ''}
async function checkOpenWorkerVersion(interactive){
 const b=document.getElementById('versionBadge');if(!b)return;
 b.className='version-badge checking';b.textContent='OpenWorker · 檢查版本…';
 try{
  const [sr,gr]=await Promise.all([fetch('/v1/node/status',{cache:'no-store'}),fetch('https://api.github.com/repos/liuxb99/openworker/commits/main',{cache:'no-store',headers:{Accept:'application/vnd.github+json'}})]);
  if(!sr.ok)throw new Error('node status HTTP '+sr.status);if(!gr.ok)throw new Error('GitHub HTTP '+gr.status);
  const s=await sr.json(),g=await gr.json();const current=String((s.service&&s.service.running_commit)||(s.build&&s.build.commit)||'unknown');const latest=String(g.sha||'');const version=String((s.build&&s.build.version)||'OpenWorker');const verified=!!(s.service&&s.service.upgrade_verified);const available=!!latest&&current!=='unknown'&&current.toLowerCase()!==latest.toLowerCase();const workflow=workflowFor(s.machine);const url=workflow?'https://github.com/liuxb99/openworker/actions/workflows/'+workflow:'';
  owVersionState={machine:s.machine,current,latest,version,verified,available,url};
  if(available){b.className='version-badge update';b.textContent='OpenWorker '+version+' · '+shortSha(current)+' → '+shortSha(latest)+' · 可升級';b.title='偵測到新版。點擊開啟 '+(workflow||'升級 workflow');if(interactive&&url)window.open(url,'_blank','noopener');}
  else{b.className='version-badge current';b.textContent='OpenWorker '+version+' · '+shortSha(current)+' · '+(verified?'VERIFIED · ':'')+'已是最新版';b.title='目前 running commit 與 GitHub main 一致。點擊重新檢查。';}
 }catch(e){b.className='version-badge error';b.textContent='OpenWorker · 版本檢查失敗';b.title=String(e);}
}
setTimeout(()=>checkOpenWorkerVersion(false),100);owVersionTimer=setInterval(()=>checkOpenWorkerVersion(false),300000);
</script>`
