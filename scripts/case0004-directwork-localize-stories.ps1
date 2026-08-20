param([Parameter(Mandatory=$true)][string]$RequestId)
$ErrorActionPreference='Stop'
Set-StrictMode -Version Latest
if($env:COMPUTERNAME -ine 'DESKTOP-O87PJNR'){throw "CASE0004_WRONG_HOST actual=$env:COMPUTERNAME"}
$workspace='D:\AI-Work\jobs\0004-DWG-TO-3D'
$evidence=Join-Path $workspace ('evidence\directwork\'+$RequestId)
New-Item -ItemType Directory -Force -Path $evidence|Out-Null
$pointer=Join-Path $env:ProgramData 'go-tool-runtime\work-agent\authorities\dwg-todo-current.json'
if(-not(Test-Path -LiteralPath $pointer -PathType Leaf)){throw "DWG_AUTHORITY_POINTER_MISSING path=$pointer"}
$authority=Get-Content -LiteralPath $pointer -Raw|ConvertFrom-Json
$invoke=Join-Path ([string]$authority.root) 'scripts\invoke-agent-cad-local.ps1'
if(-not(Test-Path -LiteralPath $invoke -PathType Leaf)){throw "DWG_LOCAL_WRAPPER_MISSING path=$invoke"}

# This is a zoom request, not a story assignment. Bounds come from REAL overview text/block
# evidence around the stacked plan-like sheets. Do not label any story until visual review.
$params=[ordered]@{
  name=('case0004-story-relocalize-'+$RequestId)
  width_px=3000
  height_px=5000
  bounds=[ordered]@{min_x=46400.0;min_y=51000.0;max_x=50800.0;max_y=63100.0}
}
$paramsPath=Join-Path $evidence 'relocalize-render-params.json'
[IO.File]::WriteAllText($paramsPath,($params|ConvertTo-Json -Depth 20)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$paramsJson=$params|ConvertTo-Json -Depth 20 -Compress
$result=& {
  param($invokePath,$json,$root,$id)
  Set-StrictMode -Off
  & $invokePath -Method 'cad.render_png' -ParamsJson $json -WorkspaceRoot $root -WorkId $id
} $invoke $paramsJson $workspace ('directwork-case0004-localize-'+$RequestId)
if($LASTEXITCODE -ne 0){throw "CASE0004_LOCALIZE_RENDER_FAILED exit=$LASTEXITCODE"}
$text=($result -join "`n")
$out=Join-Path $evidence 'relocalize-render.stdout.json'
[IO.File]::WriteAllText($out,$text+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$parsed=$text|ConvertFrom-Json
$summary=[ordered]@{schema='case0004.directwork.story-relocalize.v1';case_id='0004';request_id=$RequestId;status='succeeded';machine=$env:COMPUTERNAME;authority_commit=[string]$authority.commit;render=$parsed;params_sha256=(Get-FileHash $paramsPath -Algorithm SHA256).Hash.ToLowerInvariant();completed_at=[DateTimeOffset]::UtcNow.ToString('o')}
[IO.File]::WriteAllText((Join-Path $evidence 'final.json'),($summary|ConvertTo-Json -Depth 60)+[Environment]::NewLine,[Text.UTF8Encoding]::new($false))
$summary|ConvertTo-Json -Depth 60 -Compress
