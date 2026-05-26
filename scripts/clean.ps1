<#
.SYNOPSIS
    Clean Kolektria generated artefacts.

.DESCRIPTION
    Removes generated runtime, report, build, and Python cache artefacts.

    The collected scan archive and executable output are intentionally preserved.

.OUTPUTS
    Console status output.
#>


# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

$ProjectRoot = Resolve-Path "$PSScriptRoot\.."


# ------------------------------------------------------------
# DISPLAY HELPERS
# ------------------------------------------------------------

function Write-Section {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Title
    )

    Write-Host
    Write-Host $Title
    Write-Host ("-" * $Title.Length)
}


function Write-Step {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[*] $Message"
}


function Write-Result {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "    [+] $Message"
}


function Write-Detail {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "    [i] $Message"
}


function Write-Success {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[+] $Message"
}


function Write-Info {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Message
    )

    Write-Host "[i] $Message"
}


function Get-RelativePath {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    $projectRootText = $ProjectRoot.Path.TrimEnd('\')
    $pathText = $Path.TrimEnd('\')

    if ($pathText.StartsWith($projectRootText)) {
        return $pathText.Substring($projectRootText.Length).TrimStart('\')
    }

    return $Path
}


# ------------------------------------------------------------
# CLEAN HELPERS
# ------------------------------------------------------------

function Get-DirectoryItemCount {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $false)]
        [string[]]$Preserve = @(".gitkeep")
    )

    if (-not (Test-Path $Path)) {
        return 0
    }

    $items = @(
        Get-ChildItem -Path $Path -Force |
            Where-Object { $Preserve -notcontains $_.Name }
    )

    return $items.Count
}


function Clear-DirectoryContents {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path,

        [Parameter(Mandatory = $false)]
        [string[]]$Preserve = @(".gitkeep")
    )

    if (-not (Test-Path $Path)) {
        return 0
    }

    $items = @(
        Get-ChildItem -Path $Path -Force |
            Where-Object { $Preserve -notcontains $_.Name }
    )

    $removedCount = 0

    foreach ($item in $items) {
        if (Test-Path $item.FullName) {
            Remove-Item -Path $item.FullName -Recurse -Force
            $removedCount++
        }
    }

    return $removedCount
}


function Get-DirectoryRemovalCount {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (Test-Path $Path) {
        return 1
    }

    return 0
}


function Remove-DirectoryIfExists {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Path
    )

    if (-not (Test-Path $Path)) {
        return 0
    }

    Remove-Item -Path $Path -Recurse -Force
    return 1
}


function Get-MatchingItems {
    param(
        [Parameter(Mandatory = $true)]
        [string]$Mode,

        [Parameter(Mandatory = $true)]
        [string]$Pattern
    )

    if ($Mode -eq "Directory") {
        return @(
            Get-ChildItem -Path $ProjectRoot -Directory -Recurse -Force -Filter $Pattern
        )
    }

    return @(
        Get-ChildItem -Path $ProjectRoot -File -Recurse -Force -Include $Pattern
    )
}


function Remove-MatchingItems {
    param(
        [Parameter(Mandatory = $true)]
        [object[]]$Items
    )

    $removedCount = 0

    foreach ($item in $Items) {
        if (Test-Path $item.FullName) {
            Remove-Item -Path $item.FullName -Recurse -Force
            $removedCount++
        }
    }

    return $removedCount
}


# ------------------------------------------------------------
# CLEAN TARGETS
# ------------------------------------------------------------

$RuntimePath = "$ProjectRoot\data\runtime"
$ReportsPath = "$ProjectRoot\results\reports"
$PyInstallerPath = "$ProjectRoot\build\pyinstaller"
$CollectedPath = "$ProjectRoot\data\collected"
$DistPath = "$ProjectRoot\dist"

$CacheDirectories = Get-MatchingItems -Mode "Directory" -Pattern "__pycache__"
$PycFiles = Get-MatchingItems -Mode "File" -Pattern "*.pyc"
$PyoFiles = Get-MatchingItems -Mode "File" -Pattern "*.pyo"
$BytecodeFiles = @($PycFiles + $PyoFiles)


# ------------------------------------------------------------
# CLEAN PLAN
# ------------------------------------------------------------

$RuntimeCount = Get-DirectoryItemCount -Path $RuntimePath
$ReportsCount = Get-DirectoryItemCount -Path $ReportsPath
$PyInstallerCount = Get-DirectoryRemovalCount -Path $PyInstallerPath
$CacheCount = $CacheDirectories.Count
$BytecodeCount = $BytecodeFiles.Count

$TotalCount = (
    $RuntimeCount +
    $ReportsCount +
    $PyInstallerCount +
    $CacheCount +
    $BytecodeCount
)

Write-Section "Clean Generated Artefacts"

Write-Step "Reviewing generated artefact targets"
Write-Result "Cleanup plan prepared"
Write-Detail "Runtime workspace: $(Get-RelativePath -Path $RuntimePath)"
Write-Detail "Generated reports: $(Get-RelativePath -Path $ReportsPath)"
Write-Detail "PyInstaller workspace: $(Get-RelativePath -Path $PyInstallerPath)"
Write-Detail "Python cache directories: __pycache__"
Write-Detail "Python bytecode files: *.pyc, *.pyo"

Write-Host
Write-Step "Checking preserved locations"
Write-Result "Archive preservation confirmed"
Write-Detail "Collected archive: $(Get-RelativePath -Path $CollectedPath)"
Write-Detail "Executable output: $(Get-RelativePath -Path $DistPath)"

Write-Host
Write-Step "Counting selected artefacts"
Write-Result "Artefact count calculated"
Write-Detail "Runtime workspace items: $RuntimeCount"
Write-Detail "Generated report items: $ReportsCount"
Write-Detail "PyInstaller workspace items: $PyInstallerCount"
Write-Detail "Python cache directories: $CacheCount"
Write-Detail "Python bytecode files: $BytecodeCount"
Write-Detail "Total artefacts selected: $TotalCount"

Write-Host
$response = Read-Host "Proceed with cleanup? [y/N]"

if ($response -notin @("y", "Y", "yes", "YES")) {
    Write-Host
    Write-Info "Cleanup cancelled"
    exit 0
}


# ------------------------------------------------------------
# CLEAN EXECUTION
# ------------------------------------------------------------

$RuntimeRemoved = Clear-DirectoryContents -Path $RuntimePath
$ReportsRemoved = Clear-DirectoryContents -Path $ReportsPath
$PyInstallerRemoved = Remove-DirectoryIfExists -Path $PyInstallerPath
$BytecodeRemoved = Remove-MatchingItems -Items $BytecodeFiles
$CacheRemoved = Remove-MatchingItems -Items $CacheDirectories


# ------------------------------------------------------------
# CLEAN RESULTS
# ------------------------------------------------------------

Write-Section "Cleanup Results"

Write-Step "Cleaning runtime workspace"
Write-Result "Runtime workspace cleaned"
Write-Detail "Items removed: $RuntimeRemoved"

Write-Host
Write-Step "Cleaning generated reports"
Write-Result "Generated reports cleaned"
Write-Detail "Items removed: $ReportsRemoved"

Write-Host
Write-Step "Cleaning PyInstaller workspace"
Write-Result "PyInstaller workspace cleaned"
Write-Detail "Items removed: $PyInstallerRemoved"

Write-Host
Write-Step "Cleaning Python bytecode files"
Write-Result "Python bytecode files cleaned"
Write-Detail "Items removed: $BytecodeRemoved"

Write-Host
Write-Step "Cleaning Python cache directories"
Write-Result "Python cache directories cleaned"
Write-Detail "Items removed: $CacheRemoved"

Write-Host
Write-Success "Generated artefacts cleaned"
Write-Info "Collected scan archive preserved: $(Get-RelativePath -Path $CollectedPath)"
Write-Info "Executable output preserved: $(Get-RelativePath -Path $DistPath)"
Write-Host