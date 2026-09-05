param(
    [string]$Version = "",
    [string]$BlenderPath = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe"
)

$ErrorActionPreference = "Stop"
if (-not $Version) {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $manifest = Get-Content -LiteralPath (Join-Path $projectRoot "onyx_reviewer\blender_manifest.toml") -Raw
    $versionMatch = [regex]::Match($manifest, '(?m)^version\s*=\s*"([^"]+)"\s*$')
    if (-not $versionMatch.Success) { throw "Onyx Reviewer manifest version is missing" }
    $Version = $versionMatch.Groups[1].Value
}
& (Join-Path $PSScriptRoot "package_extension.ps1") `
    -AddonId "onyx_reviewer" `
    -Version $Version `
    -BlenderPath $BlenderPath `
    -Required @("README.md", "docs\USER_GUIDE.md")
