param(
  [Parameter(Mandatory=$true)][string]$SourceExe,
  [string]$ServiceName = 'OpenWorkerNode',
  [string]$InstallDir = 'C:\ProgramData\OpenWorker\bin',
  [string]$DataDir = 'C:\ProgramData\OpenWorker\node',
  [string]$Listen = '127.0.0.1:8787',
  [int]$Workers = 4,
  [string]$Capabilities = ''
)

$ErrorActionPreference='Stop'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=[Security.Principal.WindowsPrincipal]::new($identity)
if(-not $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)){throw 'Administrator privileges are required'}
if(-not(Test-Path -LiteralPath $SourceExe -PathType Leaf)){throw "Source exe not found: $SourceExe"}

New-Item -ItemType Directory -Force -Path $InstallDir,$DataDir | Out-Null
$target=Join-Path $InstallDir 'openworker-node.exe'
$svc=Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
if($svc){
  if($svc.Status -ne 'Stopped'){
    Stop-Service -Name $ServiceName -Force
    $svc.WaitForStatus('Stopped',[TimeSpan]::FromSeconds(30))
  }
}
Copy-Item -LiteralPath $SourceExe -Destination $target -Force
$capArg=''
if(-not [string]::IsNullOrWhiteSpace($Capabilities)){$capArg=' -capabilities "{0}"' -f $Capabilities.Replace('"','')}
$bin='"{0}" -service -listen {1} -data "{2}" -workers {3}{4}' -f $target,$Listen,$DataDir,$Workers,$capArg
if(-not $svc){
  sc.exe create $ServiceName binPath= $bin start= auto DisplayName= 'OpenWorker Local Execution Node' | Out-Host
  if($LASTEXITCODE -ne 0){throw "sc create failed rc=$LASTEXITCODE"}
}else{
  sc.exe config $ServiceName binPath= $bin start= auto | Out-Host
  if($LASTEXITCODE -ne 0){throw "sc config failed rc=$LASTEXITCODE"}
}
sc.exe failure $ServiceName reset= 86400 actions= restart/5000/restart/15000/restart/60000 | Out-Host
sc.exe failureflag $ServiceName 1 | Out-Host
Start-Service -Name $ServiceName
(Get-Service -Name $ServiceName).WaitForStatus('Running',[TimeSpan]::FromSeconds(30))

$health="http://$Listen/healthz"
$ok=$false
for($i=0;$i -lt 30;$i++){
  try{$h=Invoke-RestMethod -Uri $health -TimeoutSec 2;if($h.ok){$ok=$true;break}}catch{}
  Start-Sleep -Milliseconds 500
}
if(-not $ok){throw "Service is running but health check failed: $health"}
[ordered]@{
  schema='openworker.windows-service-install.v2'
  service=$ServiceName
  status=(Get-Service -Name $ServiceName).Status.ToString()
  exe=$target
  data_dir=$DataDir
  listen=$Listen
  workers=$Workers
  capabilities=$Capabilities
  machine=$env:COMPUTERNAME
  health=$h
}|ConvertTo-Json -Depth 8
