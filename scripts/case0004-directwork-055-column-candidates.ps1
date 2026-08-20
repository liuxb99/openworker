param([Parameter(Mandatory=$true)][string]$RequestId)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:COMPUTERNAME -ine 'DESKTOP-O87PJNR'){throw "CASE0004_WRONG_HOST actual=$env:COMPUTERNAME"}
$workspace='D:\AI-Work\jobs\0004-DWG-TO-3D'
$evidence=Join-Path $workspace ('evidence\directwork\'+$RequestId)
New-Item -ItemType Directory -Force -Path $evidence|Out-Null

$query=[ordered]@{
  session_id=('case0004-055-'+$RequestId)
  project='DWG_todo Case 0004'
  workspace_root=$workspace
  question='Confirm current contract for cad.list_story_column_candidates. This step is read-only candidate inventory; do not promote any handle or invent column authority.'
  task='Provide method guidance only for Case0004 step 0004-055.'
}
try{$goTool=Invoke-RestMethod -Method POST -Uri 'http://127.0.0.1:8848/agent/query' -ContentType 'application/json' -Body ($query|ConvertTo-Json -Depth 20) -TimeoutSec 60}catch{$goTool=[ordered]@{error=$_.Exception.Message}}
[IO.File]::WriteAllText((Join-Path $evidence 'go-tool-query.json'),($goTool|ConvertTo-Json -Depth 80)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))

$pointer=Join-Path $env:ProgramData 'go-tool-runtime\work-agent\authorities\dwg-todo-current.json'
if(-not(Test-Path -LiteralPath $pointer -PathType Leaf)){throw "DWG_AUTHORITY_POINTER_MISSING path=$pointer"}
$authority=Get-Content -LiteralPath $pointer -Raw|ConvertFrom-Json
$authorityRoot=[string]$authority.root
$invoke=Join-Path $authorityRoot 'scripts\invoke-agent-cad-local.ps1'
if(-not(Test-Path -LiteralPath $invoke -PathType Leaf)){throw "DWG_LOCAL_WRAPPER_MISSING path=$invoke"}

$stories=@('1F','2F','3F','4F','R1F')
$inventories=@()
foreach($story in $stories){
  $getParams=[ordered]@{story_id=$story}
  $getJson=$getParams|ConvertTo-Json -Compress
  $get=& {param($p,$j,$root,$id) Set-StrictMode -Off; & $p -Method 'cad.get_story_region' -ParamsJson $j -WorkspaceRoot $root -WorkId $id} $invoke $getJson $workspace ('directwork-case0004-055-region-'+$story.ToLowerInvariant()+'-'+$RequestId)
  if($LASTEXITCODE -ne 0){throw "CASE0004_055_REGION_GET_FAILED story=$story exit=$LASTEXITCODE"}
  $getText=($get -join "`n");$getObj=$getText|ConvertFrom-Json
  if([string]$getObj.result.story_region.review_status -ne 'confirmed'){throw "CASE0004_055_REGION_NOT_CONFIRMED story=$story"}

  $params=[ordered]@{story_id=$story;limit=500}
  $json=$params|ConvertTo-Json -Compress
  $out=& {param($p,$j,$root,$id) Set-StrictMode -Off; & $p -Method 'cad.list_story_column_candidates' -ParamsJson $j -WorkspaceRoot $root -WorkId $id} $invoke $json $workspace ('directwork-case0004-055-candidates-'+$story.ToLowerInvariant()+'-'+$RequestId)
  if($LASTEXITCODE -ne 0){throw "CASE0004_055_CANDIDATES_FAILED story=$story exit=$LASTEXITCODE"}
  $text=($out -join "`n")
  $path=Join-Path $evidence ($story.ToLowerInvariant()+'-column-candidates.stdout.json')
  [IO.File]::WriteAllText($path,$text+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
  $obj=$text|ConvertFrom-Json
  if([string]$obj.result.authority -ne 'none'){throw "CASE0004_055_UNEXPECTED_AUTHORITY story=$story authority=$($obj.result.authority)"}
  $inventories+=@([ordered]@{story_id=$story;candidate_count=[int]$obj.result.candidate_count;source_sha256=[string]$obj.result.source_sha256;story_region=$obj.result.story_region;receipt_path=$path;receipt_sha256=(Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant()})
}

$state=Join-Path $workspace 'dwg\agent-cad-state.json'
$summary=[ordered]@{
  schema='case0004.directwork.055.column-candidates.v1';case_id='0004';step='0004-055';request_id=$RequestId;status='succeeded';machine=$env:COMPUTERNAME
  authority_root=$authorityRoot;authority_commit=[string]$authority.commit
  source_story_region_work_id='dw-20260820T083831-efc1b644d6d5966c'
  inventory_count=$inventories.Count;inventories=$inventories;column_authority='none';visual_review_required=$true
  state_path=$state;state_sha256=(Get-FileHash -LiteralPath $state -Algorithm SHA256).Hash.ToLowerInvariant();completed_at=[DateTimeOffset]::UtcNow.ToString('o')
}
[IO.File]::WriteAllText((Join-Path $evidence 'final.json'),($summary|ConvertTo-Json -Depth 80)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$summary|ConvertTo-Json -Depth 80 -Compress
