param(
    [string]$CoreVersion = "",
    [string]$ReviewVersion = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot "dist"
$internalInstructionName = "AG" + "ENTS.md"

function Get-ManifestVersion {
    param([Parameter(Mandatory = $true)][string]$ManifestPath)

    $manifest = Get-Content -LiteralPath $ManifestPath -Raw
    $match = [regex]::Match($manifest, '(?m)^version\s*=\s*"([^"]+)"\s*$')
    if (-not $match.Success) { throw "Manifest version is missing: $ManifestPath" }
    return $match.Groups[1].Value
}

function Test-ReleaseArchive {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string[]]$RequiredEntries
    )

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
    try {
        $entries = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::OrdinalIgnoreCase
        )
        foreach ($entry in $archive.Entries) {
            $name = $entry.FullName.Replace('\', '/')
            if (
                [string]::IsNullOrWhiteSpace($name) -or
                $name.StartsWith('/') -or
                $name -match '^[A-Za-z]:' -or
                $name -match '(^|/)\.\.(/|$)'
            ) {
                throw "Unsafe archive path in $ArchivePath`: $name"
            }
            if (-not $entries.Add($name)) {
                throw "Duplicate archive entry in $ArchivePath`: $name"
            }
            if (
                $name -match '(^|/)__pycache__(/|$)' -or
                $name -match '\.py[co]$' -or
                [System.IO.Path]::GetFileName($name) -ieq $internalInstructionName
            ) {
                throw "Generated or repository-internal file in $ArchivePath`: $name"
            }
        }
        foreach ($required in $RequiredEntries) {
            if (-not $entries.Contains($required)) {
                throw "Required archive entry is missing from $ArchivePath`: $required"
            }
        }
    } finally {
        $archive.Dispose()
    }
}

if (-not $CoreVersion) {
    $CoreVersion = Get-ManifestVersion (Join-Path $projectRoot "onyx_core\blender_manifest.toml")
}
if (-not $ReviewVersion) {
    $ReviewVersion = Get-ManifestVersion (Join-Path $projectRoot "onyx_review\blender_manifest.toml")
}
if ($CoreVersion -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid Core version: $CoreVersion" }
if ($ReviewVersion -notmatch '^\d+\.\d+\.\d+$') { throw "Invalid Review version: $ReviewVersion" }

& (Join-Path $PSScriptRoot "check_public_source.ps1") | Write-Output
& (Join-Path $PSScriptRoot "package_core.ps1") -Version $CoreVersion | Write-Output
& (Join-Path $PSScriptRoot "package_review.ps1") -Version $ReviewVersion | Write-Output

$coreArchive = Join-Path $distRoot "onyx_core-$CoreVersion.zip"
$reviewArchive = Join-Path $distRoot "onyx_review-$ReviewVersion.zip"

Test-ReleaseArchive -ArchivePath $coreArchive -RequiredEntries @(
    "__init__.py",
    "blender_manifest.toml",
    "README.md",
    "LICENSE",
    "docs/DEVELOPER_GUIDE.md"
)
Test-ReleaseArchive -ArchivePath $reviewArchive -RequiredEntries @(
    "__init__.py",
    "blender_manifest.toml",
    "README.md",
    "LICENSE",
    "docs/USER_GUIDE.md",
    "_onyx_core/embedded.py",
    "_onyx_core/lifecycle.py",
    "delta_state.py",
    "highlight_state.py",
    "review_profiles.py"
)

$checksumPath = Join-Path $distRoot "SHA256SUMS.txt"
$checksumLines = @($coreArchive, $reviewArchive) | ForEach-Object {
    $hash = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $([System.IO.Path]::GetFileName($_))"
}
[System.IO.File]::WriteAllLines(
    $checksumPath,
    $checksumLines,
    [System.Text.UTF8Encoding]::new($false)
)

Write-Output "Release bundle: $coreArchive"
Write-Output "Release bundle: $reviewArchive"
Write-Output "Checksums: $checksumPath"
Write-Output "ONYX_RELEASE_BUNDLE_OK"
