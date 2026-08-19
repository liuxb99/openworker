$ErrorActionPreference='Stop'

$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$result=[ordered]@{
  schema='openworker-control-install/v4'
  succeeded=$false
  status='FAILED'
  machine=$env:COMPUTERNAME
  runner_name=$env:RUNNER_NAME
  canonical_executable=''
  compatibility_executable=''
  supervisor_status=''
  route_label=''
  single_go_control_authority=$true
  python_required_for_case_bootstrap=$false
  error=''
  github_run_id=$env:GITHUB_RUN_ID
  github_run_attempt=$env:GITHUB_RUN_ATTEMPT
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  observed_at=[DateTimeOffset]::UtcNow.ToString('o')
}

try {
  if($env:COMPUTERNAME -ine 'DESKTOP-ODAQN0D'){throw "wrong host $env:COMPUTERNAME expected=DESKTOP-ODAQN0D"}
  $installer=Join-Path $PSScriptRoot 'install-openworkerctl.ps1'
  if(-not(Test-Path -LiteralPath $installer -PathType Leaf)){throw "installer missing: $installer"}
  $installRoot=Join-Path $env:ProgramData 'OpenWorker\bin'
  & $installer -InstallRoot $installRoot
  $openworker=Join-Path $installRoot 'openworker.exe'
  $ctl=Join-Path $installRoot 'openworkerctl.exe'
  if(-not(Test-Path -LiteralPath $openworker -PathType Leaf)){throw "openworker missing after install: $openworker"}
  if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){throw "openworkerctl compatibility binary missing after install: $ctl"}
  $raw=& $openworker supervisor status 2>&1 | Out-String
  $exitCode=$LASTEXITCODE
  if($exitCode -ne 0){throw "openworker supervisor status failed exit=$exitCode output=$raw"}
  try{$status=$raw|ConvertFrom-Json -ErrorAction Stop}catch{throw "non-JSON supervisor status: $raw"}
  if($status.status -ne 'OPERATIONAL'){throw "local supervisor is not OPERATIONAL: $raw"}
  if($status.route_label -ne 'LOCAL_SUPERVISOR'){throw "unexpected route_label=$($status.route_label)"}
  if($status.github_action_used_for_business_execution -eq $true){throw 'local supervisor reports GitHub business execution=true'}
  $result.succeeded=$true
  $result.status='REAL_VERIFIED'
  $result.canonical_executable=$openworker
  $result.compatibility_executable=$ctl
  $result.supervisor_status=$status.status
  $result.route_label=$status.route_label
} catch {
  $result.error=$_.Exception.Message
}

$result.observed_at=[DateTimeOffset]::UtcNow.ToString('o')
$rel="command-results/oda-install/$env:GITHUB_RUN_ID/final.json"
$resultPath=Join-Path $repoRoot $rel
New-Item -ItemType Directory -Force -Path (Split-Path $resultPath -Parent)|Out-Null
$json=$result|ConvertTo-Json -Depth 30
[IO.File]::WriteAllText($resultPath,$json+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
Write-Host ($result|ConvertTo-Json -Depth 30 -Compress)

Push-Location $repoRoot
try {
  git config user.name 'openworker-control-plane-installer'
  git config user.email 'openworker-control-plane-installer@users.noreply.github.com'
  git add -- $rel
  if(Test-Path -LiteralPath (Join-Path $repoRoot 'go-runtime\go.sum')){git add -- 'go-runtime/go.sum'}
  git diff --cached --quiet
  if($LASTEXITCODE -ne 0){
    git commit -m "receipt: unified Go OpenWorker install $env:GITHUB_RUN_ID"
    if($LASTEXITCODE -ne 0){throw 'failed to commit install receipt/module sums'}
    $pushed=$false
    for($i=0;$i -lt 3;$i++){
      git pull --rebase origin main
      if($LASTEXITCODE -ne 0){git rebase --abort 2>$null; Start-Sleep -Seconds 2; continue}
      git push origin HEAD:main
      if($LASTEXITCODE -eq 0){$pushed=$true;break}
      Start-Sleep -Seconds 2
    }
    if(-not $pushed){throw 'failed to push immutable install receipt'}
  }
} finally { Pop-Location }

if(-not $result.succeeded){Write-Error "ODA_OPENWORKER_INSTALL_FAILED error=$($result.error)";exit 1}
Write-Host 'ODA_OPENWORKER_UNIFIED_GO_REAL_VERIFIED'
exit 0
