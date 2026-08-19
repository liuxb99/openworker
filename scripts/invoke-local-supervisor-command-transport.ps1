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

$ctl=Join-Path $env:ProgramData 'OpenWorker\bin\openworkerctl.exe'
if(-not(Test-Path -LiteralPath $ctl -PathType Leaf)){
  throw "openworkerctl is not installed: $ctl; deploy/install control plane first"
}

$args=@()
switch($Command){
  'supervisor_status' { $args=@('supervisor','status') }
  'case_status'       { $args=@('case','status','0005') }
  'case_continue'     { $args=@('case','continue','0005') }
  'queue_clear'       { $args=@('queue','clear','DESKTOP-ODAQN0D') }
  default             { throw "unsupported command: $Command" }
}

$raw=& $ctl @args 2>&1 | Out-String
if($LASTEXITCODE -ne 0){
  throw "openworkerctl failed exit=$LASTEXITCODE output=$raw"
}
try{
  $result=$raw | ConvertFrom-Json -ErrorAction Stop
}catch{
  throw "openworkerctl returned non-JSON output: $raw"
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

if($Command -eq 'case_continue' -and -not(Test-Accepted $result)){
  throw "case_continue did not return accepted=true: $raw"
}

$receipt=[ordered]@{
  schema='openworker.command-transport.v1'
  transport='github_actions'
  request_id=if($RequestId){$RequestId}else{$env:GITHUB_RUN_ID}
  command=$Command
  case_id=if($Command -in @('case_status','case_continue')){'0005'}else{$null}
  machine='DESKTOP-ODAQN0D'
  accepted=$true
  github_run_id=$env:GITHUB_RUN_ID
  github_run_attempt=$env:GITHUB_RUN_ATTEMPT
  github_action_used_for_command_transport=$true
  github_action_used_for_business_execution=$false
  dispatched_at=[DateTimeOffset]::UtcNow.ToString('o')
  result=$result
}

$receipt | ConvertTo-Json -Depth 30
