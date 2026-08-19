param(
 [string]$InstallRoot = "$env:ProgramData\OpenWorker\bin"
)
$ErrorActionPreference='Stop'
$repoRoot=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$goRoot=Join-Path $repoRoot 'go-runtime'
if(-not(Test-Path -LiteralPath (Join-Path $goRoot 'go.mod') -PathType Leaf)){throw "go-runtime module missing: $goRoot"}
New-Item -ItemType Directory -Force -Path $InstallRoot|Out-Null
$target=Join-Path $InstallRoot 'openworkerctl.exe'
Push-Location $goRoot
try{
 & go test ./cmd/openworkerctl -count=1
 if($LASTEXITCODE-ne 0){throw "openworkerctl tests failed: $LASTEXITCODE"}
 & go build -trimpath -o $target ./cmd/openworkerctl
 if($LASTEXITCODE-ne 0){throw "openworkerctl build failed: $LASTEXITCODE"}
}finally{Pop-Location}
$shim=Join-Path $InstallRoot 'openworkerctl.cmd'
[IO.File]::WriteAllText($shim,"@echo off`r`n\"$target\" %*`r`n",[Text.UTF8Encoding]::new($false))
$result=[ordered]@{schema='openworkerctl-install/v1';status='installed';machine=$env:COMPUTERNAME;exe=$target;shim=$shim;server='http://127.0.0.1:8848';github_action_used_for_business_execution=$false;installed_at=[DateTime]::UtcNow.ToString('o')}
$result|ConvertTo-Json -Depth 5
