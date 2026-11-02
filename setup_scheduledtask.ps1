```powershell
#Requires -RunAsAdministrator

# -----------------------------------
# BASE CONFIG
# -----------------------------------

$BaseFolder   = $PSScriptRoot

$Module1Path  = Join-Path $BaseFolder "module1.ps1"

$AlertsFile   = Join-Path $BaseFolder "alerts.json"

$LastRunFile  = Join-Path $BaseFolder "last_run.txt"

$TaskName     = "AlertAgent_EventTrigger"

$TaskDesc     = "Continuous Windows Alert Monitoring Pipeline"


# -----------------------------------
# CREATE REQUIRED FILES/FOLDERS
# -----------------------------------

if (-not (Test-Path $AlertsFile)) {
    "[]" | Set-Content -Encoding UTF8 $AlertsFile
}

if (-not (Test-Path $LastRunFile)) {
    (Get-Date).AddMinutes(-10).ToString("o") |
        Set-Content -Encoding UTF8 $LastRunFile
}


# -----------------------------------
# MODULE 1 SCRIPT CONTENT
# -----------------------------------

$Module1Code = @'

$BaseFolder  = $PSScriptRoot

$AlertsFile  = Join-Path $BaseFolder "alerts.json"

$LastRunFile = Join-Path $BaseFolder "last_run.txt"


# -----------------------------------
# READ LAST RUN TIME
# -----------------------------------

$lastRun = (Get-Date).AddMinutes(-10)

if (Test-Path $LastRunFile) {

    $raw = Get-Content $LastRunFile |
        Select-Object -First 1

    if ($raw) {

        [datetime]::TryParse(
            $raw,
            [ref]$lastRun
        ) | Out-Null
    }
}


# -----------------------------------
# COLLECT WINDOWS EVENTS
# -----------------------------------

$logs = @(
    "System",
    "Application"
)

$allAlerts = @()

foreach ($log in $logs) {

    $filter = @{
        LogName   = $log
        StartTime = $lastRun
        Level     = 1,2,3
    }

    try {

        $events = Get-WinEvent `
            -FilterHashtable $filter `
            -ErrorAction SilentlyContinue |

        ForEach-Object {

            [PSCustomObject]@{

                timestamp = $_.TimeCreated.ToString("o")

                event_id  = $_.Id

                source    = $_.ProviderName

                severity  = if ($_.LevelDisplayName) {
                    $_.LevelDisplayName
                }
                else {
                    "Unknown"
                }

                message   = $_.Message

                host      = $env:COMPUTERNAME

                user      = if ($_.UserId) {
                    $_.UserId.Value
                }
                else {
                    "SYSTEM"
                }
            }
        }

        if ($events) {
            $allAlerts += $events
        }

    }
    catch {
    }
}


# -----------------------------------
# EXIT IF NO NEW ALERTS
# -----------------------------------

if ($allAlerts.Count -eq 0) {

    Write-Host " No new alerts found."

    exit 0
}


# -----------------------------------
# SAVE ALERTS
# -----------------------------------

$allAlerts |
    ConvertTo-Json -Depth 4 |
    Set-Content -Encoding UTF8 $AlertsFile


# -----------------------------------
# UPDATE LAST RUN TIME
# -----------------------------------

(Get-Date).ToString("o") |
    Set-Content -Encoding UTF8 $LastRunFile


Write-Host " New alerts detected: $($allAlerts.Count)"


# -----------------------------------
# RUN MODULE 2
# -----------------------------------

Write-Host " Running Module 2..."

python `
    (Join-Path -Path $PSScriptRoot -ChildPath "module2.py")

Write-Host " Full pipeline completed"

exit 0

'@


# -----------------------------------
# SAVE MODULE 1
# -----------------------------------

$Module1Code |
    Set-Content `
    -Encoding UTF8 `
    $Module1Path


# -----------------------------------
# REMOVE OLD TASK
# -----------------------------------

if (
    Get-ScheduledTask `
        -TaskName $TaskName `
        -ErrorAction SilentlyContinue
) {

    Unregister-ScheduledTask `
        -TaskName $TaskName `
        -Confirm:$false
}


# -----------------------------------
# EVENT-BASED TRIGGER
# -----------------------------------

$EventQuery = @"
<QueryList>

  <Query Id="0">

    <Select Path="System">
      *[System[(Level=1 or Level=2 or Level=3)]]
    </Select>

    <Select Path="Application">
      *[System[(Level=1 or Level=2 or Level=3)]]
    </Select>

  </Query>

</QueryList>
"@


# -----------------------------------
# CREATE EVENT TRIGGER
# -----------------------------------

$TriggerClass = Get-CimClass `
    -ClassName MSFT_TaskEventTrigger `
    -Namespace Root/Microsoft/Windows/TaskScheduler


$Trigger = New-CimInstance `
    -CimClass $TriggerClass `
    -ClientOnly


$Trigger.Subscription = $EventQuery

$Trigger.Enabled = $true


# -----------------------------------
# TASK ACTION
# -----------------------------------

$Action = New-ScheduledTaskAction `
    -Execute "powershell.exe" `
    -Argument "-NoProfile -ExecutionPolicy Bypass -File `"$Module1Path`""


# -----------------------------------
# TASK SETTINGS
# -----------------------------------

$Settings = New-ScheduledTaskSettingsSet `
    -StartWhenAvailable `
    -AllowStartIfOnBatteries `
    -DontStopIfGoingOnBatteries


# -----------------------------------
# RUN AS SYSTEM
# -----------------------------------

$Principal = New-ScheduledTaskPrincipal `
    -UserId "SYSTEM" `
    -LogonType ServiceAccount `
    -RunLevel Highest


# -----------------------------------
# REGISTER TASK
# -----------------------------------

Register-ScheduledTask `
    -TaskName $TaskName `
    -Description $TaskDesc `
    -Trigger $Trigger `
    -Action $Action `
    -Settings $Settings `
    -Principal $Principal


Write-Host ""

Write-Host " Alert Agent setup complete."

Write-Host " Continuous monitoring pipeline enabled."

Write-Host ""

Write-Host "Pipeline:"

Write-Host "Windows Logs - Module1 - Module2 - RCA Engine"
```
