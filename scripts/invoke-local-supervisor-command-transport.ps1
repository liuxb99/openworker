param(
  [Parameter(Mandatory=$true)]
  [ValidateSet('supervisor_status','case_status','case_continue','queue_clear')]
  [string]$Command,
  [string]$RequestId = '',
  [string]$ExpectedMachine = 'DESKTOP-ODAQN0D'
)

$ErrorActionPreference='Stop'

if($env:COMPUTERNAME -ine $ExpectedMachine){
  throw "wrong host $env:COMPUTERNAME expected=$ExpectedMachine"
}
if($ExpectedMachine -ine 'DESKTOP-ODAQN0D'){
  throw "unsupported machine $ExpectedMachine"
}
if([string]::IsNullOrWhiteSpace($RequestId)){
  $RequestId="$env:GITHUB_RUN_ID-$env:GITHUB_RUN_ATTEMPT"
}
if($RequestId -notmatch '^[A-Za-z0-9._-]{8,128}$'){
  throw "invalid request id: $RequestId"
}

$cacheRoot=Join-Path $env:ProgramData 'OpenWorker\command-transport\receipts'
New-Item -ItemType Directory -Force -Path $cacheRoot | Out-Null
$cachePath=Join-Path $cacheRoot ($RequestId + '.json')
if(Test-Path -LiteralPath $cachePath -PathType Leaf){
  Get-Content -LiteralPath $cachePath -Raw
  exit 0
}

$ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworkerctl.exe'
$cliArgs=@()
switch($Command){
  'supervisor_status' { $cliArgs=@('supervisor','status') }
  'case_status'       { $cliArgs=@('case','status','0005') }
  'case_continue'     { $cliArgs=@('case','continue','0005') }
  'queue_clear'       { $cliArgs=@('queue','clear','DESKTOP-ODAQN0D') }
  default             { throw "unsupported command: $Command" }
}

function Test-Accepted($Value){
  if($null -eq $Value){ return $false }
  if($Value -is [bool]){ return $Value }
  if($Value -is [System.Collections.IDictionary]){
    foreach($k in $Value.Keys){
      if(([string]$k -ieq 'accepted') -and ($Value[$k] -eq $true)){ return $true }
      if(Test-Accepted $Value[$k]){ return $true }
    }
    return $false
  }
  if($Value -is [pscustomobject]){
    foreach($p in $Value.PSObject.Properties){
      if(($p.Name -ieq 'accepted') -and ($p.Value -eq $true)){ return $true }
      if(Test-Accepted $p.Value){ return $true }
    }
    return $false
  }
  if(($Value -is [System.Collections.IEnumerable]) -and -not($Value -is [string])){
    foreach($item in $Value){ if(Test-Accepted $item){ return $true } }
  }
  return $false
}

$result=$null
$errorText=''
$exitCode=0
$started=[DateTimeOffset]::UtcNow

if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){
  $exitCode=127
  $errorText="openworkerctl is not installed: $ctl; deploy/install control plane first"
}else{
  try{
    $raw=& $ctl @cliArgs 2>&1 | Out-String
    $exitCode=$LASTEXITCODE
    if($exitCode -ne 0){
      $errorText="openworkerctl failed exit=$exitCode output=$raw"
    }else{
      try{ $result=$raw | ConvertFrom-Json -ErrorAction Stop }
      catch{
        $exitCode=70
        $errorText="openworkerctl returned non-JSON output: $raw"
      }
    }
  }catch{
    $exitCode=71
    $errorText=$_.Exception.Message
  }
}

$accepted=($exitCode -eq 0)
if($accepted -and $Command -eq 'case_continue'){
  $accepted=Test-Accepted $result
  if(-not $accepted){
    $exitCode=72
    $errorText='case_continue did not return accepted=true'
  }
}

$receipt=[ordered]@{
  schema='openworker.command-transport.v1'
  transport='github_actions'
  request_id=$RequestId
  command=$Command
  case_id=if($Command -in @('case_status','case_continue')){'0005'}else{$null}
  machine='DESKTOP-ODAQN0D'
  accepted=$accepted
  exit_code=$exitCode
  error=$errorText
  github_run_id=$env:GITHUB_RUN_ID
  github_run_attempt=$env:GITHUB_RUN_ATTEMPT
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  business_completion_claimed=$false
  authoritative_business_state='openworker'
  started_at=$started.ToString('o')
  dispatched_at=[DateTimeOffset]::UtcNow.ToString('o')
  result=$result
}

$json=$receipt | ConvertTo-Json -Depth 40
[IO.File]::WriteAllText($cachePath,$json+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$json
