param([string]$Version = "")

$ErrorActionPreference = "Stop"
if (-not $Version) {
    $projectRoot = Split-Path -Parent $PSScriptRoot
    $manifest = Get-Content -LiteralPath (Join-Path $projectRoot "onyx_review\blender_manifest.toml") -Raw
    $versionMatch = [regex]::Match($manifest, '(?m)^version\s*=\s*"([^"]+)"\s*$')
    if (-not $versionMatch.Success) { throw "Onyx Review manifest version is missing" }
    $Version = $versionMatch.Groups[1].Value
}
& (Join-Path $PSScriptRoot "package_extension.ps1") `
    -AddonId "onyx_review" `
    -Version $Version `
    -Required @("README.md", "docs\USER_GUIDE.md")
