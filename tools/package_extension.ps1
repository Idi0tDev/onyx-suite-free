param(
    [Parameter(Mandatory = $true)][string]$AddonId,
    [Parameter(Mandatory = $true)][string]$Version,
    [string[]]$Required = @()
)

$ErrorActionPreference = "Stop"
if ($AddonId -notmatch '^onyx_[a-z0-9_]+$' -or $AddonId -eq "onyx_core") {
    throw "Invalid Onyx product package ID: $AddonId"
}

$projectRoot = Split-Path -Parent $PSScriptRoot
& (Join-Path $PSScriptRoot "sync_embedded_core.ps1") | Write-Output

$packageRoot = Join-Path $projectRoot $AddonId
$licensePath = Join-Path $projectRoot "LICENSE"
$internalInstructionName = "AG" + "ENTS.md"
$resolvedProject = [System.IO.Path]::GetFullPath($projectRoot).TrimEnd('\')
$resolvedPackage = [System.IO.Path]::GetFullPath($packageRoot)
if (-not $resolvedPackage.StartsWith("$resolvedProject\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Product package is outside the project: $resolvedPackage"
}
if (-not (Test-Path -LiteralPath (Join-Path $resolvedPackage "blender_manifest.toml"))) {
    throw "Onyx product manifest is missing: $AddonId"
}
$packageRoot = $resolvedPackage
$distRoot = Join-Path $projectRoot "dist"
$archive = Join-Path $distRoot "$AddonId-$Version.zip"
$requiredPaths = @(
    $licensePath,
    (Join-Path $packageRoot "__init__.py"),
    (Join-Path $packageRoot "blender_manifest.toml"),
    (Join-Path $packageRoot "_onyx_core\embedded.py"),
    (Join-Path $packageRoot "_onyx_core\lifecycle.py")
)
foreach ($relative in $Required) {
    $requiredPaths += Join-Path $packageRoot $relative
}
foreach ($path in $requiredPaths) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing release file: $path" }
    if ((Get-Item -LiteralPath $path).Length -eq 0) { throw "Empty release file: $path" }
}

$manifest = Get-Content -LiteralPath (Join-Path $packageRoot "blender_manifest.toml") -Raw
$versionMatch = [regex]::Match($manifest, '(?m)^version\s*=\s*"([^"]+)"\s*$')
if (-not $versionMatch.Success) { throw "Manifest version is missing: $AddonId" }
if ($versionMatch.Groups[1].Value -ne $Version) {
    throw "Package version $Version does not match $AddonId manifest version $($versionMatch.Groups[1].Value)"
}
$initSource = Get-Content -LiteralPath (Join-Path $packageRoot "__init__.py") -Raw
$runtimeVersionMatch = [regex]::Match($initSource, '(?m)^VERSION\s*=\s*"([^"]+)"\s*$')
if (-not $runtimeVersionMatch.Success) { throw "Runtime VERSION is missing: $AddonId" }
if ($runtimeVersionMatch.Groups[1].Value -ne $Version) {
    throw "Package version $Version does not match $AddonId runtime version $($runtimeVersionMatch.Groups[1].Value)"
}

New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
if (Test-Path -LiteralPath $archive) {
    Remove-Item -LiteralPath $archive -Force
}
Add-Type -AssemblyName System.IO.Compression
Add-Type -AssemblyName System.IO.Compression.FileSystem

function Add-ArchiveFile {
    param(
        [Parameter(Mandatory = $true)]$Archive,
        [Parameter(Mandatory = $true)][string]$SourcePath,
        [Parameter(Mandatory = $true)][string]$EntryName
    )

    $entry = $Archive.CreateEntry(
        $EntryName,
        [System.IO.Compression.CompressionLevel]::Optimal
    )
    $entry.LastWriteTime = [System.DateTimeOffset]::new(1980, 1, 1, 0, 0, 0, [System.TimeSpan]::Zero)
    $source = [System.IO.File]::OpenRead($SourcePath)
    try {
        $destination = $entry.Open()
        try {
            $source.CopyTo($destination)
        } finally {
            $destination.Dispose()
        }
    } finally {
        $source.Dispose()
    }
}

$trackedFiles = @(& git -C $projectRoot ls-files -- $AddonId)
if ($LASTEXITCODE -ne 0 -or $trackedFiles.Count -eq 0) {
    throw "Unable to enumerate tracked package files: $AddonId"
}
$packagePrefix = "$AddonId/"
$stream = [System.IO.File]::Open($archive, [System.IO.FileMode]::CreateNew)
try {
    $zip = [System.IO.Compression.ZipArchive]::new(
        $stream,
        [System.IO.Compression.ZipArchiveMode]::Create,
        $false
    )
    try {
        foreach ($trackedPath in ($trackedFiles | Sort-Object)) {
            if (-not $trackedPath.StartsWith($packagePrefix, [System.StringComparison]::Ordinal)) {
                continue
            }
            $relative = $trackedPath.Substring($packagePrefix.Length)
            if (
                $relative -match '(^|/)__pycache__(/|$)' -or
                $relative -match '\.py[co]$' -or
                [System.IO.Path]::GetFileName($relative) -ieq $internalInstructionName
            ) {
                throw "Repository-internal or generated file cannot be packaged: $trackedPath"
            }
            $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $trackedPath))
            if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
                throw "Tracked package file is missing: $trackedPath"
            }
            Add-ArchiveFile -Archive $zip -SourcePath $sourcePath -EntryName $relative
        }
        Add-ArchiveFile -Archive $zip -SourcePath $licensePath -EntryName "LICENSE"
    } finally {
        $zip.Dispose()
    }
} finally {
    $stream.Dispose()
}
Write-Output "Packed $archive with bundled Onyx Core runtime"
