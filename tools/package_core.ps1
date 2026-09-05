param(
    [string]$Version = "",
    [string]$BlenderPath = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
)

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
if (-not (Test-Path -LiteralPath $BlenderPath -PathType Leaf)) {
    throw "Blender extension builder was not found: $BlenderPath"
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

$trackedFiles = @(& git -C $projectRoot ls-files -- "onyx_core")
if ($LASTEXITCODE -ne 0 -or $trackedFiles.Count -eq 0) {
    throw "Unable to enumerate tracked Core package files."
}
$packagePrefix = "onyx_core/"
$tempBase = [System.IO.Path]::GetFullPath([System.IO.Path]::GetTempPath()).TrimEnd('\', '/')
$stagingRoot = [System.IO.Path]::GetFullPath(
    (Join-Path $tempBase ("onyx-core-build-" + [System.Guid]::NewGuid().ToString("N")))
)
if (-not $stagingRoot.StartsWith("$tempBase\", [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Unsafe Core staging path: $stagingRoot"
}
New-Item -ItemType Directory -Path $stagingRoot | Out-Null
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
            throw "Repository-internal or generated file cannot be staged: $trackedPath"
        }
        $sourcePath = [System.IO.Path]::GetFullPath((Join-Path $projectRoot $trackedPath))
        if (-not (Test-Path -LiteralPath $sourcePath -PathType Leaf)) {
            throw "Tracked package file is missing: $trackedPath"
        }
        $destinationPath = Join-Path $stagingRoot $relative
        $destinationDirectory = Split-Path -Parent $destinationPath
        New-Item -ItemType Directory -Path $destinationDirectory -Force | Out-Null
        Copy-Item -LiteralPath $sourcePath -Destination $destinationPath
    }
    Copy-Item -LiteralPath $licensePath -Destination (Join-Path $stagingRoot "LICENSE")

    & $BlenderPath --background --command extension build `
        --source-dir $stagingRoot `
        --output-filepath $archive
    if ($LASTEXITCODE -ne 0) {
        throw "Blender failed to build the standalone Core extension archive"
    }
} finally {
    $resolvedStaging = [System.IO.Path]::GetFullPath($stagingRoot)
    if (-not $resolvedStaging.StartsWith("$tempBase\", [System.StringComparison]::OrdinalIgnoreCase)) {
        throw "Refusing to clean unsafe Core staging path: $resolvedStaging"
    }
    if (Test-Path -LiteralPath $resolvedStaging) {
        Remove-Item -LiteralPath $resolvedStaging -Recurse -Force
    }
}
if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
    throw "Blender did not create the expected Core archive: $archive"
}
Write-Output "Built $archive with Blender's extension builder"
