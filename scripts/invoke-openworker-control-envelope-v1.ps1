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
function Quote-Arg([string]$s){ if($null-eq$s){return '""'}; return '"'+$s.Replace('"','\"')+'"' }

if($env:COMPUTERNAME -ine $ExpectedMachine){ throw "wrong host $env:COMPUTERNAME expected=$ExpectedMachine" }
if(-not(Test-Path -LiteralPath $EnvelopePath -PathType Leaf)){ throw "control envelope not found: $EnvelopePath" }
$envl=(Get-Content -LiteralPath $EnvelopePath -Raw)|ConvertFrom-Json -ErrorAction Stop
if($envl.schema -ne 'openworker.control-envelope.v1'){ throw "unsupported schema: $($envl.schema)" }
$requestId=[string]$envl.request_id
if([string]::IsNullOrWhiteSpace($requestId) -or ($requestId -notmatch '^[A-Za-z0-9._-]{8,128}$')){ throw 'invalid request_id' }
if([string]$envl.machine -ine $ExpectedMachine){ throw "machine mismatch envelope=$($envl.machine) expected=$ExpectedMachine" }

$command=[string]$envl.command
$needsCase=$command -in @('CASE.STATUS','CASE.CONTINUE_BATCH')
if($needsCase -and [string]::IsNullOrWhiteSpace([string]$envl.case_id)){ throw 'case_id is required' }
$maxParallel=4
if($null-ne$envl.policy-and$null-ne$envl.policy.max_parallel){$maxParallel=[int]$envl.policy.max_parallel}
if($maxParallel-lt1-or$maxParallel-gt4){ throw "max_parallel must be 1..4, got $maxParallel" }

$receiptRoot=Join-Path $env:ProgramData 'OpenWorker\control-envelope\receipts'
$receiptPath=Join-Path $receiptRoot ($requestId+'.json')
if(Test-Path -LiteralPath $receiptPath -PathType Leaf){
  $cached=Get-Content -LiteralPath $receiptPath -Raw
  try{$cachedObj=$cached|ConvertFrom-Json -ErrorAction Stop}catch{$cachedObj=$null}
  if(($null -ne $cachedObj) -and ([string]$cachedObj.request_id -eq $requestId)){
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
  'CASE.STATUS'         {$cliArgs=@('case','status',[string]$envl.case_id)}
  'CASE.CONTINUE_BATCH'{$cliArgs=@('case','continue',[string]$envl.case_id)}
  'SUPERVISOR.STATUS'  {$cliArgs=@('supervisor','status')}
  'QUEUE.CLEAR'        {$cliArgs=@('queue','clear',$ExpectedMachine)}
  default              {throw "unsupported control command: $command"}
}

$started=[DateTimeOffset]::UtcNow
$exitCode=0;$errorClass='';$errorText='';$result=$null
$outFile=Join-Path $env:TEMP ("openworker-out-$requestId-"+[Guid]::NewGuid().ToString('N')+'.txt')
$errFile=Join-Path $env:TEMP ("openworker-err-$requestId-"+[Guid]::NewGuid().ToString('N')+'.txt')
try{
  $argLine=($cliArgs|ForEach-Object{Quote-Arg ([string]$_)}) -join ' '
  $p=Start-Process -FilePath $ctl -ArgumentList $argLine -NoNewWindow -PassThru -RedirectStandardOutput $outFile -RedirectStandardError $errFile
  if(-not $p.WaitForExit($TimeoutSeconds*1000)){
    try{$p.Kill()}catch{}
    $exitCode=124;$errorClass='timeout';$errorText="OpenWorker control timed out after ${TimeoutSeconds}s"
  }else{
    $exitCode=[int]$p.ExitCode
    $stdout=if(Test-Path $outFile){Get-Content -LiteralPath $outFile -Raw}else{''}
    $stderr=if(Test-Path $errFile){Get-Content -LiteralPath $errFile -Raw}else{''}
    $combined=($stdout+"`n"+$stderr).Trim()
    if($exitCode -ne 0){
      if(($combined -match '127\.0\.0\.1:8848') -and ($combined -match '(refused|connectex|connection)')){$errorClass='go_tool_unreachable'}else{$errorClass='openworker_process_failed'}
      $errorText=$combined
    }else{
      try{$result=$stdout|ConvertFrom-Json -ErrorAction Stop}catch{$exitCode=72;$errorClass='invalid_control_output';$errorText=$combined}
    }
  }
}finally{
  Remove-Item -LiteralPath $outFile,$errFile -Force -ErrorAction SilentlyContinue
}

$accepted = (($exitCode -eq 0) -and ($null -ne $result))
$response=[ordered]@{
  schema='openworker.control-result.v2';request_id=$requestId;command=$command;case_id=if($needsCase){[string]$envl.case_id}else{$null};machine=$ExpectedMachine
  accepted=$accepted;exit_code=$exitCode;error_class=$errorClass;error=$errorText;max_parallel=$maxParallel
  dispatch_semantics=if($command-eq'CASE.CONTINUE_BATCH'){'reconcile_ready_fanout'}else{'single_control_operation'}
  business_authority='openworker-go-native-case-controller';execution_authority='go-tool-runtime-local-supervisor'
  github_action_used_for_command_transport=$true;github_action_used_for_business_execution=$false;timeout_seconds=$TimeoutSeconds
  started_at=$started.ToString('o');completed_at=[DateTimeOffset]::UtcNow.ToString('o');result=$result
}
Write-ControlReceipt -Receipt $response -Path $receiptPath
$response|ConvertTo-Json -Depth 50
exit $exitCode
