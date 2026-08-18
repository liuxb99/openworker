param(
  [string]$OpenWorkerUrl = 'http://127.0.0.1:8787',
  [string]$WorkspaceRoot = 'D:\AI-Work\jobs\0003-YUJING-BRIDGE',
  [string]$Machine = 'DESKTOP-UL7V2VV',
  [string]$GoToolRoot = $env:GO_TOOL_ROOT,
  [string]$TerrainRoot = $env:TERRAIN_ROOT
)
$ErrorActionPreference='Stop'
if (-not $env:COMPUTERNAME.Equals($Machine,[StringComparison]::OrdinalIgnoreCase)) { throw "wrong host expected=$Machine actual=$env:COMPUTERNAME" }
if ([string]::IsNullOrWhiteSpace($GoToolRoot)) { throw 'GO_TOOL_ROOT/GoToolRoot is required for localexec' }
if ([string]::IsNullOrWhiteSpace($TerrainRoot)) { throw 'TERRAIN_ROOT/TerrainRoot is required for Terrain localexec' }
if (-not (Test-Path -LiteralPath (Join-Path $GoToolRoot 'go.mod'))) { throw "invalid go-tool root: $GoToolRoot" }
if (-not (Test-Path -LiteralPath (Join-Path $TerrainRoot 'go.mod'))) { throw "invalid Terrain root: $TerrainRoot" }
$geo=Join-Path $WorkspaceRoot 'geo\geolocation.json'
if (-not (Test-Path -LiteralPath $geo)) { throw "accepted geolocation missing: $geo" }
$claimDir=Join-Path $WorkspaceRoot '.openworker\localexec'
$evidenceDir=Join-Path $WorkspaceRoot 'evidence'
New-Item -ItemType Directory -Force -Path $claimDir,$evidenceDir | Out-Null
function Read-Json([string]$Path){if(-not(Test-Path -LiteralPath $Path)){return $null};try{return Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}catch{return $null}}
function File-OK([string]$Path){return (Test-Path -LiteralPath $Path -PathType Leaf) -and ((Get-Item -LiteralPath $Path).Length -gt 0)}
function StreetView-OK{$m=Read-Json (Join-Path $WorkspaceRoot 'streetview\browser\streetview-browser-screenshots.json');if($null -eq $m -or -not $m.ok -or $m.schema_version -ne 'streetview-browser-screenshots/v2'){return $false};$r=@($m.renders);if($r.Count -ne 4){return $false};foreach($x in $r){if(-not(File-OK ([string]$x.path))){return $false}};return $true}
function Ortho-OK{$e=Read-Json (Join-Path $WorkspaceRoot 'orthophoto\nlsc-photo2\orthophoto-photo2-evidence.json');return $null -ne $e -and $e.ok -and (File-OK ([string]$e.output_path))}
$jobSnapshot=Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/jobs?limit=1000"
$activeStates=@('accepted','queued_local','starting','running')
function Active-Prefix([string]$Prefix){foreach($j in @($jobSnapshot.jobs)){if(([string]$j.job_id).StartsWith($Prefix,[StringComparison]::OrdinalIgnoreCase) -and $activeStates -contains [string]$j.status){return $true}};return $false}
$stamp=[DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$specs=@()
if(-not(StreetView-OK) -and -not(Active-Prefix 'case0003-streetview-')){$specs+=@{id='terrain.streetview.acquire';short='streetview';priority=100;lock='case0003-streetview-local'}}
if(-not(Ortho-OK) -and -not(Active-Prefix 'case0003-orthophoto-')){$specs+=@{id='terrain.orthophoto.acquire';short='orthophoto';priority=100;lock='case0003-orthophoto-local'}}
$jobs=@()
foreach($spec in $specs){
  $workId="case0003-$($spec.short)-$stamp"
  $claimPath=Join-Path $claimDir ($workId+'.json')
  $resultPath=Join-Path $evidenceDir ($workId+'-localexec-result.json')
  $claim=[ordered]@{work_id=$workId;assigned_host=$Machine;capability_id=$spec.id;inputs=[ordered]@{workspace_root=$WorkspaceRoot;assigned_host=$Machine};claimed_by='openworker-local-supervisor';lease_token=$workId}
  $claim|ConvertTo-Json -Depth 8|Set-Content -LiteralPath $claimPath -Encoding utf8
  $escapedGo=$GoToolRoot.Replace("'","''");$escapedTerrain=$TerrainRoot.Replace("'","''");$escapedClaim=$claimPath.Replace("'","''");$escapedResult=$resultPath.Replace("'","''")
  $cmd="powershell -NoProfile -ExecutionPolicy Bypass -Command `"`$env:TERRAIN_ROOT='$escapedTerrain'; Set-Location -LiteralPath '$escapedGo'; go run ./cmd/gtr-local-exec --claim '$escapedClaim' --timeout 10m | Set-Content -LiteralPath '$escapedResult' -Encoding utf8; if(`$LASTEXITCODE -ne 0){exit `$LASTEXITCODE}`""
  $jobs+=@{job_id=$workId;dispatch_id="case0003-imagery-local-$stamp-$($spec.short)";machine=$Machine;priority=$spec.priority;cwd=$WorkspaceRoot;workspace_root=$WorkspaceRoot;timeout_sec=660;command=$cmd;locks=@($spec.lock)}
}
$node=Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/node/status"
$agents=Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/cluster/agents"
$acks=@();foreach($job in $jobs){$acks+=Invoke-RestMethod -Method Post -Uri "$OpenWorkerUrl/v1/jobs" -ContentType 'application/json' -Body ($job|ConvertTo-Json -Depth 8 -Compress)}
$receipt=[ordered]@{schema='openworker/case0003-local-imagery-parallel/v2';case_id='0003';machine=$Machine;workspace_root=$WorkspaceRoot;transport='openworker-local-jobs+go-tool-localexec';github_business_transport=$false;submitted_at=[DateTimeOffset]::UtcNow.ToString('o');node=$node;agents=$agents;submitted_count=$acks.Count;durable_acks=$acks}
$receiptPath=Join-Path $evidenceDir 'case0003-local-imagery-parallel-submit.json';$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Host "CASE0003_LOCAL_IMAGERY_PARALLEL_ACK count=$($acks.Count) receipt=$receiptPath";$acks|ConvertTo-Json -Depth 8|Write-Host
