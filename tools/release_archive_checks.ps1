function Test-OnyxReleaseArchive {
    param(
        [Parameter(Mandatory = $true)][string]$ArchivePath,
        [Parameter(Mandatory = $true)][string[]]$RequiredEntries
    )

    Add-Type -AssemblyName System.IO.Compression
    Add-Type -AssemblyName System.IO.Compression.FileSystem
    $internalInstructionName = "AG" + "ENTS.md"
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
            if (
                $name -match '(^|/)(docs|tests|tools)(/|$)' -or
                [System.IO.Path]::GetFileName($name) -ieq 'embedded_init.py' -or
                [System.IO.Path]::GetFileName($name) -imatch '^(README|CHANGELOG|CONTRIBUTING|SECURITY)\.md$'
            ) {
                throw "Non-runtime file in $ArchivePath`: $name"
            }
            if ($name.EndsWith(".py", [System.StringComparison]::OrdinalIgnoreCase)) {
                $reader = [System.IO.StreamReader]::new($entry.Open())
                try {
                    $source = $reader.ReadToEnd()
                } finally {
                    $reader.Dispose()
                }
                if ($source -match '(?m)^\s*(?:from\s+(?:threading|queue)\b|import\s+[^\r\n#]*\b(?:threading|queue)\b)') {
                    throw "Blender-unsafe threading or queue import in $ArchivePath`: $name"
                }
                if ($source -match '(?m)^\s*(?:from\s+onyx_core(?:\.|\s)|import\s+onyx_core(?:\.|\s|$))') {
                    throw "External Onyx Core dependency in $ArchivePath`: $name"
                }
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
