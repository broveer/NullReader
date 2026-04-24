# --- CRITICAL DEFINITIONS ---
$ErrorActionPreference = "SilentlyContinue"
$baseDir = $PSScriptRoot
$startTime = [System.DateTime]::Now

# --- MINIMAL SETUP HEADER ---
Clear-Host
Write-Host " [ NullReader ] System Maintenance & Indexing" -ForegroundColor DarkGray
Write-Host " --------------------------------------------" -ForegroundColor Gray

Add-Type -AssemblyName System.IO.Compression.FileSystem
$collectionsDir = Join-Path $baseDir "collections"
if (-not (Test-Path $collectionsDir)) { 
    New-Item -ItemType Directory -Path $collectionsDir -Force | Out-Null 
}

# Check for .cbr files and convert
$cbrFiles = Get-ChildItem -Path $collectionsDir -Recurse -Filter "*.cbr"
if ($cbrFiles.Count -gt 0) {
    Write-Host " [!] Found $($cbrFiles.Count) .cbr files. Converting..." -ForegroundColor Yellow
    python ConvertCbrToCbz.py
}

# --- FUNCTIONS ---
function ProcessSeries($seriesPath, $seriesName) {
    $infoFile = Join-Path -Path $seriesPath -ChildPath "config.json"
    $dates = @(); $issuesList = @()
    $comicFiles = @(Get-ChildItem -Path $seriesPath -Filter "*.cbz") + @(Get-ChildItem -Path $seriesPath -Filter "*.cbr")
    $coverDir = Join-Path $seriesPath "covers"
    
    if (-not (Test-Path $coverDir)) { New-Item -ItemType Directory -Path $coverDir -Force | Out-Null }
    
    foreach ($file in $comicFiles) {
        $baseName = $file.BaseName
        $issueNameStr = $baseName; $dateStr = ""
        if ($baseName -match '^(.*?)-(\d{8})$') {
            $issueNameStr = $matches[1] -replace '_', ' '; $dateStr = $matches[2]; $dates += $dateStr
        } else { $issueNameStr = $baseName -replace '_', ' ' }
        
        $coverImgPath = Join-Path $coverDir "$baseName.jpg"
        $pageCount = 0
        if ($file.Extension -eq '.cbz') {
            try {
                $zip = [System.IO.Compression.ZipFile]::OpenRead($file.FullName)
                $imageEntries = $zip.Entries | Where-Object { $_.FullName -match '\.(jpg|jpeg|png|webp|gif)$' } | Sort-Object FullName
                $pageCount = @($imageEntries).Count
                if (-not (Test-Path $coverImgPath)) {
                    $firstEntry = $imageEntries | Select-Object -First 1
                    if ($null -ne $firstEntry) { [System.IO.Compression.ZipFileExtensions]::ExtractToFile($firstEntry, $coverImgPath, $true) }
                }
            } finally { if ($zip) { $zip.Dispose() } }
        }
        
        $relComicPath = $file.FullName.Substring($baseDir.Length + 1).Replace("\", "/")
        $relCoverPath = if (Test-Path $coverImgPath) { $coverImgPath.Substring($baseDir.Length + 1).Replace("\", "/") } else { "" }
        $issuesList += "{ name: `"$issueNameStr`", date: `"$dateStr`", comic: `"$relComicPath`", cover: `"$relCoverPath`", pages: $pageCount }"
    }
    
    # Ensure config.json exists with defaults
    if (-not (Test-Path -Path $infoFile)) {
        $defaultInfo = [ordered]@{ name = $seriesName; description = "Welcome!"; run = ""; coverImage = ""; bannerImage = ""; authors = @(); pencillers = @(); characters = @(); genres = @(); creators = @() }
        $defaultInfo | ConvertTo-Json -Depth 5 | Set-Content -Path $infoFile -Encoding UTF8
    }
    
    $infoJson = Get-Content -Path $infoFile -Raw | ConvertFrom-Json
    
    # Auto-update 'run' if empty
    if ($null -eq $infoJson.run -or $infoJson.run -eq "") {
        if ($dates.Count -gt 0) {
            $dates = $dates | Sort-Object
            $earliest = $dates[0].Substring(0,4)
            $infoJson | Add-Member -MemberType NoteProperty -Name "run" -Value "$earliest - Present" -Force
            $infoJson | ConvertTo-Json | Set-Content -Path $infoFile -Encoding UTF8
        }
    }

    if ($issuesList.Count -gt 0) {
        # --- RESTORED METADATA EXTRACTION ---
        $t = if ($infoJson.name) { $infoJson.name } else { $seriesName }
        $d = if ($infoJson.description) { $infoJson.description } else { "Welcome!" }
        $r = if ($infoJson.run) { $infoJson.run } else { "" }
        $c = if ($infoJson.coverImage) { $infoJson.coverImage } else { "" }
        $b = if ($infoJson.bannerImage) { $infoJson.bannerImage } else { "" }
        $chars = if ($null -ne $infoJson.characters) { ConvertTo-Json $infoJson.characters -Compress } else { "[]" }
        $auths = if ($null -ne $infoJson.authors) { ConvertTo-Json $infoJson.authors -Compress } else { "[]" }
        $pencs = if ($null -ne $infoJson.pencillers) { ConvertTo-Json $infoJson.pencillers -Compress } else { "[]" }

        $seriesEntry = @"
        {
            folderName: "$seriesName",
            type: "series",
            title: "$($t -replace '"', '\"')",
            description: "$($d -replace '"', '\"')",
            run: "$($r -replace '"', '\"')",
            coverImage: "$($c -replace '"', '\"')",
            bannerImage: "$($b -replace '"', '\"')",
            characters: $chars,
            authors: $auths,
            pencillers: $pencs,
            issues: [
                $($issuesList -join ",`n                ")
            ]
        }
"@
        return $seriesEntry
    }
    return $null
}

# --- MAIN SCANNING LOGIC ---
Write-Host " [*] Indexing library..." -ForegroundColor Cyan
$topLevelFolders = @(Get-ChildItem -Path $collectionsDir -Directory)
$seriesEntries = @(); $collectionEntries = @()

for ($i = 0; $i -lt $topLevelFolders.Count; $i++) {
    $folder = $topLevelFolders[$i]
    if ($folder.Name -eq "covers" -or $folder.Name -eq "css") { continue }
    
    Write-Progress -Activity "NullReader: Indexing" -Status "Reading: $($folder.Name)" -PercentComplete ([int](($i / $topLevelFolders.Count) * 100))

    $comicFiles = @(Get-ChildItem -Path $folder.FullName -Filter "*.cbz" -File) + @(Get-ChildItem -Path $folder.FullName -Filter "*.cbr" -File)
    $subFolders = Get-ChildItem -Path $folder.FullName -Directory

    if ($comicFiles.Count -gt 0) {
        $entry = ProcessSeries -seriesPath $folder.FullName -seriesName $folder.Name
        if ($null -ne $entry) { $seriesEntries += $entry }
    }
    elseif ($subFolders.Count -gt 0) {
        # --- RESTORED COLLECTION METADATA ---
        $infoFile = Join-Path -Path $folder.FullName -ChildPath "config.json"
        if (Test-Path $infoFile) {
            $infoJson = Get-Content -Path $infoFile -Raw | ConvertFrom-Json
        }

        $subSeriesIds = @()
        foreach ($sub in $subFolders) {
            $subEntry = ProcessSeries -seriesPath $sub.FullName -seriesName $sub.Name
            if ($null -ne $subEntry) {
                $seriesEntries += $subEntry
                $subSeriesIds += ($seriesEntries.Count - 1).ToString()
            }
        }

        if ($subSeriesIds.Count -gt 0) {
            $t = if ($infoJson.name) { $infoJson.name } else { $folder.Name }
            $d = if ($infoJson.description) { $infoJson.description } else { "Welcome!" }
            $c = if ($infoJson.coverImage) { $infoJson.coverImage } else { "" }
            $b = if ($infoJson.bannerImage) { $infoJson.bannerImage } else { "" }
            $chars = if ($null -ne $infoJson.characters) { ConvertTo-Json $infoJson.characters -Compress } else { "[]" }
            $ids = ConvertTo-Json $subSeriesIds -Compress
            $spine = if ($null -ne $infoJson.spineConfig) { ConvertTo-Json $infoJson.spineConfig -Depth 5 -Compress } else { "{}" }

            $collectionEntries += @"
        {
            folderName: "$($folder.Name)",
            type: "collection",
            title: "$($t -replace '"', '\"')",
            description: "$($d -replace '"', '\"')",
            coverImage: "$($c -replace '"', '\"')",
            bannerImage: "$($b -replace '"', '\"')",
            characters: $chars,
            seriesIds: $ids,
            spineConfig: $spine
        }
"@
        }
    }
}

Write-Progress -Activity "NullReader" -Completed

# --- SAVE DATA ---
$allLibraryData = $seriesEntries + $collectionEntries
$jsContent = "const libraryData = [`n" + ($allLibraryData -join ",`n") + "`n];"
Set-Content -Path (Join-Path -Path $baseDir -ChildPath "libraryData.js") -Value $jsContent -Encoding UTF8

# --- QUICK SUMMARY ---
$elapsed = [System.DateTime]::Now - $startTime
Write-Host " ✅ Indexing Complete!" -ForegroundColor Green
Write-Host "    Items found: $($allLibraryData.Count)"
Write-Host "    Scan time:   $($elapsed.Seconds).$($elapsed.Milliseconds)s"
Write-Host " --------------------------------------------" -ForegroundColor Gray
Write-Host " [ Launching Server Engine... ]" -ForegroundColor Cyan