
param(
    [switch]$RunOnce,
    [ValidateRange(2, 3600)]
    [int]$PollSeconds = 5
)

# By default this process stays alive and continuously ingests new Windows
# Event Viewer alerts. The child invocation performs one complete pipeline run.
if (-not $RunOnce) {
    Write-Host "Starting continuous Event Viewer monitoring (every $PollSeconds seconds)."
    Write-Host "Press Ctrl+C to stop monitoring."

    while ($true) {
        & $PSCommandPath -RunOnce -PollSeconds $PollSeconds
        Start-Sleep -Seconds $PollSeconds
    }
}

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
        Write-Host "Last Run = $lastRun"
        Write-Host "Filter Log = $log"

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

        Write-Host "Log: $log"
        Write-Host "Events returned: $($events.Count)"

        if ($events) {
            $allAlerts += $events
        }

        Write-Host "Total alerts so far: $($allAlerts.Count)"
        Write-Host "---------------------------"

    }
    catch {

    Write-Host "ERROR in log $log"

    Write-Host $_

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

Write-Host "Reached before Python"

$testFile = Join-Path $PSScriptRoot "task_test.txt"
"Reached here at $(Get-Date)" | Out-File $testFile -Append

$venvPython = Join-Path $PSScriptRoot "venv\Scripts\python.exe"
$condaPython = Join-Path $env:USERPROFILE "anaconda3\python.exe"

if (Test-Path $venvPython) {
    $python = $venvPython
}
elseif (Test-Path $condaPython) {
    $python = $condaPython
}
else {
    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if (-not $pythonCommand) {
        throw "Python was not found. Create venv\\Scripts\\python.exe or install Python."
    }
    $python = $pythonCommand.Source
}

Write-Host "Using Python:"
& $python --version

& $python -m pip show pandas
& $python -m pip show requests
Write-Host "Python: $python"

& $python -u (Join-Path $PSScriptRoot "module2.py")

Write-Host " Full pipeline completed"

exit 0

