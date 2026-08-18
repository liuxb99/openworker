# case0005-bootstrap-transport-marker: 2026-08-18T23:28+08:00
param(
  [Parameter(Mandatory=$true)][string]$SourceExe,
  [string]$ServiceName='OpenWorkerNode',
  [string]$InstallDir='C:\ProgramData\OpenWorker\bin',
  [string]$DataDir='C:\ProgramData\OpenWorker\node',
  [string]$Listen='127.0.0.1:8787',
  [string]$Advertise='',
  [int]$Workers=4,
  [string]$Capabilities='',
  [string]$Peers=''
)
$ErrorActionPreference='Stop'
$identity=[Security.Principal.WindowsIdentity]::GetCurrent()
$principal=[Security.Principal.WindowsPrincipal]::new($identity)
$isAdmin=$principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
if(-not(Test-Path -LiteralPath $SourceExe -PathType Leaf)){throw "Source exe not found: $SourceExe"}
New-Item -ItemType Directory -Force -Path $InstallDir,$DataDir|Out-Null
$target=Join-Path $InstallDir 'openworker-node.exe'

function Get-HealthUrl([string]$addr){
  $port=[int]($addr.Split(':')[-1])
  return "http://127.0.0.1:$port/healthz"
}
function Wait-Health([string]$url){
  for($i=0;$i-lt 40;$i++){
    try{$h=Invoke-RestMethod -Uri $url -TimeoutSec 2;if($h.ok){return $h}}catch{}
    Start-Sleep -Milliseconds 500
  }
  throw "OpenWorker node health check failed: $url"
}
function Build-Args {
  $a=@('-listen',$Listen,'-data',$DataDir,'-workers',[string]$Workers)
  if(-not[string]::IsNullOrWhiteSpace($Capabilities)){$a+=@('-capabilities',$Capabilities.Replace('"',''))}
  if(-not[string]::IsNullOrWhiteSpace($Peers)){$a+=@('-peers',$Peers.Replace('"',''))}
  if(-not[string]::IsNullOrWhiteSpace($Advertise)){$a+=@('-advertise',$Advertise.Replace('"',''))}
  return ,$a
}

if($isAdmin){
  $svc=Get-Service -Name $ServiceName -ErrorAction SilentlyContinue
  if($svc -and $svc.Status -ne 'Stopped'){Stop-Service -Name $ServiceName -Force;$svc.WaitForStatus('Stopped',[TimeSpan]::FromSeconds(30))}
  Copy-Item -LiteralPath $SourceExe -Destination $target -Force
  $capArg='';if(-not[string]::IsNullOrWhiteSpace($Capabilities)){$capArg=' -capabilities "{0}"' -f $Capabilities.Replace('"','')}
  $peerArg='';if(-not[string]::IsNullOrWhiteSpace($Peers)){$peerArg=' -peers "{0}"' -f $Peers.Replace('"','')}
  $advArg='';if(-not[string]::IsNullOrWhiteSpace($Advertise)){$advArg=' -advertise "{0}"' -f $Advertise.Replace('"','')}
  $bin='"{0}" -service -listen {1} -data "{2}" -workers {3}{4}{5}{6}' -f $target,$Listen,$DataDir,$Workers,$capArg,$peerArg,$advArg
  if(-not $svc){
    sc.exe create $ServiceName binPath= $bin start= auto DisplayName= 'OpenWorker Local Execution Node'|Out-Host
    if($LASTEXITCODE-ne 0){throw "sc create failed rc=$LASTEXITCODE"}
  }else{
    sc.exe config $ServiceName binPath= $bin start= auto|Out-Host
    if($LASTEXITCODE-ne 0){throw "sc config failed rc=$LASTEXITCODE"}
  }
  sc.exe failure $ServiceName reset=86400 actions=restart/5000/restart/15000/restart/60000|Out-Host
  sc.exe failureflag $ServiceName 1|Out-Host
  Start-Service -Name $ServiceName
  (Get-Service -Name $ServiceName).WaitForStatus('Running',[TimeSpan]::FromSeconds(30))
  $h=Wait-Health (Get-HealthUrl $Listen)
  [ordered]@{schema='openworker.windows-service-install.v5';mode='windows_service';service=$ServiceName;status=(Get-Service -Name $ServiceName).Status.ToString();exe=$target;data_dir=$DataDir;listen=$Listen;advertise=$Advertise;workers=$Workers;capabilities=$Capabilities;peers=$Peers;machine=$env:COMPUTERNAME;health=$h}|ConvertTo-Json -Depth 8
  exit 0
}

Get-Process -Name 'openworker-node' -ErrorAction SilentlyContinue | ForEach-Object {
  try { Stop-Process -Id $_.Id -Force -ErrorAction Stop } catch {}
}
Start-Sleep -Milliseconds 300
Copy-Item -LiteralPath $SourceExe -Destination $target -Force
$args=Build-Args
$oldTracking=$env:RUNNER_TRACKING_ID
try{
  Remove-Item Env:RUNNER_TRACKING_ID -ErrorAction SilentlyContinue
  $p=Start-Process -FilePath $target -ArgumentList $args -WorkingDirectory $DataDir -WindowStyle Hidden -PassThru
}finally{
  if($null-ne $oldTracking){$env:RUNNER_TRACKING_ID=$oldTracking}
}
$h=Wait-Health (Get-HealthUrl $Listen)
[ordered]@{schema='openworker.windows-service-install.v5';mode='detached_process';service=$null;status='Running';pid=$p.Id;exe=$target;data_dir=$DataDir;listen=$Listen;advertise=$Advertise;workers=$Workers;capabilities=$Capabilities;peers=$Peers;machine=$env:COMPUTERNAME;health=$h}|ConvertTo-Json -Depth 8
