$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot

Push-Location $projectRoot
try {
    $trackedFiles = @(& git ls-files)
    if ($LASTEXITCODE -ne 0) { throw "Unable to enumerate tracked files." }

    $problems = [System.Collections.Generic.List[string]]::new()
    $internalInstructionName = "AG" + "ENTS.md"

    foreach ($path in $trackedFiles) {
        $fileName = [System.IO.Path]::GetFileName($path)
        if ($fileName -ieq $internalInstructionName) {
            $problems.Add("Repository-internal instruction file is tracked: $path")
        }
        if (
            $path -match '(^|/)__pycache__(/|$)' -or
            $path -match '\.py[co]$' -or
            $path -match '(^|/)dist(/|$)' -or
            $path -match '\.zip$'
        ) {
            $problems.Add("Generated or packaged file is tracked: $path")
        }
    }

    $publicProducts = @("onyx_core", "onyx_review")
    $productRoots = $trackedFiles | ForEach-Object {
        if ($_ -match '^(onyx_[a-z0-9_]+)/') { $Matches[1] }
    } | Sort-Object -Unique
    foreach ($productRoot in $productRoots) {
        if ($productRoot -notin $publicProducts) {
            $problems.Add("Unexpected Onyx product directory is tracked: $productRoot")
        }
    }

    $allowedIdentifiers = @(
        "onyx_asset_id",
        "onyx_asset_role",
        "onyx_core",
        "onyx_example",
        "onyx_missing",
        "onyx_review",
        "onyx_review_analysis_test_module",
        "onyx_smoke",
        "onyx_source_name"
    )
    $identifiers = @(& git grep -I -h -o -E 'onyx_[a-z0-9_]+' -- .)
    $grepStatus = $LASTEXITCODE
    if ($grepStatus -notin @(0, 1)) { throw "Unable to scan public identifiers." }
    foreach ($identifier in ($identifiers | Sort-Object -Unique)) {
        if ($identifier -notin $allowedIdentifiers) {
            $problems.Add("Unexpected Onyx identifier appears in tracked source: $identifier")
        }
    }

    $allowedPackageScripts = @(
        "package_core.ps1",
        "package_extension.ps1",
        "package_review.ps1"
    )
    $packageReferences = @(& git grep -I -h -o -E 'package_[a-z0-9_]+\.ps1' -- .)
    $grepStatus = $LASTEXITCODE
    if ($grepStatus -notin @(0, 1)) { throw "Unable to scan package references." }
    foreach ($packageReference in ($packageReferences | Sort-Object -Unique)) {
        if ($packageReference -notin $allowedPackageScripts) {
            $problems.Add("Unexpected package script appears in tracked source: $packageReference")
        }
    }

    # These names describe internal workflow context, not the public add-ons.
    # Construct them in pieces so the audit script does not flag itself.
    $internalOnlyTerms = @(("co" + "dex"), ("super" + "hive"))
    foreach ($term in $internalOnlyTerms) {
        $matches = @(& git grep -I -n -i -F $term -- .)
        $grepStatus = $LASTEXITCODE
        if ($grepStatus -notin @(0, 1)) { throw "Unable to scan internal-only terms." }
        foreach ($match in $matches) {
            $problems.Add("Internal-only term '$term' appears in tracked source: $match")
        }
    }

    $privatePathPattern = '([A-Za-z]:[\\/]+Users[\\/]+[A-Za-z0-9._-]+|/Users/[A-Za-z0-9._-]+|/home/[A-Za-z0-9._-]+)'
    $privatePaths = @(& git grep -I -n -E $privatePathPattern -- .)
    $grepStatus = $LASTEXITCODE
    if ($grepStatus -notin @(0, 1)) { throw "Unable to scan local user paths." }
    foreach ($match in $privatePaths) {
        $problems.Add("Local user path appears in tracked source: $match")
    }

    if ($problems.Count -gt 0) {
        throw "Public source audit failed:`n- $($problems -join "`n- ")"
    }

    # A successful no-match grep reports native status 1. Clear that status so
    # a direct `pwsh -File` invocation also exits successfully in CI.
    $global:LASTEXITCODE = 0
    Write-Output "ONYX_PUBLIC_SOURCE_OK"
} finally {
    Pop-Location
}
