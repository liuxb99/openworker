param(
    [string]$Workspace = 'D:\AI-Work\jobs\0005-SNOW-WHITE',
    [string]$OpenWorkerRoot = '',
    [string]$GoToolRoot = '',
    [string]$PythonExe = '',
    [switch]$SkipCodeSync
)

$ErrorActionPreference = 'Stop'
$expectedHost = 'DESKTOP-ODAQN0D'
$actualHost = [Environment]::MachineName
if ($actualHost -ine $expectedHost) { throw "Case 0005 must activate on $expectedHost; actual=$actualHost" }

function Resolve-RepoRoot {
    param([string]$Explicit,[string[]]$Candidates,[string[]]$Markers,[string]$Name)
    $items = @(); if (-not [string]::IsNullOrWhiteSpace($Explicit)) { $items += $Explicit }; $items += $Candidates
    foreach ($candidate in $items) {
        if ([string]::IsNullOrWhiteSpace($candidate)) { continue }
        try { $root = (Resolve-Path -LiteralPath $candidate -ErrorAction Stop).Path } catch { continue }
        $valid = $true
        foreach ($marker in $Markers) { if (-not (Test-Path -LiteralPath (Join-Path $root $marker) -PathType Leaf)) { $valid = $false; break } }
        if ($valid) { return $root }
    }
    throw "$Name checkout not found"
}

function Resolve-Python([string]$Explicit) {
    $candidates = @(); if (-not [string]::IsNullOrWhiteSpace($Explicit)) { $candidates += $Explicit }
    $candidates += @('C:\Python314\python.exe','C:\Python313\python.exe','C:\Python312\python.exe','C:\Python311\python.exe','C:\Python310\python.exe')
    foreach ($candidate in $candidates) { if (Test-Path -LiteralPath $candidate -PathType Leaf) { return (Resolve-Path -LiteralPath $candidate).Path } }
    $cmd = Get-Command python.exe -ErrorAction SilentlyContinue; if ($null -ne $cmd) { return $cmd.Source }
    throw 'Python executable not found'
}

$OpenWorkerRoot = Resolve-RepoRoot -Explicit $OpenWorkerRoot -Name 'OpenWorker' -Markers @('case-specs\0005.json','coworker\case0005_verified_local_controller.py') -Candidates @(
    'C:\github-runners\openworker\_work\openworker\openworker','D:\AI\openworker','D:\AIWork\openworker','D:\PyWork\openworker'
)
$GoToolRoot = Resolve-RepoRoot -Explicit $GoToolRoot -Name 'go-tool-runtime' -Markers @('go.mod','scripts\windows\install-and-verify-true-local-supervisor.ps1','scripts\windows\verify-gtr-true-local-supervisor.ps1') -Candidates @(
    'C:\github-runners\go-tool-runtime\_work\go-tool-runtime\go-tool-runtime','D:\AI\go-tool-runtime','D:\AIWork\go-tool-runtime','D:\PyWork\go-tool-runtime'
)
$PythonExe = Resolve-Python $PythonExe

# Git is code synchronization only. No GitHub workflow is used for Case business
# execution, status, approval, artifact return, or scheduling.
if (-not $SkipCodeSync) {
    foreach ($repo in @($GoToolRoot,$OpenWorkerRoot)) {
        if (Test-Path -LiteralPath (Join-Path $repo '.git') -PathType Container) {
            Push-Location $repo
            try {
                $dirty = (& git status --porcelain); if ($LASTEXITCODE -ne 0) { throw "git status failed: $repo" }
                if (-not [string]::IsNullOrWhiteSpace(($dirty -join "`n"))) { throw "refuse code sync on dirty checkout: $repo" }
                & git pull --ff-only origin main; if ($LASTEXITCODE -ne 0) { throw "git pull --ff-only failed: $repo" }
            } finally { Pop-Location }
        }
    }
}

# Canonical activation always installs the binaries built from the currently
# selected local checkout and reruns REAL verification. There is deliberately no
# skip-verification switch: an older OPERATIONAL runtime must not be allowed to
# masquerade as the current capability set.
$installRoot = "$env:ProgramData\go-tool-runtime\work-agent"
$realReceipt = Join-Path $installRoot 'true-local-supervisor-real-verification.json'
$installAndVerify = Join-Path $GoToolRoot 'scripts\windows\install-and-verify-true-local-supervisor.ps1'
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File $installAndVerify -MaxParallelActions 4 -InstallRoot $installRoot -OpenWorkerRoot $OpenWorkerRoot
if ($LASTEXITCODE -ne 0) { throw "true local supervisor install/REAL verification failed: $LASTEXITCODE" }

# Historical REAL verification alone is insufficient. Current runtime must expose
# four fresh claim slots and four fresh executor slots now.
$status = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8848/api/execution/local-supervisor/status?machine=$expectedHost&limit=200" -TimeoutSec 10
if ([string]$status.status -ne 'OPERATIONAL' -or -not [bool]$status.operational) { throw "local supervisor is not OPERATIONAL: $($status | ConvertTo-Json -Depth 12 -Compress)" }
if ([string]$status.verification.status -ne 'REAL_VERIFIED') { throw "local supervisor verification is not REAL_VERIFIED: $($status.verification.status)" }
if ([int]$status.fresh_claim_slot_count -lt 4) { throw "need 4 fresh claim slots; actual=$($status.fresh_claim_slot_count)" }
if ([int]$status.fresh_executor_slot_count -lt 4) { throw "need 4 fresh executor slots; actual=$($status.fresh_executor_slot_count)" }
if ([string]$status.route_label -ne 'LOCAL_SUPERVISOR') { throw "unexpected route_label=$($status.route_label)" }
if ([bool]$status.github_action_used_for_business_execution) { throw 'status reports GitHub business execution' }
if (-not (Test-Path -LiteralPath $realReceipt -PathType Leaf)) { throw "REAL verification receipt missing: $realReceipt" }
if (-not [bool]$status.capability_authority_known -or -not [bool]$status.capability_authority_matches_machine) { throw "local capability authority is unavailable or belongs to another machine" }

$requiredCapabilities = @(
    'comfyx-studio.director.preproduction',
    'comfyx-studio.storyboard.plan',
    'presentation.openmaic',
    'image.comfyx.storyboard-real',
    'comfyx-studio.storyboard.real-bind',
    'comfyx.production.video.real',
    'comfyx-studio.finalize',
    'openworker.case.publish-artifacts',
    'drive.review.publish'
)
$registered = @($status.registered_capabilities | ForEach-Object { [string]$_ })
$missingCapabilities = @($requiredCapabilities | Where-Object { $registered -notcontains $_ })
if ($missingCapabilities.Count -gt 0) { throw ("Case 0005 local capability coverage incomplete: " + ($missingCapabilities -join ', ')) }

New-Item -ItemType Directory -Force -Path $Workspace | Out-Null
$specPath = Join-Path $OpenWorkerRoot 'case-specs\0005.json'
$manifestPath = Join-Path $OpenWorkerRoot 'case-worklists\0005.json'
$controllerModule = 'coworker.case0005_verified_local_controller'

$bootstrap = [ordered]@{
    case_id = '0005'
    machine = $expectedHost
    workspace_root = $Workspace
    openworker_root = $OpenWorkerRoot
    controller_module = $controllerModule
    manifest_path = $manifestPath
    spec_path = $specPath
    python_exe = $PythonExe
    env = [ordered]@{
        GTR_WORK_QUEUE_URL = 'http://127.0.0.1:8848'
        GTR_LOCAL_WORKERS = '4'
        OPENWORKER_ROOT = $OpenWorkerRoot
        GO_TOOL_ROOT = $GoToolRoot
        GTR_LOCAL_EXEC_EXE = (Join-Path $installRoot 'gtr-local-exec.exe')
    }
}
$bootstrapAck = Invoke-RestMethod -Method Post -Uri 'http://127.0.0.1:8848/api/openworker/case/bootstrap' -ContentType 'application/json' -Body ($bootstrap | ConvertTo-Json -Depth 8 -Compress) -TimeoutSec 60
if ([string]$bootstrapAck.status -ne 'completed') { throw "Case 0005 local bootstrap failed: $($bootstrapAck | ConvertTo-Json -Depth 8 -Compress)" }
if ([bool]$bootstrapAck.github_action_used_for_business_execution) { throw 'Case bootstrap unexpectedly reports GitHub business execution' }

$runtime = $null; $routeProven = $false; $deadline = [DateTime]::UtcNow.AddSeconds(90)
while ([DateTime]::UtcNow -lt $deadline) {
    try {
        $runtime = Invoke-RestMethod -Method Get -Uri "http://127.0.0.1:8848/api/openworker/case/runtime?case_id=0005&machine=$expectedHost&limit=500" -TimeoutSec 5
        if ([bool]$runtime.route_resolved_from_local_evidence -and [string]$runtime.route_label -eq 'LOCAL_SUPERVISOR') { $routeProven = $true; break }
    } catch {}
    Start-Sleep -Milliseconds 500
}
if (-not $routeProven) { throw 'Case 0005 did not materialize LOCAL_SUPERVISOR route evidence within 90 seconds' }

$controlDir = Join-Path $Workspace '.openworker'; New-Item -ItemType Directory -Force -Path $controlDir | Out-Null
$receiptPath = Join-Path $controlDir 'true-local-supervisor-activation.json'
$receipt = [ordered]@{
    schema_version = 'openworker-case0005-true-local-activation/v4'
    status = 'OPERATIONAL'
    case_id = '0005'
    machine = $actualHost
    workspace_root = $Workspace
    controller_module = $controllerModule
    business_execution_authority = 'go-tool-runtime-local-supervisor'
    process_kernel = 'OpenWorker:8787'
    local_queue = 'go-tool-runtime:8848'
    max_parallel_actions = 4
    fresh_claim_slot_count = [int]$status.fresh_claim_slot_count
    fresh_executor_slot_count = [int]$status.fresh_executor_slot_count
    registered_capabilities = $registered
    required_case_capabilities = $requiredCapabilities
    capability_coverage_complete = $true
    github_action_used_for_business_execution = $false
    code_sync_transport = $(if ($SkipCodeSync) { 'skipped' } else { 'local-git-pull-ff-only' })
    binaries_reinstalled_from_current_checkout = $true
    real_verification_receipt = $realReceipt
    supervisor_status = $status
    bootstrap_ack = $bootstrapAck
    initial_case_runtime = $runtime
    activated_at = [DateTime]::UtcNow.ToString('o')
}
$temp = "$receiptPath.tmp"; [IO.File]::WriteAllText($temp, ($receipt | ConvertTo-Json -Depth 20), [Text.UTF8Encoding]::new($false)); Move-Item -LiteralPath $temp -Destination $receiptPath -Force
Write-Host "CASE0005_TRUE_LOCAL_SUPERVISOR_OPERATIONAL host=$actualHost workspace=$Workspace receipt=$receiptPath"
