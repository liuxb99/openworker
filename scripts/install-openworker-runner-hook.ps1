param(
  [Parameter(Mandatory=$true)]
  [string]$RunnerRoot,
  [string]$OpenWorkerRepoRoot = ''
)

$ErrorActionPreference='Stop'
$RunnerRoot=(Resolve-Path -LiteralPath $RunnerRoot).Path
$envFile=Join-Path $RunnerRoot '.env'
if(-not(Test-Path -LiteralPath $envFile -PathType Leaf)){
  throw "runner .env not found: $envFile"
}
if([string]::IsNullOrWhiteSpace($OpenWorkerRepoRoot)){
  $OpenWorkerRepoRoot=$PSScriptRoot | Split-Path -Parent
}
$OpenWorkerRepoRoot=(Resolve-Path -LiteralPath $OpenWorkerRepoRoot).Path
$srcPs=Join-Path $OpenWorkerRepoRoot 'scripts\openworker-job-started-hook.ps1'
$srcCmd=Join-Path $OpenWorkerRepoRoot 'scripts\openworker-job-started.cmd'
if(-not(Test-Path -LiteralPath $srcPs -PathType Leaf)){throw "missing hook source: $srcPs"}
if(-not(Test-Path -LiteralPath $srcCmd -PathType Leaf)){throw "missing hook entrypoint: $srcCmd"}

$dest=Join-Path $env:ProgramData 'OpenWorker\hooks'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -LiteralPath $srcPs -Destination (Join-Path $dest 'openworker-job-started-hook.ps1') -Force
Copy-Item -LiteralPath $srcCmd -Destination (Join-Path $dest 'openworker-job-started.cmd') -Force

$hookPath='C:\ProgramData\OpenWorker\hooks\openworker-job-started.cmd'
$lines=@(Get-Content -LiteralPath $envFile -ErrorAction Stop)
$found=$false
$out=New-Object System.Collections.Generic.List[string]
foreach($line in $lines){
  if($line -match '^ACTIONS_RUNNER_HOOK_JOB_STARTED='){
    $out.Add('ACTIONS_RUNNER_HOOK_JOB_STARTED='+$hookPath)
    $found=$true
  }else{
    $out.Add($line)
  }
}
if(-not $found){$out.Add('ACTIONS_RUNNER_HOOK_JOB_STARTED='+$hookPath)}
[IO.File]::WriteAllLines($envFile,$out,[Text.UTF8Encoding]::new($false))

Write-Output ([ordered]@{
  schema='openworker.runner-hook-install.v1'
  runner_root=$RunnerRoot
  env_file=$envFile
  hook=$hookPath
  installed=$true
  restart_required=$true
} | ConvertTo-Json -Depth 5)
