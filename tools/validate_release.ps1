param(
    [string]$BlenderPath = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot "dist"
$catalogPath = Join-Path $PSScriptRoot "public_products.txt"

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
if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
    throw "Public product catalog is missing: $catalogPath"
}

$productIds = @(Get-Content -LiteralPath $catalogPath | ForEach-Object {
    $_.Trim()
} | Where-Object {
    $_ -and -not $_.StartsWith("#")
})
if ($productIds.Count -eq 0) { throw "Public product catalog is empty." }

foreach ($productId in $productIds) {
    $manifestPath = Join-Path $projectRoot "$productId\blender_manifest.toml"
    $version = Get-ManifestVersion $manifestPath
    $archive = Join-Path $distRoot "$productId-$version.zip"
    if (-not (Test-Path -LiteralPath $archive -PathType Leaf)) {
        throw "Release archive is missing. Run tools/build_release.ps1 first: $archive"
    }
    & $BlenderPath --background --command extension validate $archive
    if ($LASTEXITCODE -ne 0) {
        throw "Blender rejected the extension archive: $archive"
    }
}

Write-Output "ONYX_BLENDER_EXTENSION_VALIDATION_OK"
