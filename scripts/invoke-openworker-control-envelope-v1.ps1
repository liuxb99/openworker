param(
  [Parameter(Mandatory=$true)]
  [string]$EnvelopePath,
  [string]$ExpectedMachine = 'DESKTOP-ODAQN0D'
)

$ErrorActionPreference='Stop'

if($env:COMPUTERNAME -ine $ExpectedMachine){
  throw "wrong host $env:COMPUTERNAME expected=$ExpectedMachine"
}
if(-not(Test-Path -LiteralPath $EnvelopePath -PathType Leaf)){
  throw "control envelope not found: $EnvelopePath"
}

$raw=Get-Content -LiteralPath $EnvelopePath -Raw
$envl=$raw | ConvertFrom-Json -ErrorAction Stop

if($envl.schema -ne 'openworker.control-envelope/v1'){
  throw "unsupported schema: $($envl.schema)"
}
if([string]::IsNullOrWhiteSpace([string]$envl.request_id) -or ([string]$envl.request_id -notmatch '^[A-Za-z0-9._-]{8,128}$')){
  throw 'invalid request_id'
}
if([string]$envl.machine -ine $ExpectedMachine){
  throw "machine mismatch envelope=$($envl.machine) expected=$ExpectedMachine"
}
if([string]::IsNullOrWhiteSpace([string]$envl.case_id)){
  throw 'case_id is required'
}

$maxParallel=4
if($null -ne $envl.policy -and $null -ne $envl.policy.max_parallel){
  $maxParallel=[int]$envl.policy.max_parallel
}
if($maxParallel -lt 1 -or $maxParallel -gt 4){
  throw "max_parallel must be 1..4, got $maxParallel"
}

$ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworker.exe'
if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){
  $ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworkerctl.exe'
}
if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){
  throw "OpenWorker control executable is not installed: $ctl"
}

$command=[string]$envl.command
$cliArgs=@()
switch($command){
  'CASE.STATUS'         { $cliArgs=@('case','status',[string]$envl.case_id) }
  'CASE.CONTINUE_BATCH' { $cliArgs=@('case','continue',[string]$envl.case_id) }
  'SUPERVISOR.STATUS'   { $cliArgs=@('supervisor','status') }
  'QUEUE.CLEAR'         { $cliArgs=@('queue','clear',$ExpectedMachine) }
  default               { throw "unsupported control command: $command" }
}

$started=[DateTimeOffset]::UtcNow
$out=& $ctl @cliArgs 2>&1 | Out-String
$exitCode=$LASTEXITCODE
if($exitCode -ne 0){
  throw "OpenWorker control command failed exit=$exitCode output=$out"
}

try { $result=$out | ConvertFrom-Json -ErrorAction Stop }
catch { throw "OpenWorker control command returned non-JSON output: $out" }

$response=[ordered]@{
  schema='openworker.control-result/v1'
  request_id=[string]$envl.request_id
  command=$command
  case_id=[string]$envl.case_id
  machine=$ExpectedMachine
  accepted=$true
  max_parallel=$maxParallel
  dispatch_semantics=if($command -eq 'CASE.CONTINUE_BATCH'){'reconcile_ready_fanout'}else{'single_control_operation'}
  business_authority='openworker-go-native-case-controller'
  execution_authority='go-tool-runtime-local-supervisor'
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  started_at=$started.ToString('o')
  completed_at=[DateTimeOffset]::UtcNow.ToString('o')
  result=$result
}

$response | ConvertTo-Json -Depth 50
