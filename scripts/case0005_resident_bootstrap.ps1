param(
  [string]$OpenWorkerUrl = 'http://127.0.0.1:8787',
  [string]$WorkspaceRoot = 'D:\AI-Work\jobs\0005-SNOW-WHITE',
  [string]$Machine = 'DESKTOP-ODAQN0D',
  [string]$ResidentRoot = 'D:\AI-Work\runtime\openworker'
)
$ErrorActionPreference='Stop'
$stage='start'
$started=[DateTimeOffset]::UtcNow.ToString('o')
$outcomePath='C:\ProgramData\OpenWorker\node\case0005-last-bootstrap-outcome.json'
$checks=[ordered]@{}

function Save-Outcome([bool]$Succeeded,[string]$Reason,$RawResponse=$null,$Ack=$null){
  $dir=Split-Path $outcomePath
  New-Item -ItemType Directory -Force -Path $dir | Out-Null
  $o=[ordered]@{
    schema='openworker/case0005-bootstrap-script-outcome/v4'
    case_id='0005'
    machine=$env:COMPUTERNAME
    workspace_root=$WorkspaceRoot
    resident_root=$ResidentRoot
    succeeded=$Succeeded
    stage=$stage
    reason=$Reason
    raw_openworker_response=$RawResponse
    ack=$Ack
    checks=$checks
    started_at=$started
    observed_at=[DateTimeOffset]::UtcNow.ToString('o')
    next_action=if($Succeeded){'continue with OpenWorker local supervisor'}else{'repair the reported stage/reason, then retry bootstrap only'}
  }
  $o|ConvertTo-Json -Depth 30|Set-Content -LiteralPath $outcomePath -Encoding utf8
  $o|ConvertTo-Json -Depth 30
}

try {
  $stage='verify_machine'
  $checks.expected_machine=$Machine
  $checks.actual_machine=$env:COMPUTERNAME
  if($env:COMPUTERNAME -ine $Machine){ throw "wrong host expected=$Machine actual=$env:COMPUTERNAME" }

  $stage='resolve_source'
  $source=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
  $checks.source_root=$source

  $stage='query_node_status'
  $node=Invoke-RestMethod "$OpenWorkerUrl/v1/node/status"
  $checks.node_online=[bool]$node.online
  $checks.node_machine=[string]$node.machine
  $checks.node_max_workers=[int]$node.max_workers
  $checks.node_running_commit=[string]$node.service.running_commit
  if(-not $node.online){ throw 'resident OpenWorker offline' }
  if($node.machine -ine $Machine){ throw "resident node mismatch $($node.machine)" }
  if([int]$node.max_workers -lt 4){ throw "resident node max_workers=$($node.max_workers), expected >=4" }

  $stage='sync_resident_runtime'
  New-Item -ItemType Directory -Force -Path $ResidentRoot | Out-Null
  foreach($name in @('coworker','case-worklists','case-specs')){
    $src=Join-Path $source $name
    $dst=Join-Path $ResidentRoot $name
    if(-not(Test-Path -LiteralPath $src)){ throw "missing runtime source $src" }
    if(Test-Path -LiteralPath $dst){ Remove-Item -LiteralPath $dst -Recurse -Force }
    Copy-Item -LiteralPath $src -Destination $dst -Recurse -Force
  }
  $pyproject=Join-Path $source 'pyproject.toml'
  if(Test-Path -LiteralPath $pyproject){ Copy-Item -LiteralPath $pyproject -Destination (Join-Path $ResidentRoot 'pyproject.toml') -Force }
  $checks.resident_root_exists=Test-Path -LiteralPath $ResidentRoot -PathType Container
  $checks.manifest_exists=Test-Path -LiteralPath (Join-Path $ResidentRoot 'case-worklists\0005.json') -PathType Leaf
  $checks.spec_exists=Test-Path -LiteralPath (Join-Path $ResidentRoot 'case-specs\0005.json') -PathType Leaf

  function Resolve-RepoRoot([string]$Name,[string[]]$Markers){
    $candidates=@(
      (Join-Path 'D:\actions-runner\_work' "$Name\$Name"),
      (Join-Path 'C:\github-runners' "$Name\_work\$Name\$Name"),
      (Join-Path 'C:\github-runners' $Name),
      (Join-Path 'D:\AI' $Name),
      (Join-Path 'D:\AIWork' $Name),
      (Join-Path 'D:\PyWork' $Name)
    )
    foreach($c in $candidates){
      if(-not(Test-Path -LiteralPath $c -PathType Container)){continue}
      $ok=$true; foreach($m in $Markers){if(-not(Test-Path -LiteralPath (Join-Path $c $m))){$ok=$false;break}}
      if($ok){return (Resolve-Path $c).Path}
    }
    foreach($base in @('C:\github-runners','D:\actions-runner\_work')){
      if(-not(Test-Path -LiteralPath $base -PathType Container)){continue}
      $dirs=Get-ChildItem -LiteralPath $base -Directory -Recurse -ErrorAction SilentlyContinue | Where-Object {$_.Name -ieq $Name} | Select-Object -First 20
      foreach($d in $dirs){
        $ok=$true; foreach($m in $Markers){if(-not(Test-Path -LiteralPath (Join-Path $d.FullName $m))){$ok=$false;break}}
        if($ok){return $d.FullName}
      }
    }
    throw "local checkout not found for $Name"
  }
  function Resolve-RepoRootAlias([string[]]$Names,[string[]]$Markers){
    foreach($name in $Names){try{return Resolve-RepoRoot $name $Markers}catch{}}
    throw "local checkout not found for aliases=$($Names -join ',')"
  }
  function Resolve-GoToolAuthority(){
    $deploy='C:\ProgramData\go-tool-runtime\work-agent'
    $required=@('gtr-local-exec.exe','gtr-work-agent.exe','gtr-work-executor.exe','local-queue-authority.json')
    if(Test-Path -LiteralPath $deploy -PathType Container){
      $ok=$true;foreach($m in $required){if(-not(Test-Path -LiteralPath (Join-Path $deploy $m) -PathType Leaf)){$ok=$false;break}}
      if($ok){return (Resolve-Path $deploy).Path}
    }
    return Resolve-RepoRoot 'go-tool-runtime' @('go.mod','cmd\gtr-local-exec\main.go')
  }

  $stage='resolve_tool_roots'
  $envMap=@{
    GO_TOOL_ROOT=(Resolve-GoToolAuthority)
    COMFYX_ROOT=(Resolve-RepoRoot 'ComfyX' @('go.mod','cmd\comfyx-synthesis-video-real'))
    COMFYX_STUDIO_ROOT=(Resolve-RepoRoot 'Comfyx-Studio' @('go.mod','cmd\operator-director-preproduction'))
    OPENMAIC_ROOT=(Resolve-RepoRootAlias @('OpenMAIC','openmaic-fork') @('package.json','src\cli\presentation.ts'))
  }
  $goToolExe=Join-Path $envMap.GO_TOOL_ROOT 'gtr-local-exec.exe'
  if(Test-Path -LiteralPath $goToolExe -PathType Leaf){$envMap.GTR_LOCAL_EXEC_EXE=$goToolExe}
  $checks.tool_roots=$envMap
  $checks.go_tool_authority_kind=if($envMap.GTR_LOCAL_EXEC_EXE){'deployed-runtime-exe'}else{'source-checkout'}
  if($checks.go_tool_authority_kind -eq 'deployed-runtime-exe' -and -not(Test-Path -LiteralPath $envMap.GTR_LOCAL_EXEC_EXE -PathType Leaf)){throw 'deployed GTR_LOCAL_EXEC_EXE authority missing'}

  $stage='resolve_comfyui_output'
  foreach($p in @('D:\Comfy-Desktop\ComfyUI-Installs\ComfyUI\ComfyUI\output','D:\ComfyUI\output')){
    if(Test-Path -LiteralPath $p -PathType Container){$envMap.COMFYX_COMFYUI_OUTPUT_ROOT=$p;break}
  }
  if(-not $envMap.COMFYX_COMFYUI_OUTPUT_ROOT){throw 'COMFYX_COMFYUI_OUTPUT_ROOT not found on ODA'}
  $checks.comfyui_output=$envMap.COMFYX_COMFYUI_OUTPUT_ROOT

  $stage='post_case_bootstrap'
  $body=@{
    case_id='0005'
    machine=$Machine
    workspace_root=$WorkspaceRoot
    openworker_root=$ResidentRoot
    controller_module='coworker.case0005_controller'
    manifest_path='case-worklists/0005.json'
    spec_path='case-specs/0005.json'
    env=$envMap
  }|ConvertTo-Json -Depth 10

  $ack=$null
  try {
    $ack=Invoke-RestMethod -Method Post "$OpenWorkerUrl/v1/cases/bootstrap" -ContentType 'application/json' -Body $body
  } catch {
    $raw=$null
    if($_.ErrorDetails -and $_.ErrorDetails.Message){$raw=$_.ErrorDetails.Message}
    if(-not $raw){$raw=$_.Exception.Message}
    Save-Outcome $false "OpenWorker bootstrap HTTP request failed" $raw $null
    exit 1
  }

  $stage='verify_ack'
  if(-not $ack.job.accepted){throw 'Case 0005 bootstrap did not receive durable ACK'}
  if($ack.machine -ine $Machine){throw "bootstrap ACK machine=$($ack.machine)"}
  $checks.workspace_created=[bool]$ack.workspace_created
  $checks.workspace_exists=Test-Path -LiteralPath $WorkspaceRoot -PathType Container
  $checks.dot_openworker_exists=Test-Path -LiteralPath (Join-Path $WorkspaceRoot '.openworker') -PathType Container

  $stage='write_workspace_receipt'
  $evidence=Join-Path $WorkspaceRoot 'evidence'
  New-Item -ItemType Directory -Force -Path $evidence | Out-Null
  $receipt=[ordered]@{
    schema='openworker/case0005-resident-bootstrap/v4';case_id='0005';machine=$Machine;workspace_root=$WorkspaceRoot;
    resident_root=$ResidentRoot;transport='go-tool-lan-hostname';target_queue_url="http://$Machine`:8848";business_execution='resident-openworker-local-supervisor';github_action_used_for_business_execution=$false;
    node=$node;ack=$ack;tool_roots=$envMap;submitted_at=[DateTimeOffset]::UtcNow.ToString('o')
  }
  $receipt|ConvertTo-Json -Depth 20|Set-Content -LiteralPath (Join-Path $evidence 'case0005-resident-bootstrap.json') -Encoding utf8
  $stage='completed'
  Save-Outcome $true '' $ack $ack
  exit 0
} catch {
  Save-Outcome $false $_.Exception.Message $null $null
  exit 1
}
