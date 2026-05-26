<#
.SYNOPSIS
    Kolektria baseline collector.

.DESCRIPTION
    Collects Windows update-state evidence required for Windows and MSRC correlation.

    Resolves operating system identity, architecture, privilege context, latest
    MSRC month, product name hints, and latest cumulative update context.

    Exact LCU installation timestamps are not emitted. The collector derives
    lower-precision update-state fields suitable for downstream Remetria analysis.

.OUTPUTS
    JSON object written to stdout.
#>


# ------------------------------------------------------------
# PRIVILEGE CONTEXT
# ------------------------------------------------------------

function Test-KolektriaAdministrator {
    <#
    .SYNOPSIS
        Return True when the current PowerShell session is elevated.
    #>

    $identity = [Security.Principal.WindowsIdentity]::GetCurrent()
    $principal = New-Object Security.Principal.WindowsPrincipal($identity)

    return $principal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
}


# ------------------------------------------------------------
# SYSTEM IDENTITY
# ------------------------------------------------------------

function Get-KolektriaArchitecture {
    <#
    .SYNOPSIS
        Return a normalised architecture label.
    #>

    switch ($env:PROCESSOR_ARCHITECTURE) {
        'AMD64' { return 'x64' }
        'ARM64' { return 'ARM64' }
        'x86'   { return 'x86' }
        default { return $env:PROCESSOR_ARCHITECTURE }
    }
}


function Get-KolektriaWindowsFamily {
    <#
    .SYNOPSIS
        Return the Windows product family from the operating system caption.
    #>

    param(
        [Parameter(Mandatory = $true)]
        [string]$Caption
    )

    if ($Caption -like '*Windows 11*') {
        return 'Windows 11'
    }

    if ($Caption -like '*Windows 10*') {
        return 'Windows 10'
    }

    return $null
}


function Get-KolektriaArchitectureToken {
    <#
    .SYNOPSIS
        Return the MSRC product-name architecture token.
    #>

    switch ($env:PROCESSOR_ARCHITECTURE) {
        'AMD64' { return 'x64' }
        'ARM64' { return 'ARM64' }
        'x86'   { return '32-bit' }
        default { return 'x64' }
    }
}


# ------------------------------------------------------------
# MSRC MODULE HELPERS
# ------------------------------------------------------------

function Import-KolektriaMsrcModule {
    <#
    .SYNOPSIS
        Import MsrcSecurityUpdates if available.
    #>

    try {
        Import-Module MsrcSecurityUpdates -ErrorAction Stop
        return $true
    }
    catch {
        return $false
    }
}


function ConvertFrom-KolektriaMonthId {
    <#
    .SYNOPSIS
        Convert yyyy-MMM MonthId text into a DateTime object.
    #>

    param(
        [Parameter(Mandatory = $true)]
        [string]$MonthId
    )

    $parts = $MonthId -split '-', 2

    if ($parts.Count -ne 2 -or -not $parts[1]) {
        return $null
    }

    $normalisedMonth = $parts[1].Substring(0, 1).ToUpper() + $parts[1].Substring(1).ToLower()

    try {
        return [datetime]::ParseExact(
            "$($parts[0])-$normalisedMonth",
            'yyyy-MMM',
            [System.Globalization.CultureInfo]::InvariantCulture
        )
    }
    catch {
        return $null
    }
}


# ------------------------------------------------------------
# MSRC MONTH RESOLUTION
# ------------------------------------------------------------

function Get-KolektriaLatestMsrcMonthId {
    <#
    .SYNOPSIS
        Return the latest MonthId exposed by MsrcSecurityUpdates.
    #>

    if (-not (Import-KolektriaMsrcModule)) {
        return $null
    }

    try {
        $command = Get-Command Get-MsrcCvrfDocument -ErrorAction Stop
        $validateSetAttribute = $command.Parameters['ID'].Attributes |
            Where-Object { $_ -is [System.Management.Automation.ValidateSetAttribute] } |
            Select-Object -First 1

        if (-not $validateSetAttribute -or -not $validateSetAttribute.ValidValues) {
            return $null
        }

        $parsedMonthIds = foreach ($monthId in $validateSetAttribute.ValidValues) {
            if (-not $monthId) {
                continue
            }

            $date = ConvertFrom-KolektriaMonthId -MonthId $monthId

            if (-not $date) {
                continue
            }

            [pscustomobject]@{
                Id   = $monthId
                Date = $date
            }
        }

        if (-not $parsedMonthIds) {
            return $null
        }

        return ($parsedMonthIds | Sort-Object Date | Select-Object -Last 1).Id
    }
    catch {
        return $null
    }
}


# ------------------------------------------------------------
# MSRC PRODUCT RESOLUTION
# ------------------------------------------------------------

function Get-KolektriaProductNameHint {
    <#
    .SYNOPSIS
        Resolve the best matching MSRC product name for this host.
    #>

    param(
        [Parameter(Mandatory = $true)]
        [string]$MonthId
    )

    if (-not (Import-KolektriaMsrcModule)) {
        return $null
    }

    try {
        $operatingSystem = Get-CimInstance Win32_OperatingSystem
        $currentVersion = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'

        $windowsFamily = Get-KolektriaWindowsFamily -Caption $operatingSystem.Caption

        if (-not $windowsFamily) {
            return $null
        }

        $displayVersion = $currentVersion.DisplayVersion

        if (-not $displayVersion) {
            $displayVersion = $currentVersion.ReleaseId
        }

        $architectureToken = Get-KolektriaArchitectureToken

        $document = Get-MsrcCvrfDocument -ID $MonthId -ErrorAction Stop
        $affectedSoftware = Get-MsrcCvrfAffectedSoftware `
            -Vulnerability $document.Vulnerability `
            -ProductTree $document.ProductTree

        if (-not $affectedSoftware) {
            return $null
        }

        $windowsProductNames = $affectedSoftware |
            Select-Object -ExpandProperty FullProductName -Unique |
            Where-Object { $_ -like 'Windows *' } |
            Sort-Object

        if (-not $windowsProductNames) {
            return $null
        }

        if ($displayVersion) {
            $versionedProductName = if ($architectureToken -eq '32-bit') {
                "$windowsFamily Version $displayVersion for 32-bit Systems"
            }
            else {
                "$windowsFamily Version $displayVersion for $architectureToken-based Systems"
            }

            $match = $windowsProductNames |
                Where-Object { $_ -ieq $versionedProductName } |
                Select-Object -First 1

            if ($match) {
                return $match
            }
        }

        $genericProductName = if ($architectureToken -eq '32-bit') {
            "$windowsFamily for 32-bit Systems"
        }
        else {
            "$windowsFamily for $architectureToken-based Systems"
        }

        $match = $windowsProductNames |
            Where-Object { $_ -ieq $genericProductName } |
            Select-Object -First 1

        if ($match) {
            return $match
        }

        if ($architectureToken -eq '32-bit') {
            $match = $windowsProductNames |
                Where-Object { $_ -like "$windowsFamily*32-bit*" } |
                Select-Object -First 1
        }
        else {
            $match = $windowsProductNames |
                Where-Object { $_ -like "$windowsFamily*$architectureToken-based*" } |
                Select-Object -First 1
        }

        if ($match) {
            return $match
        }

        return (
            $windowsProductNames |
                Where-Object { $_ -like "$windowsFamily*" } |
                Select-Object -First 1
        )
    }
    catch {
        return $null
    }
}


function Resolve-KolektriaProductNameHint {
    <#
    .SYNOPSIS
        Search recent MSRC months for a usable product name hint.
    #>

    param(
        [Parameter(Mandatory = $false)]
        [AllowNull()]
        [string]$LatestMonthId
    )

    if (-not $LatestMonthId) {
        return [pscustomobject]@{
            ProductNameHint        = $null
            ResolvedProductMonthId = $null
        }
    }

    try {
        $latestMsrcDate = [datetime]::ParseExact(
            $LatestMonthId,
            'yyyy-MMM',
            [System.Globalization.CultureInfo]::InvariantCulture
        )

        for ($index = 0; $index -lt 6; $index++) {
            $monthId = $latestMsrcDate.AddMonths(-$index).ToString('yyyy-MMM')
            $candidateProductName = Get-KolektriaProductNameHint -MonthId $monthId

            if ($candidateProductName) {
                return [pscustomobject]@{
                    ProductNameHint        = $candidateProductName
                    ResolvedProductMonthId = $monthId
                }
            }
        }
    }
    catch {
        return [pscustomobject]@{
            ProductNameHint        = $null
            ResolvedProductMonthId = $null
        }
    }

    return [pscustomobject]@{
        ProductNameHint        = $null
        ResolvedProductMonthId = $null
    }
}


# ------------------------------------------------------------
# LCU ANCHOR
# ------------------------------------------------------------

function Get-KolektriaLcuContext {
    <#
    .SYNOPSIS
        Return latest cumulative update context when running elevated.
    #>

    param(
        [Parameter(Mandatory = $true)]
        [bool]$IsAdmin
    )

    if (-not $IsAdmin) {
        return [pscustomobject]@{
            LcuMonthId      = $null
            LcuPackageName  = $null
            LcuInstallMonth = $null
            PatchAgeDays    = $null
        }
    }

    try {
        $latestCumulativeUpdate = Get-WindowsPackage -Online |
            Where-Object { $_.PackageName -like '*RollupFix*' } |
            Sort-Object InstallTime -Descending |
            Select-Object -First 1

        if (-not $latestCumulativeUpdate) {
            return [pscustomobject]@{
                LcuMonthId      = $null
                LcuPackageName  = $null
                LcuInstallMonth = $null
                PatchAgeDays    = $null
            }
        }

        $installTime = Get-Date $latestCumulativeUpdate.InstallTime
        $patchAgeDays = [int]((Get-Date).Date - $installTime.Date).TotalDays

        [pscustomobject]@{
            LcuMonthId      = $installTime.ToString('yyyy-MMM')
            LcuPackageName  = $latestCumulativeUpdate.PackageName
            LcuInstallMonth = $installTime.ToString('yyyy-MMM')
            PatchAgeDays    = $patchAgeDays
        }
    }
    catch {
        return [pscustomobject]@{
            LcuMonthId      = $null
            LcuPackageName  = $null
            LcuInstallMonth = $null
            PatchAgeDays    = $null
        }
    }
}


# ------------------------------------------------------------
# BASELINE COLLECTION
# ------------------------------------------------------------

function Get-KolektriaBaseline {
    <#
    .SYNOPSIS
        Build the Kolektria baseline object.
    #>

    $currentVersion = Get-ItemProperty 'HKLM:\SOFTWARE\Microsoft\Windows NT\CurrentVersion'
    $operatingSystem = Get-CimInstance Win32_OperatingSystem

    $buildString = "$($currentVersion.CurrentBuild).$($currentVersion.UBR)"
    $architecture = Get-KolektriaArchitecture
    $isAdmin = Test-KolektriaAdministrator

    $lcuContext = Get-KolektriaLcuContext -IsAdmin $isAdmin
    $msrcLatestMonthId = Get-KolektriaLatestMsrcMonthId
    $productResolution = Resolve-KolektriaProductNameHint -LatestMonthId $msrcLatestMonthId

    [pscustomobject]@{
        OsName                 = $operatingSystem.Caption
        OsEdition              = $currentVersion.EditionID
        DisplayVersion         = $currentVersion.DisplayVersion
        Build                  = $buildString
        Architecture           = $architecture
        IsAdmin                = $isAdmin

        LcuMonthId             = $lcuContext.LcuMonthId
        LcuPackageName         = $lcuContext.LcuPackageName
        LcuInstallMonth        = $lcuContext.LcuInstallMonth
        PatchAgeDays           = $lcuContext.PatchAgeDays

        MsrcLatestMonthId      = $msrcLatestMonthId
        ResolvedProductMonthId = $productResolution.ResolvedProductMonthId
        ProductNameHint        = $productResolution.ProductNameHint
    }
}


# ------------------------------------------------------------
# ENTRY POINT
# ------------------------------------------------------------

if ($MyInvocation.InvocationName -ne '.') {
    Get-KolektriaBaseline | ConvertTo-Json -Depth 4
}