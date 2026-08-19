param(
  [Parameter(Mandatory=$true)]
  [string]$EnvelopePath,
  [string]$ExpectedMachine = 'DESKTOP-ODAQN0D',
  [int]$TimeoutSeconds = 30
)

$ErrorActionPreference='Stop'
if($TimeoutSeconds -lt 5 -or $TimeoutSeconds -gt 120){ throw "TimeoutSeconds must be 5..120" }

function Write-ControlReceipt {
  param([hashtable]$Receipt,[string]$Path)
  $dir=Split-Path -Parent $Path
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $tmp=$Path+'.tmp.'+[Guid]::NewGuid().ToString('N')
  [IO.File]::WriteAllText($tmp,($Receipt|ConvertTo-Json -Depth 50)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
  Move-Item -LiteralPath $tmp -Destination $Path -Force
}

if($env:COMPUTERNAME -ine $ExpectedMachine){ throw "wrong host $env:COMPUTERNAME expected=$ExpectedMachine" }
if(-not(Test-Path -LiteralPath $EnvelopePath -PathType Leaf)){ throw "control envelope not found: $EnvelopePath" }

$raw=Get-Content -LiteralPath $EnvelopePath -Raw
$envl=$raw | ConvertFrom-Json -ErrorAction Stop
if($envl.schema -ne 'openworker.control-envelope.v1'){ throw "unsupported schema: $($envl.schema)" }
$requestId=[string]$envl.request_id
if([string]::IsNullOrWhiteSpace($requestId) -or ($requestId -notmatch '^[A-Za-z0-9._-]{8,128}$')){ throw 'invalid request_id' }
if([string]$envl.machine -ine $ExpectedMachine){ throw "machine mismatch envelope=$($envl.machine) expected=$ExpectedMachine" }

$command=[string]$envl.command
$needsCase=$command -in @('CASE.STATUS','CASE.CONTINUE_BATCH')
if($needsCase -and [string]::IsNullOrWhiteSpace([string]$envl.case_id)){ throw 'case_id is required' }

$maxParallel=4
if($null -ne $envl.policy -and $null -ne $envl.policy.max_parallel){$maxParallel=[int]$envl.policy.max_parallel}
if($maxParallel -lt 1 -or $maxParallel -gt 4){ throw "max_parallel must be 1..4, got $maxParallel" }

$receiptRoot=Join-Path $env:ProgramData 'OpenWorker\control-envelope\receipts'
$receiptPath=Join-Path $receiptRoot ($requestId+'.json')
if(Test-Path -LiteralPath $receiptPath -PathType Leaf){
  $cached=Get-Content -LiteralPath $receiptPath -Raw
  try{$cachedObj=$cached|ConvertFrom-Json -ErrorAction Stop}catch{$cachedObj=$null}
  if($null -ne $cachedObj -and [string]$cachedObj.request_id -eq $requestId){
    Write-Host "OPENWORKER_CONTROL_IDEMPOTENT_HIT request_id=$requestId"
    $cached
    exit ([int]$cachedObj.exit_code)
  }
}

$ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworker.exe'
if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){$ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworkerctl.exe'}
if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){ throw "OpenWorker control executable is not installed: $ctl" }

$cliArgs=@()
switch($command){
  'CASE.STATUS'          { $cliArgs=@('case','status',[string]$envl.case_id) }
  'CASE.CONTINUE_BATCH'  { $cliArgs=@('case','continue',[string]$envl.case_id) }
  'SUPERVISOR.STATUS'    { $cliArgs=@('supervisor','status') }
  'QUEUE.CLEAR'          { $cliArgs=@('queue','clear',$ExpectedMachine) }
  default                { throw "unsupported control command: $command" }
}

$started=[DateTimeOffset]::UtcNow
$exitCode=0;$errorClass='';$errorText='';$result=$null;$stdout=''
try{
  $job=Start-Job -ScriptBlock { param($exe,$args) & $exe @args 2>&1 | Out-String; exit $LASTEXITCODE } -ArgumentList $ctl,(,$cliArgs)
  $done=Wait-Job -Job $job -Timeout $TimeoutSeconds
  if($null -eq $done){
    Stop-Job -Job $job -Force -ErrorAction SilentlyContinue
    $exitCode=124;$errorClass='timeout';$errorText="OpenWorker control timed out after ${TimeoutSeconds}s"
  }else{
    $stdout=(Receive-Job -Job $job | Out-String).Trim()
    $childState=$job.ChildJobs[0]
    $nativeCode=$childState.Output[-1]
    if($stdout -match 'OPENWORKER_FAIL:.*127\.0\.0\.1:8848.*(refused|connectex|connection)'){
      $exitCode=71;$errorClass='go_tool_unreachable';$errorText=$stdout
    }elseif($childState.State -ne 'Completed'){
      $exitCode=70;$errorClass='openworker_process_failed';$errorText=$stdout
    }else{
      try{$result=$stdout|ConvertFrom-Json -ErrorAction Stop}
      catch{$exitCode=72;$errorClass='invalid_control_output';$errorText=$stdout}
    }
  }
}finally{
  if($null -ne $job){Remove-Job -Job $job -Force -ErrorAction SilentlyContinue}
}

$accepted=($exitCode -eq 0 -and $null -ne $result)
$response=[ordered]@{
  schema='openworker.control-result.v2'
  request_id=$requestId
  command=$command
  case_id=if($needsCase){[string]$envl.case_id}else{$null}
  machine=$ExpectedMachine
  accepted=$accepted
  exit_code=$exitCode
  error_class=$errorClass
  error=$errorText
  max_parallel=$maxParallel
  dispatch_semantics=if($command -eq 'CASE.CONTINUE_BATCH'){'reconcile_ready_fanout'}else{'single_control_operation'}
  business_authority='openworker-go-native-case-controller'
  execution_authority='go-tool-runtime-local-supervisor'
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  timeout_seconds=$TimeoutSeconds
  started_at=$started.ToString('o')
  completed_at=[DateTimeOffset]::UtcNow.ToString('o')
  result=$result
}
Write-ControlReceipt -Receipt $response -Path $receiptPath
$response|ConvertTo-Json -Depth 50
exit $exitCode
