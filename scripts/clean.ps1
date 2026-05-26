<#
.SYNOPSIS
    Clean Kolektria generated artefacts.

.DESCRIPTION
    Removes generated runtime, report, build, executable, and Python cache artefacts.

    The collected scan archive is intentionally preserved.

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
    Write-Host
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


function Format-ItemCount {
    param(
        [Parameter(Mandatory = $true)]
        [int]$Count
    )

    if ($Count -eq 1) {
        return "1 item"
    }

    return "$Count items"
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

    foreach ($item in $items) {
        Remove-Item -Path $item.FullName -Recurse -Force
    }

    return $items.Count
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

    foreach ($item in $Items) {
        Remove-Item -Path $item.FullName -Recurse -Force
    }

    return $Items.Count
}


# ------------------------------------------------------------
# CLEAN TARGETS
# ------------------------------------------------------------

$RuntimePath = "$ProjectRoot\data\runtime"
$ReportsPath = "$ProjectRoot\results\reports"
$DistPath = "$ProjectRoot\dist"
$PyInstallerPath = "$ProjectRoot\build\pyinstaller"
$CollectedPath = "$ProjectRoot\data\collected"

$CacheDirectories = Get-MatchingItems -Mode "Directory" -Pattern "__pycache__"
$PycFiles = Get-MatchingItems -Mode "File" -Pattern "*.pyc"
$PyoFiles = Get-MatchingItems -Mode "File" -Pattern "*.pyo"
$BytecodeFiles = @($PycFiles + $PyoFiles)


# ------------------------------------------------------------
# CLEAN PLAN
# ------------------------------------------------------------

$RuntimeCount = Get-DirectoryItemCount -Path $RuntimePath
$ReportsCount = Get-DirectoryItemCount -Path $ReportsPath
$DistCount = Get-DirectoryItemCount -Path $DistPath
$PyInstallerCount = Get-DirectoryRemovalCount -Path $PyInstallerPath
$CacheCount = $CacheDirectories.Count
$BytecodeCount = $BytecodeFiles.Count

$TotalCount = (
    $RuntimeCount +
    $ReportsCount +
    $DistCount +
    $PyInstallerCount +
    $CacheCount +
    $BytecodeCount
)

Write-Section "Clean Generated Artefacts"

Write-Host "The following generated artefacts will be removed:"
Write-Host

Write-Info "Runtime workspace: $(Get-RelativePath -Path $RuntimePath) ($RuntimeCount)"
Write-Info "Generated reports: $(Get-RelativePath -Path $ReportsPath) ($ReportsCount)"
Write-Info "Executable output: $(Get-RelativePath -Path $DistPath) ($DistCount)"
Write-Info "PyInstaller workspace: $(Get-RelativePath -Path $PyInstallerPath) ($PyInstallerCount)"
Write-Info "Python cache directories: __pycache__ ($CacheCount)"
Write-Info "Python bytecode files: *.pyc, *.pyo ($BytecodeCount)"

Write-Host
Write-Info "Total artefacts selected: $TotalCount"
Write-Info "Preserved archive: $(Get-RelativePath -Path $CollectedPath)"
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
$DistRemoved = Clear-DirectoryContents -Path $DistPath
$PyInstallerRemoved = Remove-DirectoryIfExists -Path $PyInstallerPath
$CacheRemoved = Remove-MatchingItems -Items $CacheDirectories
$BytecodeRemoved = Remove-MatchingItems -Items $BytecodeFiles


# ------------------------------------------------------------
# CLEAN RESULTS
# ------------------------------------------------------------

Write-Section "Cleanup Results"

Write-Success "Runtime workspace cleaned: $(Format-ItemCount -Count $RuntimeRemoved) removed"
Write-Success "Generated reports cleaned: $(Format-ItemCount -Count $ReportsRemoved) removed"
Write-Success "Executable output cleaned: $(Format-ItemCount -Count $DistRemoved) removed"
Write-Success "PyInstaller workspace cleaned: $(Format-ItemCount -Count $PyInstallerRemoved) removed"
Write-Success "Python cache directories cleaned: $(Format-ItemCount -Count $CacheRemoved) removed"
Write-Success "Python bytecode files cleaned: $(Format-ItemCount -Count $BytecodeRemoved) removed"

Write-Host
Write-Success "Generated artefacts cleaned"
Write-Info "Collected scan archive preserved: $(Get-RelativePath -Path $CollectedPath)"
Write-Host