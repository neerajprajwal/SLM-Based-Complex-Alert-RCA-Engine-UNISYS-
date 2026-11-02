# ===============================
# Feedback Module
# ===============================

param (
    [string]$alertId,
    [string]$solution,
    [string]$feedback
)

$BaseFolder = Split-Path -Parent $MyInvocation.MyCommand.Path

$FeedbackFile = Join-Path $BaseFolder "feedback_data.json"
# --------------------------------
# APPROVED ACTIONS FILE
# --------------------------------

$ApprovedFile = Join-Path $BaseFolder "approved_actions.json"

if (-not (Test-Path $ApprovedFile)) {

    "{}" | Set-Content -Encoding UTF8 $ApprovedFile

}


# --------------------------------
# CREATE FILE IF NOT EXISTS
# --------------------------------

if (-not (Test-Path $FeedbackFile)) {
    "{}" | Set-Content -Encoding UTF8 $FeedbackFile
}


# --------------------------------
# LOAD JSON SAFELY
# --------------------------------

$jsonText = Get-Content $FeedbackFile -Raw

if ([string]::IsNullOrWhiteSpace($jsonText)) {
    $jsonText = "{}"
}

$data = @{}

try {

    $parsed = $jsonText | ConvertFrom-Json

    if ($parsed -ne $null) {

        foreach ($prop in $parsed.PSObject.Properties) {

            $data[$prop.Name] = $prop.Value
        }
    }

} catch {

    $data = @{}
}


# --------------------------------
# CREATE ALERT SECTION
# --------------------------------

if (-not $data.ContainsKey($alertId)) {

    $data[$alertId] = @{}
}


# --------------------------------
# CREATE SOLUTION SECTION
# --------------------------------

if (-not $data[$alertId].ContainsKey($solution)) {

    $data[$alertId][$solution] = @{
        success = 0
        failure = 0
    }
}


# --------------------------------
# UPDATE FEEDBACK
# --------------------------------

if ($feedback -eq "success") {

    $data[$alertId][$solution]["success"] += 1

    # ==============================
    # Remember approved remediation
    # ==============================

    $approved = @{}

    try {

        $approvedText = Get-Content $ApprovedFile -Raw

        if (-not [string]::IsNullOrWhiteSpace($approvedText)) {

            $parsedApproved = $approvedText | ConvertFrom-Json

            if ($parsedApproved) {

                foreach ($prop in $parsedApproved.PSObject.Properties) {

                    $approved.Add($prop.Name, @{
                        status = $prop.Value.status
                        approved_on = $prop.Value.approved_on
                    })

                }

            }

        }

    }

    catch {

        $approved = @{}

    }

    $approved[$solution] = @{

        status = "approved"

        approved_on = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

    }

    $approved |

        ConvertTo-Json -Depth 10 |

        Set-Content -Encoding UTF8 $ApprovedFile

}

elseif ($feedback -eq "failure") {

    $data[$alertId][$solution]["failure"] += 1

}


# --------------------------------
# SAVE JSON
# --------------------------------

$data |
    ConvertTo-Json -Depth 10 |
    Set-Content -Encoding UTF8 $FeedbackFile


Write-Host " Feedback updated successfully."