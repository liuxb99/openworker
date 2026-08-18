param(
  [string]$RegistryPath=$env:OPENWORKER_MACHINE_ROOTS_FILE,
  [string]$OpenWorkerRoot=$env:OPENWORKER_ROOT,
  [string]$GoToolRoot=$env:GO_TOOL_ROOT,
  [string]$TerrainRoot=$env:TERRAIN_ROOT,
  [string]$SceneXRoot=$env:SCENEX_ROOT,
  [string]$EngineeringOSRoot=$env:ENGINEERING_OS_ROOT,
  [string]$DriveReviewRoot=$env:OPENWORKER_REVIEW_DRIVE_ROOT
)
$ErrorActionPreference='Stop'
if([string]::IsNullOrWhiteSpace($RegistryPath)){
  $base=$env:ProgramData
  if([string]::IsNullOrWhiteSpace($base)){throw 'ProgramData unavailable; pass -RegistryPath explicitly'}
  $RegistryPath=Join-Path $base 'OpenWorker\machine-roots.json'
}
$items=[ordered]@{
  OPENWORKER_ROOT=$OpenWorkerRoot
  GO_TOOL_ROOT=$GoToolRoot
  TERRAIN_ROOT=$TerrainRoot
  SCENEX_ROOT=$SceneXRoot
  ENGINEERING_OS_ROOT=$EngineeringOSRoot
  OPENWORKER_REVIEW_DRIVE_ROOT=$DriveReviewRoot
}
foreach($k in @($items.Keys)){
  $v=[string]$items[$k]
  if([string]::IsNullOrWhiteSpace($v)){continue}
  if(-not(Test-Path -LiteralPath $v -PathType Container)){throw "$k root unavailable: $v"}
  $items[$k]=(Resolve-Path -LiteralPath $v).Path
}
$filtered=[ordered]@{}
foreach($k in $items.Keys){if(-not[string]::IsNullOrWhiteSpace([string]$items[$k])){$filtered[$k]=[string]$items[$k]}}
if($filtered.Count -eq 0){throw 'no machine roots supplied'}
$parent=Split-Path -Parent $RegistryPath;New-Item -ItemType Directory -Force -Path $parent|Out-Null
$tmp="$RegistryPath.tmp"
$filtered|ConvertTo-Json -Depth 4|Set-Content -LiteralPath $tmp -Encoding utf8
Move-Item -Force -LiteralPath $tmp -Destination $RegistryPath
[ordered]@{schema='openworker/machine-roots/v1';machine=$env:COMPUTERNAME;registry_path=$RegistryPath;roots=$filtered}|ConvertTo-Json -Depth 6|Write-Host
