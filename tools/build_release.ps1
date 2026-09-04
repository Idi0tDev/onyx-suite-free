$ErrorActionPreference = "Stop"
$projectRoot = Split-Path -Parent $PSScriptRoot
$distRoot = Join-Path $projectRoot "dist"
$catalogPath = Join-Path $PSScriptRoot "public_products.txt"
$internalInstructionName = "AG" + "ENTS.md"

function Get-PublicProductIds {
    if (-not (Test-Path -LiteralPath $catalogPath -PathType Leaf)) {
        throw "Public product catalog is missing: $catalogPath"
    }

    $ids = @(Get-Content -LiteralPath $catalogPath | ForEach-Object {
        $_.Trim()
    } | Where-Object {
        $_ -and -not $_.StartsWith("#")
    })
    if ($ids.Count -eq 0) { throw "Public product catalog is empty." }

    $duplicates = @($ids | Group-Object | Where-Object Count -gt 1)
    if ($duplicates.Count -gt 0) {
        throw "Duplicate public product ID: $($duplicates[0].Name)"
    }
    foreach ($id in $ids) {
        if ($id -notmatch '^onyx_[a-z0-9_]+$') {
            throw "Invalid public product ID: $id"
        }
    }
    if ($ids[0] -ne "onyx_core") {
        throw "Onyx Core must be the first public product."
    }
    return $ids
}

function Get-ManifestField {
    param(
        [Parameter(Mandatory = $true)][string]$ManifestPath,
        [Parameter(Mandatory = $true)][string]$FieldName
    )

    $manifest = Get-Content -LiteralPath $ManifestPath -Raw
    $escapedName = [regex]::Escape($FieldName)
    $match = [regex]::Match($manifest, "(?m)^$escapedName\s*=\s*`"([^`"]+)`"\s*$")
    if (-not $match.Success) {
        throw "Manifest field '$FieldName' is missing: $ManifestPath"
    }
    return $match.Groups[1].Value
}

function Test-ReleaseArchive {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string[]]$RequiredEntries
    )

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $archive = [System.IO.Compression.ZipFile]::OpenRead($ArchivePath)
    try {
        $entries = [System.Collections.Generic.HashSet[string]]::new(
            [System.StringComparer]::OrdinalIgnoreCase
        )
        foreach ($entry in $archive.Entries) {
            $name = $entry.FullName.Replace('\', '/')
            if (
                [string]::IsNullOrWhiteSpace($name) -or
                $name.StartsWith('/') -or
                $name -match '^[A-Za-z]:' -or
                $name -match '(^|/)\.\.(/|$)'
            ) {
                throw "Unsafe archive path in $ArchivePath`: $name"
            }
            if (-not $entries.Add($name)) {
                throw "Duplicate archive entry in $ArchivePath`: $name"
            }
            if (
                $name -match '(^|/)__pycache__(/|$)' -or
                $name -match '\.py[co]$' -or
                [System.IO.Path]::GetFileName($name) -ieq $internalInstructionName
            ) {
                throw "Generated or repository-internal file in $ArchivePath`: $name"
            }
        }
        foreach ($required in $RequiredEntries) {
            if (-not $entries.Contains($required)) {
                throw "Required archive entry is missing from $ArchivePath`: $required"
            }
        }
    } finally {
        $archive.Dispose()
    }
}

$productIds = @(Get-PublicProductIds)
$products = foreach ($id in $productIds) {
    $manifestPath = Join-Path $projectRoot "$id\blender_manifest.toml"
    if (-not (Test-Path -LiteralPath $manifestPath -PathType Leaf)) {
        throw "Public product manifest is missing: $id"
    }
    $manifestId = Get-ManifestField -ManifestPath $manifestPath -FieldName "id"
    if ($manifestId -ne $id) {
        throw "Catalog ID $id does not match manifest ID $manifestId."
    }
    $version = Get-ManifestField -ManifestPath $manifestPath -FieldName "version"
    if ($version -notmatch '^\d+\.\d+\.\d+$') {
        throw "Invalid product version for $id`: $version"
    }
    [PSCustomObject]@{
        Id = $id
        Version = $version
    }
}

& (Join-Path $PSScriptRoot "check_public_source.ps1") | Write-Output

New-Item -ItemType Directory -Path $distRoot -Force | Out-Null
Get-ChildItem -LiteralPath $distRoot -Filter "onyx_*.zip" -File | Remove-Item -Force
$checksumPath = Join-Path $distRoot "SHA256SUMS.txt"
if (Test-Path -LiteralPath $checksumPath) {
    Remove-Item -LiteralPath $checksumPath -Force
}

$archives = [System.Collections.Generic.List[string]]::new()
foreach ($product in $products) {
    if ($product.Id -eq "onyx_core") {
        & (Join-Path $PSScriptRoot "package_core.ps1") -Version $product.Version | Write-Output
        $requiredEntries = @(
            "__init__.py",
            "blender_manifest.toml",
            "README.md",
            "LICENSE",
            "docs/DEVELOPER_GUIDE.md"
        )
    } else {
        $shortId = $product.Id.Substring("onyx_".Length)
        $productPackager = Join-Path $PSScriptRoot "package_$shortId.ps1"
        if (Test-Path -LiteralPath $productPackager -PathType Leaf) {
            & $productPackager -Version $product.Version | Write-Output
        } else {
            & (Join-Path $PSScriptRoot "package_extension.ps1") `
                -AddonId $product.Id `
                -Version $product.Version `
                -Required @("README.md") | Write-Output
        }
        $requiredEntries = @(
            "__init__.py",
            "blender_manifest.toml",
            "README.md",
            "LICENSE",
            "_onyx_core/embedded.py",
            "_onyx_core/lifecycle.py"
        )
    }

    $archivePath = Join-Path $distRoot "$($product.Id)-$($product.Version).zip"
    Test-ReleaseArchive -ArchivePath $archivePath -RequiredEntries $requiredEntries
    $archives.Add($archivePath)
}

$checksumLines = $archives | ForEach-Object {
    $hash = (Get-FileHash -LiteralPath $_ -Algorithm SHA256).Hash.ToLowerInvariant()
    "$hash  $([System.IO.Path]::GetFileName($_))"
}
[System.IO.File]::WriteAllLines(
    $checksumPath,
    $checksumLines,
    [System.Text.UTF8Encoding]::new($false)
)

foreach ($archive in $archives) {
    Write-Output "Release bundle: $archive"
}
Write-Output "Checksums: $checksumPath"
Write-Output "ONYX_RELEASE_BUNDLE_OK"
