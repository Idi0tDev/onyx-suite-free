param(
    [string]$BlenderPath = "C:\Program Files\Blender Foundation\Blender 5.2\blender.exe",
    [string]$PythonPath = ""
)

$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

if (-not (Test-Path -LiteralPath $BlenderPath)) {
    throw "Blender 5.2 was not found: $BlenderPath"
}
if (-not $PythonPath) {
    $PythonPath = Join-Path (Split-Path -Parent $BlenderPath) "5.2\python\bin\python.exe"
}
if (-not (Test-Path -LiteralPath $PythonPath)) {
    throw "Blender's bundled Python was not found: $PythonPath"
}

& (Join-Path $PSScriptRoot "check_public_source.ps1") | Write-Output
& (Join-Path $PSScriptRoot "sync_embedded_core.ps1") | Write-Output

$pureTests = @(
    "tests\extension_manifest_test.py",
    "tests\core_framework_test.py",
    "tests\review_analysis_test.py",
    "tests\review_profiles_test.py",
    "tests\core_review_embedding_test.py"
)
foreach ($test in $pureTests) {
    & $PythonPath (Join-Path $projectRoot $test)
    if ($LASTEXITCODE -ne 0) { throw "Pure test failed: $test" }
}

$blenderTests = @(
    "tests\core_blender_smoke_test.py",
    "tests\review_blender_smoke_test.py",
    "tests\core_products_blender_test.py"
)
foreach ($test in $blenderTests) {
    & $BlenderPath --background --factory-startup --python-exit-code 1 --python (Join-Path $projectRoot $test)
    if ($LASTEXITCODE -ne 0) { throw "Blender test failed: $test" }
}

Write-Output "ONYX_SUITE_FREE_TESTS_OK"
