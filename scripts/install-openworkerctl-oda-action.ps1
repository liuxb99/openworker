$ErrorActionPreference='Stop'

if($env:COMPUTERNAME -ine 'DESKTOP-ODAQN0D'){
  throw "wrong host $env:COMPUTERNAME expected=DESKTOP-ODAQN0D"
}

$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
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

$result=[ordered]@{
  schema='openworkerctl-oda-install/v2'
  status='REAL_VERIFIED'
  machine=$env:COMPUTERNAME
  runner_name=$env:RUNNER_NAME
  executable=$ctl
  supervisor_status=$status.status
  route_label=$status.route_label
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  verified_at=[DateTimeOffset]::UtcNow.ToString('o')
}
$result|ConvertTo-Json -Depth 20
