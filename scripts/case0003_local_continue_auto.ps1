param(
  [string]$OpenWorkerUrl='http://127.0.0.1:8787',
  [string]$WorkspaceRoot='D:\AI-Work\jobs\0003-YUJING-BRIDGE',
  [string]$Machine='DESKTOP-UL7V2VV',
  [string]$OpenWorkerRoot='',
  [string]$DriveSyncRoot=$env:OPENWORKER_REVIEW_DRIVE_ROOT,
  [string]$GoToolRoot='',
  [string]$TerrainRoot='',
  [string]$SceneXRoot='',
  [string]$EngineeringOSRoot='',
  [string]$OSProjectId=$env:ENGINEERING_OS_PROJECT_ID,
  [string]$OSJobId=$env:ENGINEERING_OS_JOB_ID,
  [string]$EngineeringOSBaseUrl='http://127.0.0.1:8080',
  [string]$CatalogPath='D:\TaiwanDTM\catalog\dtm_catalog.sqlite'
)
$ErrorActionPreference='Stop'
if(-not $env:COMPUTERNAME.Equals($Machine,[StringComparison]::OrdinalIgnoreCase)){throw "wrong host expected=$Machine actual=$env:COMPUTERNAME"}
$scriptRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
if([string]::IsNullOrWhiteSpace($OpenWorkerRoot)){$OpenWorkerRoot=(Split-Path -Parent $scriptRoot)}
$controller=Join-Path $OpenWorkerRoot 'scripts\case0003_local_continue.ps1'
if(-not(Test-Path -LiteralPath $controller -PathType Leaf)){throw "canonical Case 0003 controller missing: $controller"}
$node=Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/node/status" -TimeoutSec 10
if([string]$node.node_id -and -not ([string]$node.node_id).Equals($Machine,[StringComparison]::OrdinalIgnoreCase) -and -not ([string]$node.machine).Equals($Machine,[StringComparison]::OrdinalIgnoreCase)){throw "OpenWorker node identity mismatch expected=$Machine node_id=$($node.node_id) machine=$($node.machine)"}
function Inventory-Root([string]$EnvName){
  foreach($r in @($node.inventory.roots)){
    if(([string]$r.env).Equals($EnvName,[StringComparison]::OrdinalIgnoreCase) -and [bool]$r.available -and -not[string]::IsNullOrWhiteSpace([string]$r.path)){
      if(Test-Path -LiteralPath ([string]$r.path) -PathType Container){return [string]$r.path}
    }
  }
  return ''
}
function Resolve-Root([string]$Explicit,[string]$EnvName){
  if(-not[string]::IsNullOrWhiteSpace($Explicit)){
    if(-not(Test-Path -LiteralPath $Explicit -PathType Container)){throw "$EnvName explicit root unavailable: $Explicit"}
    return (Resolve-Path -LiteralPath $Explicit).Path
  }
  $fromInventory=Inventory-Root $EnvName
  if(-not[string]::IsNullOrWhiteSpace($fromInventory)){return (Resolve-Path -LiteralPath $fromInventory).Path}
  $envValue=[Environment]::GetEnvironmentVariable($EnvName)
  if(-not[string]::IsNullOrWhiteSpace($envValue) -and (Test-Path -LiteralPath $envValue -PathType Container)){return (Resolve-Path -LiteralPath $envValue).Path}
  throw "$EnvName root unavailable from explicit parameter, OpenWorker inventory, or environment"
}
$GoToolRoot=Resolve-Root $GoToolRoot 'GO_TOOL_ROOT'
$TerrainRoot=Resolve-Root $TerrainRoot 'TERRAIN_ROOT'
$SceneXRoot=Resolve-Root $SceneXRoot 'SCENEX_ROOT'
$EngineeringOSRoot=Resolve-Root $EngineeringOSRoot 'ENGINEERING_OS_ROOT'
if(-not(Test-Path -LiteralPath $OpenWorkerRoot -PathType Container)){throw "OPENWORKER_ROOT unavailable: $OpenWorkerRoot"}
$resolved=[ordered]@{
  schema='openworker/case0003-root-resolution/v1';case_id='0003';machine=$Machine;source='explicit>openworker-inventory>environment';
  openworker_root=$OpenWorkerRoot;go_tool_root=$GoToolRoot;terrain_root=$TerrainRoot;scenex_root=$SceneXRoot;engineering_os_root=$EngineeringOSRoot
}
$evidenceDir=Join-Path $WorkspaceRoot 'evidence';New-Item -ItemType Directory -Force -Path $evidenceDir|Out-Null
$resolved|ConvertTo-Json -Depth 6|Set-Content -LiteralPath (Join-Path $evidenceDir 'case0003-root-resolution.json') -Encoding utf8
& $controller -OpenWorkerUrl $OpenWorkerUrl -WorkspaceRoot $WorkspaceRoot -Machine $Machine -OpenWorkerRoot $OpenWorkerRoot -DriveSyncRoot $DriveSyncRoot -GoToolRoot $GoToolRoot -TerrainRoot $TerrainRoot -SceneXRoot $SceneXRoot -EngineeringOSRoot $EngineeringOSRoot -OSProjectId $OSProjectId -OSJobId $OSJobId -EngineeringOSBaseUrl $EngineeringOSBaseUrl -CatalogPath $CatalogPath
if($LASTEXITCODE -ne 0){exit $LASTEXITCODE}
