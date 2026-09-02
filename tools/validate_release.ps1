param(
    [string]$BlenderPath = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot "dist"

function Get-ManifestVersion {
    param([Parameter(Mandatory = $true)][string]$ManifestPath)

    $manifest = Get-Content -LiteralPath $ManifestPath -Raw
    $match = [regex]::Match($manifest, '(?m)^version\s*=\s*"([^"]+)"\s*$')
    if (-not $match.Success) { throw "Manifest version is missing: $ManifestPath" }
    return $match.Groups[1].Value
}

if (-not (Test-Path -LiteralPath $BlenderPath -PathType Leaf)) {
    throw "Blender 5.2 was not found: $BlenderPath"
}

$coreVersion = Get-ManifestVersion (Join-Path $projectRoot "onyx_core\blender_manifest.toml")
$reviewerVersion = Get-ManifestVersion (Join-Path $projectRoot "onyx_reviewer\blender_manifest.toml")
$archives = @(
    (Join-Path $distRoot "onyx_core-$coreVersion.zip"),
    (Join-Path $distRoot "onyx_reviewer-$reviewerVersion.zip")
)

foreach ($archive in $archives) {
    if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
        throw "Release archive is missing. Run tools/build_release.ps1 first: $archive"
    }
    & $BlenderPath --background --command extension validate $archive
    if ($LASTEXITCODE -ne 0) {
        throw "Blender rejected the extension archive: $archive"
    }
}

Write-Output "ONYX_BLENDER_EXTENSION_VALIDATION_OK"
