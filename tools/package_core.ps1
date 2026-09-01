param([string]$Version = "")

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$packageRoot = Join-Path $projectRoot "onyx_core"
$licensePath = Join-Path $projectRoot "LICENSE"
$distRoot = Join-Path $projectRoot "dist"
$internalInstructionName = "AG" + "ENTS.md"
$required = @(
    $licensePath,
    (Join-Path $packageRoot "__init__.py"),
    (Join-Path $packageRoot "blender_manifest.toml"),
    (Join-Path $packageRoot "README.md"),
    (Join-Path $packageRoot "docs\DEVELOPER_GUIDE.md")
)
foreach ($path in $required) {
    if (-not (Test-Path -LiteralPath $path)) { throw "Missing release file: $path" }
    if ((Get-Item -LiteralPath $path).Length -eq 0) { throw "Empty release file: $path" }
}

$manifest = Get-Content -LiteralPath (Join-Path $packageRoot "blender_manifest.toml") -Raw
$versionMatch = [regex]::Match($manifest, '(?m)^version\s*=\s*"([^"]+)"\s*$')
if (-not $versionMatch.Success) { throw "Manifest version is missing" }
if (-not $Version) { $Version = $versionMatch.Groups[1].Value }
if ($versionMatch.Groups[1].Value -ne $Version) {
    throw "Package version $Version does not match manifest version $($versionMatch.Groups[1].Value)"
}
$archive = Join-Path $distRoot "onyx_core-$Version.zip"
$apiSource = Get-Content -LiteralPath (Join-Path $packageRoot "api.py") -Raw
$runtimeVersionMatch = [regex]::Match(
    $apiSource,
    'CORE_VERSION\s*=\s*Version\((\d+),\s*(\d+),\s*(\d+)\)'
)
if (-not $runtimeVersionMatch.Success) { throw "Core runtime version is missing" }
$runtimeVersion = "{0}.{1}.{2}" -f @(
    $runtimeVersionMatch.Groups[1].Value,
    $runtimeVersionMatch.Groups[2].Value,
    $runtimeVersionMatch.Groups[3].Value
)
if ($runtimeVersion -ne $Version) {
    throw "Package version $Version does not match Core runtime version $runtimeVersion"
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

$trackedFiles = @(& git -C $projectRoot ls-files -- "onyx_core")
if ($LASTEXITCODE -ne 0 -or $trackedFiles.Count -eq 0) {
    throw "Unable to enumerate tracked Core package files."
}
$packagePrefix = "onyx_core/"
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
Write-Output "Packed $archive"
