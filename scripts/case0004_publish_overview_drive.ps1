param(
    [string]$WorkspaceRoot = 'D:\AI-Work\jobs\0004-DWG-TO-3D',
    [string]$OverviewRelativePath = 'dwg\exports\default\visual-search\case0004-overview.png',
    [string]$ExpectedSha256 = '5cee03340cbbcad51e412b46b85bda9dcaac22b193586b953bbfd5134039103e',
    [string]$DriveFolderId = $env:OPENWORKER_GOOGLE_DRIVE_REVIEW_FOLDER_ID,
    [string]$AccessToken = $env:OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN,
    [string]$Machine = 'DESKTOP-O87PJNR',
    [string]$ReceiptRelativePath = 'receipts\case0004-overview-drive-handoff.json'
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

function Fail([string]$Message) {
    throw "CASE0004_OVERVIEW_DRIVE_HANDOFF_FAILED: $Message"
}

if ($env:COMPUTERNAME -and $env:COMPUTERNAME -ine $Machine) {
    Fail "fixed machine mismatch expected=$Machine actual=$env:COMPUTERNAME"
}
if ([string]::IsNullOrWhiteSpace($AccessToken)) {
    Fail 'OPENWORKER_GOOGLE_DRIVE_ACCESS_TOKEN is required'
}

$overview = Join-Path $WorkspaceRoot $OverviewRelativePath
if (-not (Test-Path -LiteralPath $overview -PathType Leaf)) {
    Fail "overview missing: $overview"
}
$file = Get-Item -LiteralPath $overview
if ($file.Length -le 0) {
    Fail 'overview is empty'
}
$sha = (Get-FileHash -LiteralPath $overview -Algorithm SHA256).Hash.ToLowerInvariant()
if ($ExpectedSha256 -and $sha -ne $ExpectedSha256.ToLowerInvariant()) {
    Fail "overview SHA mismatch expected=$ExpectedSha256 actual=$sha"
}

$headers = @{ Authorization = "Bearer $AccessToken" }
$fileName = 'case0004-overview.png'
$metadata = [ordered]@{
    name = $fileName
    description = "Case 0004 REAL overview for ChatGPT multimodal review; machine=$Machine; sha256=$sha"
}
if (-not [string]::IsNullOrWhiteSpace($DriveFolderId)) {
    $metadata.parents = @($DriveFolderId)
}

$boundary = '===============openworker_' + [Guid]::NewGuid().ToString('N')
$crlf = "`r`n"
$metaJson = $metadata | ConvertTo-Json -Depth 8 -Compress
$imageBytes = [IO.File]::ReadAllBytes($overview)
$prefix = "--$boundary$crlf" +
          "Content-Type: application/json; charset=UTF-8$crlf$crlf" +
          $metaJson + $crlf +
          "--$boundary$crlf" +
          "Content-Type: image/png$crlf$crlf"
$suffix = "$crlf--$boundary--$crlf"
$prefixBytes = [Text.Encoding]::UTF8.GetBytes($prefix)
$suffixBytes = [Text.Encoding]::UTF8.GetBytes($suffix)
$body = New-Object byte[] ($prefixBytes.Length + $imageBytes.Length + $suffixBytes.Length)
[Array]::Copy($prefixBytes, 0, $body, 0, $prefixBytes.Length)
[Array]::Copy($imageBytes, 0, $body, $prefixBytes.Length, $imageBytes.Length)
[Array]::Copy($suffixBytes, 0, $body, $prefixBytes.Length + $imageBytes.Length, $suffixBytes.Length)

$uploadUri = 'https://www.googleapis.com/upload/drive/v3/files?uploadType=multipart&fields=id,name,mimeType,size,md5Checksum,webViewLink,parents,createdTime'
$result = Invoke-RestMethod -Method Post -Uri $uploadUri -Headers $headers -ContentType "multipart/related; boundary=$boundary" -Body $body
if (-not $result.id) {
    Fail 'Google Drive upload returned no file id'
}

$receiptPath = Join-Path $WorkspaceRoot $ReceiptRelativePath
$receiptDir = Split-Path -Parent $receiptPath
New-Item -ItemType Directory -Force -Path $receiptDir | Out-Null
$receipt = [ordered]@{
    schema = 'case0004.overview-drive-handoff.v1'
    case_id = '0004'
    machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME } else { $Machine }
    workspace_root = $WorkspaceRoot
    source_path = $overview
    source_sha256 = $sha
    source_size = $file.Length
    drive_file_id = $result.id
    drive_name = $result.name
    drive_mime_type = $result.mimeType
    drive_size = $result.size
    drive_web_view_link = $result.webViewLink
    status = 'READY_FOR_CHATGPT_MULTIMODAL_REVIEW'
    openworker_job_id = $env:OPENWORKER_JOB_ID
    openworker_agent_slot = $env:OPENWORKER_AGENT_SLOT
    published_at = (Get-Date).ToUniversalTime().ToString('o')
}
[IO.File]::WriteAllText($receiptPath, ($receipt | ConvertTo-Json -Depth 20), (New-Object Text.UTF8Encoding($false)))

$receipt | ConvertTo-Json -Depth 20
