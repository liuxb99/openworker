$ErrorActionPreference='Stop'

$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$result=[ordered]@{
  schema='openworkerctl-oda-install/v3'
  succeeded=$false
  status='FAILED'
  machine=$env:COMPUTERNAME
  runner_name=$env:RUNNER_NAME
  executable=''
  supervisor_status=''
  route_label=''
  error=''
  github_run_id=$env:GITHUB_RUN_ID
  github_run_attempt=$env:GITHUB_RUN_ATTEMPT
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  observed_at=[DateTimeOffset]::UtcNow.ToString('o')
}

try {
  if($env:COMPUTERNAME -ine 'DESKTOP-ODAQN0D'){
    throw "wrong host $env:COMPUTERNAME expected=DESKTOP-ODAQN0D"
  }

  $installer=Join-Path $PSScriptRoot 'install-openworkerctl.ps1'
  if(-not(Test-Path -LiteralPath $installer -PathType Leaf)){
    throw "installer missing: $installer"
  }

  $installRoot=Join-Path $env:ProgramData 'OpenWorker\bin'
  & $installer -InstallRoot $installRoot

  $ctl=Join-Path $installRoot 'openworkerctl.exe'
  if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){
    throw "openworkerctl missing after install: $ctl"
  }

  $raw=& $ctl supervisor status 2>&1 | Out-String
  $exitCode=$LASTEXITCODE
  if($exitCode -ne 0){
    throw "openworkerctl supervisor status failed exit=$exitCode output=$raw"
  }
  try{$status=$raw|ConvertFrom-Json -ErrorAction Stop}catch{throw "non-JSON supervisor status: $raw"}
  if($status.status -ne 'OPERATIONAL'){
    throw "local supervisor is not OPERATIONAL: $raw"
  }
  if($status.route_label -ne 'LOCAL_SUPERVISOR'){
    throw "unexpected route_label=$($status.route_label)"
  }
  if($status.github_action_used_for_business_execution -eq $true){
    throw 'local supervisor reports GitHub business execution=true'
  }

  $result.succeeded=$true
  $result.status='REAL_VERIFIED'
  $result.executable=$ctl
  $result.supervisor_status=$status.status
  $result.route_label=$status.route_label
} catch {
  $result.error=$_.Exception.Message
}

$result.observed_at=[DateTimeOffset]::UtcNow.ToString('o')
$resultDir=Join-Path $repoRoot 'command-results'
New-Item -ItemType Directory -Force -Path $resultDir|Out-Null
$resultPath=Join-Path $resultDir 'oda-install.json'
$json=$result|ConvertTo-Json -Depth 30
[IO.File]::WriteAllText($resultPath,$json+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
Write-Host ($result|ConvertTo-Json -Depth 30 -Compress)

Push-Location $repoRoot
try {
  git config user.name 'openworker-control-plane-installer'
  git config user.email 'openworker-control-plane-installer@users.noreply.github.com'
  git add -- 'command-results/oda-install.json'
  git diff --cached --quiet
  if($LASTEXITCODE -ne 0){
    git commit -m "receipt: ODA openworkerctl install $env:GITHUB_RUN_ID"
    if($LASTEXITCODE -ne 0){throw 'failed to commit install receipt'}
    $pushed=$false
    for($i=0;$i -lt 3;$i++){
      git pull --rebase origin main
      if($LASTEXITCODE -ne 0){throw 'failed to rebase install receipt'}
      git push origin HEAD:main
      if($LASTEXITCODE -eq 0){$pushed=$true;break}
      Start-Sleep -Seconds 2
    }
    if(-not $pushed){throw 'failed to push install receipt'}
  }
} finally {
  Pop-Location
}

if(-not $result.succeeded){
  Write-Error "ODA_OPENWORKERCTL_INSTALL_FAILED error=$($result.error)"
  exit 1
}

Write-Host 'ODA_OPENWORKERCTL_INSTALL_REAL_VERIFIED'
exit 0
