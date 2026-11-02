```powershell id="g5x9qa"
# ===============================
# Solution Selector
# ===============================

param (
    [string]$alertId
)

# -----------------------------------
# BASE PATH
# -----------------------------------

$BaseFolder = $PSScriptRoot

$FeedbackFile = Join-Path $BaseFolder "feedback_data.json"

$ActionFile = Join-Path $BaseFolder "action_executor.json"


# -----------------------------------
# LOAD RCA / ACTION DATA
# -----------------------------------

if (-not (Test-Path $ActionFile)) {

    Write-Host " action_executor.json not found"

    exit
}

$rcaData = Get-Content $ActionFile -Raw | ConvertFrom-Json


# -----------------------------------
# HANDLE LIST OUTPUT
# -----------------------------------

if ($rcaData -is [System.Array]) {

    $rcaData = $rcaData[0]
}


# -----------------------------------
# GET ALERT ID
# -----------------------------------

if (-not $alertId) {

    $alertId = $rcaData.root_cause.primary_event_id.ToString()
}


# -----------------------------------
# EXTRACT SOLUTIONS
# -----------------------------------

$solutions = @()

foreach ($item in $rcaData.suggested_actions) {

    $solutions += $item.action
}


# -----------------------------------
# LOAD FEEDBACK DATA
# -----------------------------------

if (Test-Path $FeedbackFile) {

    $feedbackData = Get-Content `
        $FeedbackFile `
        -Raw |
        ConvertFrom-Json

} else {

    $feedbackData = @{}
}


# -----------------------------------
# SELECT BEST SOLUTION
# -----------------------------------

$bestSolution = $null

$bestScore = -999


foreach ($sol in $solutions) {

    $success = 0

    $failure = 0


    if (
        $feedbackData.$alertId -and
        $feedbackData.$alertId.$sol
    ) {

        $success = $feedbackData.$alertId.$sol.success

        $failure = $feedbackData.$alertId.$sol.failure
    }


    $score = $success - $failure


    if ($score -gt $bestScore) {

        $bestScore = $score

        $bestSolution = $sol
    }
}


# -----------------------------------
# OUTPUT
# -----------------------------------

Write-Host ""

Write-Host "==============================="

Write-Host "Best solution for alert $alertId"

Write-Host "==============================="

Write-Host ""

Write-Host $bestSolution

Write-Host ""
```
