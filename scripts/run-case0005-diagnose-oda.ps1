$ErrorActionPreference='Stop'

if($env:COMPUTERNAME -ine 'DESKTOP-ODAQN0D'){throw "wrong host $env:COMPUTERNAME"}
$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworkerctl.exe'
if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){throw "openworkerctl missing: $ctl"}

$raw=& $ctl case diagnose 0005 2>&1 | Out-String
$exitCode=$LASTEXITCODE
$result=[ordered]@{
  schema='openworker.case0005-diagnose-result/v1'
  case_id='0005'
  machine=$env:COMPUTERNAME
  runner_name=$env:RUNNER_NAME
  accepted=($exitCode -eq 0)
  exit_code=$exitCode
  error=''
  github_run_id=$env:GITHUB_RUN_ID
  github_run_attempt=$env:GITHUB_RUN_ATTEMPT
  github_action_used_for_business_execution=$false
  observed_at=[DateTimeOffset]::UtcNow.ToString('o')
  diagnosis=$null
}
if($exitCode -eq 0){
  try{$result.diagnosis=$raw|ConvertFrom-Json -ErrorAction Stop}catch{$result.accepted=$false;$result.exit_code=70;$result.error="non-JSON diagnose output: $raw"}
}else{
  $result.error=$raw.Trim()
}

$requestId="diagnose-$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
$rel="case-evidence/case0005-diagnose/$requestId.json"
$path=Join-Path $repoRoot $rel
New-Item -ItemType Directory -Force -Path (Split-Path $path -Parent)|Out-Null
$json=$result|ConvertTo-Json -Depth 50
[IO.File]::WriteAllText($path,$json+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
Write-Host ($result|ConvertTo-Json -Depth 50 -Compress)

Push-Location $repoRoot
try{
  git config user.name 'openworker-case-diagnose'
  git config user.email 'openworker-case-diagnose@users.noreply.github.com'
  git add -- $rel
  git commit -m "receipt: Case0005 diagnose $requestId"
  if($LASTEXITCODE -ne 0){throw 'failed to commit diagnose receipt'}
  for($i=0;$i -lt 3;$i++){
    git pull --rebase origin main
    if($LASTEXITCODE -eq 0){
      git push origin HEAD:main
      if($LASTEXITCODE -eq 0){break}
    }else{git rebase --abort 2>$null}
    if($i -eq 2){throw 'failed to publish diagnose receipt'}
    Start-Sleep -Seconds 2
  }
}finally{Pop-Location}

if(-not $result.accepted){exit 1}
exit 0
