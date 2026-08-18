param(
  [string]$OpenWorkerUrl='http://127.0.0.1:8787',
  [string]$WorkspaceRoot='D:\AI-Work\jobs\0003-YUJING-BRIDGE',
  [string]$Machine='DESKTOP-UL7V2VV',
  [string]$GoToolRoot=$env:GO_TOOL_ROOT,
  [string]$TerrainRoot=$env:TERRAIN_ROOT,
  [string]$CatalogPath='D:\TaiwanDTM\catalog\dtm_catalog.sqlite'
)
$ErrorActionPreference='Stop'
if(-not $env:COMPUTERNAME.Equals($Machine,[StringComparison]::OrdinalIgnoreCase)){throw "wrong host expected=$Machine actual=$env:COMPUTERNAME"}
if([string]::IsNullOrWhiteSpace($GoToolRoot)){throw 'GO_TOOL_ROOT/GoToolRoot is required'}
if([string]::IsNullOrWhiteSpace($TerrainRoot)){throw 'TERRAIN_ROOT/TerrainRoot is required'}
$scriptRoot=Split-Path -Parent $MyInvocation.MyCommand.Path
$evidenceDir=Join-Path $WorkspaceRoot 'evidence';New-Item -ItemType Directory -Force -Path $evidenceDir|Out-Null
function Read-Json([string]$Path){if(-not(Test-Path -LiteralPath $Path)){return $null};try{return Get-Content -LiteralPath $Path -Raw|ConvertFrom-Json}catch{return $null}}
function File-OK([string]$Path){return (Test-Path -LiteralPath $Path) -and (-not (Get-Item -LiteralPath $Path).PSIsContainer) -and ((Get-Item -LiteralPath $Path).Length -gt 0)}
function StreetView-OK{
  $m=Read-Json (Join-Path $WorkspaceRoot 'streetview\browser\streetview-browser-screenshots.json');if($null -eq $m -or -not $m.ok -or $m.schema_version -ne 'streetview-browser-screenshots/v2'){return $false}
  $r=@($m.renders);if($r.Count -ne 4){return $false};foreach($x in $r){if(-not(File-OK ([string]$x.path))){return $false}};return $true
}
function Ortho-OK{
  $e=Read-Json (Join-Path $WorkspaceRoot 'orthophoto\nlsc-photo2\orthophoto-photo2-evidence.json');if($null -eq $e -or -not $e.ok){return $false};return File-OK ([string]$e.output_path)
}
function Terrain-OK{
  $root=Join-Path $WorkspaceRoot 'terrain';$names=@('terrain-context.json','terrain-build.json','terrain-grid.json','terrain.dxf','terrain-heightmap.raw','terrain-heightmap.json','terrain.obj','terrain-mesh.json','terrain-scene.json','scenex-terrain-scene.json');foreach($n in $names){if(-not(File-OK (Join-Path $root $n))){return $false}};$c=Read-Json (Join-Path $root 'terrain-context.json');return $null-ne $c -and [int]$c.usable_tiles -gt 0
}
function Consumer-OK{
  $root=Join-Path $WorkspaceRoot 'consumer';$names=@('visual-frame-set.json','blender-reference-pack.json','minimax-h3-reference-pack.json','blender-visual-handoff.json','minimax-h3-visual-handoff.json','geo-context.json','consumer-orchestration.json');foreach($n in $names){if(-not(File-OK (Join-Path $root $n))){return $false}};$c=Read-Json (Join-Path $root 'consumer-orchestration.json');return $null-ne $c -and $c.schema_version -eq 'consumer-orchestration/v1'
}
function Blender-OK{
  $root=Join-Path $WorkspaceRoot 'blender';foreach($n in @('terrain-scene.blend','terrain-render.png','blender-execution-request.json','blender-scene-evidence.json','blender-render-handoff.json')){if(-not(File-OK (Join-Path $root $n))){return $false}};$e=Read-Json (Join-Path $root 'blender-scene-evidence.json');$h=Read-Json (Join-Path $root 'blender-render-handoff.json');return $null-ne $e -and $null-ne $h -and $e.schema_version -eq 'blender-scene-evidence/v1' -and $h.schema_version -eq 'blender-render-handoff/v1'
}
$node=Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/node/status";$agents=Invoke-RestMethod -Method Get -Uri "$OpenWorkerUrl/v1/cluster/agents"
$before=[ordered]@{streetview=(StreetView-OK);orthophoto=(Ortho-OK);terrain=(Terrain-OK);consumer=(Consumer-OK);blender=(Blender-OK)}
$submitted=@()
if(-not($before.streetview -and $before.orthophoto)){
  & (Join-Path $scriptRoot 'case0003_local_imagery_parallel.ps1') -OpenWorkerUrl $OpenWorkerUrl -WorkspaceRoot $WorkspaceRoot -Machine $Machine -GoToolRoot $GoToolRoot -TerrainRoot $TerrainRoot
  $submitted+='imagery_parallel'
}
if(-not $before.terrain){
  if(Test-Path -LiteralPath $CatalogPath){
    & (Join-Path $scriptRoot 'case0003_local_terrain_aoi.ps1') -OpenWorkerUrl $OpenWorkerUrl -WorkspaceRoot $WorkspaceRoot -Machine $Machine -GoToolRoot $GoToolRoot -TerrainRoot $TerrainRoot -CatalogPath $CatalogPath
    $submitted+='terrain_aoi'
  } else {Write-Warning "DTM catalog missing; AOI not submitted: $CatalogPath"}
}
$afterImmediate=[ordered]@{streetview=(StreetView-OK);orthophoto=(Ortho-OK);terrain=(Terrain-OK);consumer=(Consumer-OK);blender=(Blender-OK)}
if($afterImmediate.streetview -and $afterImmediate.orthophoto -and $afterImmediate.terrain -and -not $afterImmediate.consumer){
  & (Join-Path $scriptRoot 'case0003_local_consumer.ps1') -OpenWorkerUrl $OpenWorkerUrl -WorkspaceRoot $WorkspaceRoot -Machine $Machine -GoToolRoot $GoToolRoot -TerrainRoot $TerrainRoot
  $submitted+='consumer'
}
$afterConsumer=[ordered]@{streetview=(StreetView-OK);orthophoto=(Ortho-OK);terrain=(Terrain-OK);consumer=(Consumer-OK);blender=(Blender-OK)}
if($afterConsumer.consumer -and -not $afterConsumer.blender){
  & (Join-Path $scriptRoot 'case0003_local_blender.ps1') -OpenWorkerUrl $OpenWorkerUrl -WorkspaceRoot $WorkspaceRoot -Machine $Machine -GoToolRoot $GoToolRoot -TerrainRoot $TerrainRoot
  $submitted+='blender'
}
$receipt=[ordered]@{schema='openworker/case0003-local-continue/v1';case_id='0003';machine=$Machine;workspace_root=$WorkspaceRoot;transport='openworker-local-first';github_business_transport=$false;checked_at=[DateTimeOffset]::UtcNow.ToString('o');node=$node;agents=$agents;gates_before=$before;gates_after_submission=$afterConsumer;submitted=$submitted;next_boundary=if((Blender-OK)){'SCENEX_REAL_IMPORT_REQUIRED'}else{'LOCAL_JOBS_AND_PHYSICAL_QC_REQUIRED'}}
$path=Join-Path $evidenceDir 'case0003-local-continue.json';$receipt|ConvertTo-Json -Depth 12|Set-Content -LiteralPath $path -Encoding utf8
$receipt|ConvertTo-Json -Depth 12|Write-Host
