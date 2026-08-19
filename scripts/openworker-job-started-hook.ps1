param()
$ErrorActionPreference='Stop'

$secret=[string]$env:OPENWORKER_CONTROL
if([string]::IsNullOrWhiteSpace($secret)){
  Write-Host '[OpenWorker Hook] no OPENWORKER_CONTROL; passthrough'
  exit 0
}

Write-Host '[OpenWorker Hook] OPENWORKER_CONTROL detected'
try {
  $envelope=$secret | ConvertFrom-Json -ErrorAction Stop
}catch{
  Write-Error "[OpenWorker Hook] invalid JSON: $($_.Exception.Message)"
  exit 80
}

if([string]$envelope.schema -ne 'openworker.control-envelope.v1'){
  Write-Error "[OpenWorker Hook] unsupported schema: $($envelope.schema)"
  exit 81
}
if([string]::IsNullOrWhiteSpace([string]$envelope.request_id) -or ([string]$envelope.request_id -notmatch '^[A-Za-z0-9._-]{8,128}$')){
  Write-Error '[OpenWorker Hook] invalid request_id'
  exit 82
}
if([string]::IsNullOrWhiteSpace([string]$envelope.command)){
  Write-Error '[OpenWorker Hook] command is required'
  exit 83
}

$allowed=@('CASE.STATUS','CASE.CONTINUE_BATCH','SUPERVISOR.STATUS','QUEUE.CLEAR')
if(([string]$envelope.command) -notin $allowed){
  Write-Error "[OpenWorker Hook] unsupported command: $($envelope.command)"
  exit 84
}

$machine=[string]$env:COMPUTERNAME
if([string]::IsNullOrWhiteSpace($machine)){$machine=[Environment]::MachineName}
if([string]$envelope.machine -ine $machine){
  Write-Error "[OpenWorker Hook] machine mismatch envelope=$($envelope.machine) local=$machine"
  exit 85
}

$max=4
if($null -ne $envelope.policy -and $null -ne $envelope.policy.max_parallel){$max=[int]$envelope.policy.max_parallel}
if($max -lt 1 -or $max -gt 4){
  Write-Error "[OpenWorker Hook] max_parallel must be 1..4, got $max"
  exit 86
}

$root=$env:OPENWORKER_ROOT
if([string]::IsNullOrWhiteSpace($root)){
  $candidates=@(
    (Join-Path $env:ProgramData 'OpenWorker\repo'),
    'C:\github-runners\openworker\_work\openworker\openworker',
    'D:\AI\openworker',
    'D:\AIWork\openworker',
    'D:\PyWork\openworker'
  )
  foreach($candidate in $candidates){
    if(Test-Path -LiteralPath (Join-Path $candidate 'scripts\invoke-openworker-control-envelope-v1.ps1') -PathType Leaf){$root=$candidate;break}
  }
}
if([string]::IsNullOrWhiteSpace($root)){
  Write-Error '[OpenWorker Hook] OpenWorker repo root not found'
  exit 87
}

$dispatcher=Join-Path $root 'scripts\invoke-openworker-control-envelope-v1.ps1'
if(-not(Test-Path -LiteralPath $dispatcher -PathType Leaf)){
  Write-Error "[OpenWorker Hook] dispatcher missing: $dispatcher"
  exit 88
}

$temp=Join-Path $env:TEMP ("openworker-control-"+[string]$envelope.request_id+'.json')
try {
  [IO.File]::WriteAllText($temp,($envelope | ConvertTo-Json -Depth 20)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
  & $dispatcher -EnvelopePath $temp -ExpectedMachine $machine
  $code=$LASTEXITCODE
  if($code -ne 0){
    Write-Error "[OpenWorker Hook] dispatcher failed exit=$code"
    exit $code
  }
  Write-Host '[OpenWorker Hook] control envelope accepted by OpenWorker'
  exit 0
}finally{
  Remove-Item -LiteralPath $temp -Force -ErrorAction SilentlyContinue
}
