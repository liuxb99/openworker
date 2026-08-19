param(
 [string]$TunnelId = $env:CONTROL_PLANE_TUNNEL_ID,
 [string]$TunnelClientVersion = 'v0.0.10',
 [switch]$SkipCaseActivation
)
$ErrorActionPreference='Stop'
$root=(Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$expected='DESKTOP-ODAQN0D';if([Environment]::MachineName-ine$expected){throw "activation must run on $expected"}
if([string]::IsNullOrWhiteSpace($TunnelId)-or$TunnelId-notmatch '^tunnel_[0-9a-f]{32}$'){throw 'valid CONTROL_PLANE_TUNNEL_ID required'}
if([string]::IsNullOrWhiteSpace($env:CONTROL_PLANE_API_KEY)){throw 'CONTROL_PLANE_API_KEY required (restricted runtime key: Tunnels Read + Use)'}
if(-not$SkipCaseActivation){
 & powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\activate-case0005-local-supervisor.ps1') -SkipCodeSync
 if($LASTEXITCODE-ne0){throw 'Case 0005 local-supervisor activation failed'}
}
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\install-openworker-opencode-bridge.ps1')
if($LASTEXITCODE-ne0){throw 'OpenCode bridge install failed'}
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\start-openworker-opencode-bridge.ps1')
if($LASTEXITCODE-ne0){throw 'OpenCode bridge start failed'}
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\verify-openworker-opencode-bridge.ps1')
if($LASTEXITCODE-ne0){throw 'OpenCode bridge local verification failed'}
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\install-openai-secure-mcp-tunnel-client.ps1') -Version $TunnelClientVersion
if($LASTEXITCODE-ne0){throw 'Secure MCP Tunnel client install failed'}
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\start-openworker-secure-mcp-tunnel.ps1') -TunnelId $TunnelId
if($LASTEXITCODE-ne0){throw 'Secure MCP Tunnel start failed'}
& powershell.exe -NoLogo -NoProfile -NonInteractive -ExecutionPolicy Bypass -File (Join-Path $root 'scripts\verify-openworker-secure-mcp-tunnel.ps1') -TunnelId $TunnelId
if($LASTEXITCODE-ne0){throw 'Secure MCP Tunnel verification failed'}
$receipt=[ordered]@{schema='case0005-secure-mcp-remote-activation/v1';status='REMOTE_TRANSPORT_READY';machine=$env:COMPUTERNAME;tunnel_id=$TunnelId;chain=@('OpenAI Secure MCP Tunnel','openworker-opencode-mcp:8850','OpenCode:4096','openworkerctl','go-tool:8848','OpenWorker:8787');github_actions_used_for_business_execution=$false;activated_at=[DateTime]::UtcNow.ToString('o')}
$state="$env:ProgramData\OpenWorker\secure-mcp-tunnel";New-Item -ItemType Directory -Force -Path $state|Out-Null;[IO.File]::WriteAllText((Join-Path $state 'case0005-remote-activation.json'),($receipt|ConvertTo-Json -Depth 8),[Text.UTF8Encoding]::new($false));$receipt|ConvertTo-Json -Depth 8
