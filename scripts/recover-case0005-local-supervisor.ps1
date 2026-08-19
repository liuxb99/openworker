param(
    [string]$GoToolRoot = 'C:\github-runners\go-tool-runtime\_work\go-tool-runtime\go-tool-runtime'
)
$ErrorActionPreference='Stop'
if($env:COMPUTERNAME -ine 'DESKTOP-ODAQN0D'){ throw "wrong host $env:COMPUTERNAME" }
if(-not(Test-Path -LiteralPath (Join-Path $GoToolRoot '.git') -PathType Container)){ throw "go-tool checkout missing: $GoToolRoot" }
Push-Location $GoToolRoot
try {
    $dirty=& git status --porcelain
    if($LASTEXITCODE -ne 0){ throw 'go-tool git status failed' }
    if($dirty){ throw "refuse to overwrite dirty go-tool checkout: $GoToolRoot" }
    & git fetch origin main
    if($LASTEXITCODE -ne 0){ throw 'go-tool fetch main failed' }
    & git checkout main
    if($LASTEXITCODE -ne 0){ throw 'go-tool checkout main failed' }
    & git reset --hard origin/main
    if($LASTEXITCODE -ne 0){ throw 'go-tool reset to origin/main failed' }
} finally { Pop-Location }
$activation=Join-Path $PSScriptRoot 'activate-case0005-local-supervisor.ps1'
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $activation -SkipCodeSync
if($LASTEXITCODE -ne 0){ throw "Case0005 local supervisor activation failed exit=$LASTEXITCODE" }
