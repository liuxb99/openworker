param(
  [string]$OpenWorkerUrl = 'http://127.0.0.1:8787',
  [string]$WorkspaceRoot = 'D:\AI-Work\jobs\0005-SNOW-WHITE',
  [string]$Machine = 'DESKTOP-ODAQN0D',
  [string]$ResidentRoot = 'D:\AI-Work\runtime\openworker'
)
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ine $Machine){ throw "wrong host expected=$Machine actual=$env:COMPUTERNAME" }

$source=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$node=Invoke-RestMethod "$OpenWorkerUrl/v1/node/status"
if(-not $node.online){ throw 'resident OpenWorker offline' }
if($node.machine -ine $Machine){ throw "resident node mismatch $($node.machine)" }
if([int]$node.max_workers -lt 4){ throw "resident node max_workers=$($node.max_workers), expected >=4" }

New-Item -ItemType Directory -Force -Path $ResidentRoot | Out-Null
foreach($name in @('coworker','case-worklists','case-specs')){
  $src=Join-Path $source $name
  $dst=Join-Path $ResidentRoot $name
  if(-not(Test-Path -LiteralPath $src)){ throw "missing runtime source $src" }
  if(Test-Path -LiteralPath $dst){ Remove-Item -LiteralPath $dst -Recurse -Force }
  Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
}
$pyproject=Join-Path $source 'pyproject.toml'
if(Test-Path -LiteralPath $pyproject){ Copy-Item -LiteralPath $pyproject -Destination (Join-Path $ResidentRoot 'pyproject.toml') -Force }

function Resolve-RepoRoot([string]$Name,[string[]]$Markers){
  $candidates=@((Join-Path 'D:\actions-runner\_work' "$Name\$Name"),(Join-Path 'D:\AI' $Name),(Join-Path 'D:\AIWork' $Name),(Join-Path 'D:\PyWork' $Name))
  foreach($c in $candidates){
    if(-not(Test-Path -LiteralPath $c -PathType Container)){continue}
    $ok=$true; foreach($m in $Markers){if(-not(Test-Path -LiteralPath (Join-Path $c $m))){$ok=$false;break}}
    if($ok){return (Resolve-Path $c).Path}
  }
  throw "local checkout not found for $Name"
}
function Resolve-RepoRootAlias([string[]]$Names,[string[]]$Markers){
  foreach($name in $Names){try{return Resolve-RepoRoot $name $Markers}catch{}}
  throw "local checkout not found for aliases=$($Names -join ',')"
}

$envMap=@{
  GO_TOOL_ROOT=(Resolve-RepoRoot 'go-tool-runtime' @('go.mod','cmd\gtr-local-exec\main.go'))
  COMFYX_ROOT=(Resolve-RepoRoot 'ComfyX' @('go.mod','cmd\comfyx-synthesis-video-real'))
  COMFYX_STUDIO_ROOT=(Resolve-RepoRoot 'Comfyx-Studio' @('go.mod','cmd\operator-director-preproduction'))
  OPENMAIC_ROOT=(Resolve-RepoRootAlias @('OpenMAIC','openmaic-fork') @('package.json','src\cli\presentation.ts'))
}
foreach($p in @('D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\output','D:\ComfyUI\output')){
  if(Test-Path -LiteralPath $p -PathType Container){$envMap.COMFYX_COMFYUI_OUTPUT_ROOT=$p;break}
}
if(-not $envMap.COMFYX_COMFYUI_OUTPUT_ROOT){throw 'COMFYX_COMFYUI_OUTPUT_ROOT not found on ODA'}

$body=@{
  case_id='0005'
  machine=$Machine
  workspace_root=$WorkspaceRoot
  openworker_root=$ResidentRoot
  controller_module='coworker.case0005_controller'
  manifest_path='case-worklists/0005.json'
  spec_path='case-specs/0005.json'
  env=$envMap
}|ConvertTo-Json -Depth 10

$ack=Invoke-RestMethod -Method Post "$OpenWorkerUrl/v1/cases/bootstrap" -ContentType 'application/json' -Body $body
if(-not $ack.job.accepted){throw 'Case 0005 bootstrap did not receive durable ACK'}
if($ack.machine -ine $Machine){throw "bootstrap ACK machine=$($ack.machine)"}

$evidence=Join-Path $WorkspaceRoot 'evidence'
New-Item -ItemType Directory -Force -Path $evidence | Out-Null
$receipt=[ordered]@{
  schema='openworker/case0005-resident-bootstrap/v1';case_id='0005';machine=$Machine;workspace_root=$WorkspaceRoot;
  resident_root=$ResidentRoot;transport='github-action-one-shot';business_execution='resident-openworker-local-supervisor';
  node=$node;ack=$ack;submitted_at=[DateTimeOffset]::UtcNow.ToString('o')
}
$receipt|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $evidence 'case0005-resident-bootstrap.json') -Encoding utf8
$receipt|ConvertTo-Json -Depth 20
