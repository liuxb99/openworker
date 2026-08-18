param(
  [string]$OpenWorkerUrl = 'http://127.0.0.1:8787',
  [string]$WorkspaceRoot = 'D:\AI-Work\jobs\0005-SNOW-WHITE',
  [string]$Machine = 'DESKTOP-ODAQN0D'
)
$ErrorActionPreference='Stop'
if (-not $env:COMPUTERNAME.Equals($Machine,[StringComparison]::OrdinalIgnoreCase)) { throw "wrong host expected=$Machine actual=$env:COMPUTERNAME" }
New-Item -ItemType Directory -Force -Path $WorkspaceRoot,(Join-Path $WorkspaceRoot 'evidence'),(Join-Path $WorkspaceRoot 'parallel') | Out-Null
$node = Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/node/status"
$agents = Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/cluster/agents"
$stamp=[DateTimeOffset]::UtcNow.ToString('yyyyMMddTHHmmssfffZ')
$jobs=@(
  @{
    job_id="case0005-director-$stamp"; dispatch_id="case0005-parallel-$stamp-01"; machine=$Machine; priority=100;
    cwd=$WorkspaceRoot; workspace_root=$WorkspaceRoot; timeout_sec=120;
    command=('powershell -NoProfile -ExecutionPolicy Bypass -Command "gh workflow run operator-director-preproduction.yml -R liuxb99/Comfyx-Studio --ref main -f case_id=0005 -f workspace_root=' + $WorkspaceRoot + ' -f assigned_host=' + $Machine + ' -f source_title=''Snow White'' -f source_story=''A cinematic fairy-tale short: Snow White appears in a forest and castle world; the Queen and magic mirror establish danger; a poisoned apple causes the crisis; the ending restores hope. Keep Snow White, Queen, apple, castle, forest and mirror visually consistent across shots.''; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}"')
    locks=@('case0005-director-dispatch')
  },
  @{
    job_id="case0005-preflight-studio-$stamp"; dispatch_id="case0005-parallel-$stamp-02"; machine=$Machine; priority=80;
    cwd=$WorkspaceRoot; workspace_root=$WorkspaceRoot; timeout_sec=120;
    command=('powershell -NoProfile -ExecutionPolicy Bypass -Command "$o=''' + (Join-Path $WorkspaceRoot 'parallel\studio-workflows.txt') + '''; gh workflow list -R liuxb99/Comfyx-Studio | Out-File -Encoding utf8 $o; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}"')
    locks=@('case0005-preflight-studio')
  },
  @{
    job_id="case0005-preflight-comfyx-$stamp"; dispatch_id="case0005-parallel-$stamp-03"; machine=$Machine; priority=80;
    cwd=$WorkspaceRoot; workspace_root=$WorkspaceRoot; timeout_sec=120;
    command=('powershell -NoProfile -ExecutionPolicy Bypass -Command "$o=''' + (Join-Path $WorkspaceRoot 'parallel\comfyx-workflows.txt') + '''; gh workflow list -R liuxb99/ComfyX | Out-File -Encoding utf8 $o; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}"')
    locks=@('case0005-preflight-comfyx')
  },
  @{
    job_id="case0005-preflight-gotool-$stamp"; dispatch_id="case0005-parallel-$stamp-04"; machine=$Machine; priority=80;
    cwd=$WorkspaceRoot; workspace_root=$WorkspaceRoot; timeout_sec=120;
    command=('powershell -NoProfile -ExecutionPolicy Bypass -Command "$o=''' + (Join-Path $WorkspaceRoot 'parallel\go-tool-head.txt') + '''; gh api repos/liuxb99/go-tool-runtime/commits/main --jq ''.sha'' | Out-File -Encoding utf8 $o; if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}"')
    locks=@('case0005-preflight-gotool')
  }
)
$acks=@()
foreach($job in $jobs){
  $json=$job|ConvertTo-Json -Depth 8 -Compress
  $ack=Invoke-RestMethod -Method Post -Uri "$OpenWorkerUrl/v1/jobs" -ContentType 'application/json' -Body $json
  $acks += $ack
}
$receipt=[ordered]@{
  schema='openworker/case0005-local-parallel-bootstrap/v1'; case_id='0005'; machine=$Machine; workspace_root=$WorkspaceRoot;
  transport_run_id=$env:GITHUB_RUN_ID; submitted_at=[DateTimeOffset]::UtcNow.ToString('o'); node=$node; agents=$agents; durable_acks=$acks
}
$receiptPath=Join-Path $WorkspaceRoot 'evidence\case0005-parallel-bootstrap.json'
$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $receiptPath -Encoding utf8
Write-Host "CASE0005_PARALLEL_BOOTSTRAP_ACK count=$($acks.Count) receipt=$receiptPath"
$acks|ConvertTo-Json -Depth 8|Write-Host
