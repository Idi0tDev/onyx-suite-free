$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$coreRoot = Join-Path $projectRoot "onyx_core"
$targets = @(
    Get-ChildItem -LiteralPath $projectRoot -Directory | Where-Object {
        $_.Name -ne "onyx_core" -and
        $_.Name -match '^onyx_[a-z0-9_]+$' -and
        (Test-Path -LiteralPath (Join-Path $_.FullName "blender_manifest.toml")) -and
        (Test-Path -LiteralPath (Join-Path $_.FullName "__init__.py"))
    } | Sort-Object Name
)
$runtimeFiles = @(
    "api.py",
    "assets.py",
    "embedded.py",
    "errors.py",
    "integration.py",
    "lifecycle.py",
    "readiness.py",
    "registry.py"
)

if ($targets.Count -eq 0) { throw "No public Onyx product extensions were discovered" }

foreach ($target in $targets) {
    $targetRoot = Join-Path $target.FullName "_onyx_core"
    New-Item -ItemType Directory -Path $targetRoot -Force | Out-Null
    foreach ($file in $runtimeFiles) {
        Copy-Item -LiteralPath (Join-Path $coreRoot $file) -Destination (Join-Path $targetRoot $file) -Force
    }
    Copy-Item -LiteralPath (Join-Path $coreRoot "embedded_init.py") -Destination (Join-Path $targetRoot "__init__.py") -Force
}

Write-Output "Synced public Onyx Core into $($targets.Count) product extension"

