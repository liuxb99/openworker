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
$srcDispatcher=Join-Path $OpenWorkerRepoRoot 'scripts\invoke-openworker-control-envelope-v1.ps1'
foreach($src in @($srcPs,$srcCmd,$srcDispatcher)){
  if(-not(Test-Path -LiteralPath $src -PathType Leaf)){throw "missing hook source: $src"}
}

$dest=Join-Path $env:ProgramData 'OpenWorker\hooks'
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -LiteralPath $srcPs -Destination (Join-Path $dest 'openworker-job-started-hook.ps1') -Force
Copy-Item -LiteralPath $srcCmd -Destination (Join-Path $dest 'openworker-job-started.cmd') -Force
Copy-Item -LiteralPath $srcDispatcher -Destination (Join-Path $dest 'invoke-openworker-control-envelope-v1.ps1') -Force

# Verify the deployed files before touching runner configuration.
$deployed=@(
  (Join-Path $dest 'openworker-job-started-hook.ps1'),
  (Join-Path $dest 'openworker-job-started.cmd'),
  (Join-Path $dest 'invoke-openworker-control-envelope-v1.ps1')
)
foreach($path in $deployed){
  if(-not(Test-Path -LiteralPath $path -PathType Leaf)){throw "deployed hook file missing: $path"}
}

$hookPath='C:\ProgramData\OpenWorker\hooks\openworker-job-started.cmd'
$backup=$envFile+'.openworker-hook-backup-'+[DateTimeOffset]::Now.ToString('yyyyMMdd-HHmmss')
Copy-Item -LiteralPath $envFile -Destination $backup -Force

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

$tmp=$envFile+'.tmp.'+[Guid]::NewGuid().ToString('N')
[IO.File]::WriteAllLines($tmp,$out,[Text.UTF8Encoding]::new($false))
Move-Item -LiteralPath $tmp -Destination $envFile -Force

# Re-read the file so a malformed update fails before reporting success.
$configured=@(Get-Content -LiteralPath $envFile | Where-Object {$_ -eq ('ACTIONS_RUNNER_HOOK_JOB_STARTED='+$hookPath)})
if($configured.Count -ne 1){throw "runner hook configuration verification failed in $envFile"}

Write-Output ([ordered]@{
  schema='openworker.runner-hook-install.v2'
  runner_root=$RunnerRoot
  env_file=$envFile
  backup=$backup
  hook=$hookPath
  dispatcher='C:\ProgramData\OpenWorker\hooks\invoke-openworker-control-envelope-v1.ps1'
  installed=$true
  configuration_verified=$true
  restart_required=$true
} | ConvertTo-Json -Depth 5)
