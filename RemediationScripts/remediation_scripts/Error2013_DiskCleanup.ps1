# ============================================
# Event ID 2013 - Disk Cleanup Remediation
# ============================================

$ErrorActionPreference = "SilentlyContinue"

Write-Host "Starting Disk Cleanup..."

$startTime = Get-Date

$before = (Get-PSDrive C).Free

$deletedFiles = 0
$deletedFolders = 0

$cleanedPaths = @()

function Clean-Folder($folder) {

    if (Test-Path $folder) {

        $global:cleanedPaths += $folder

        Get-ChildItem $folder -Recurse -Force -ErrorAction SilentlyContinue |

        Sort-Object FullName -Descending |

        ForEach-Object {

            try {

                if ($_.PSIsContainer) {

                    Remove-Item $_.FullName -Force -Recurse

                    $global:deletedFolders++

                }

                else {

                    Remove-Item $_.FullName -Force

                    $global:deletedFiles++

                }

            }

            catch {}

        }

    }

}

# ============================================
# Cleanup Locations
# ============================================

Clean-Folder $env:TEMP

Clean-Folder "C:\Windows\Temp"

Clean-Folder "C:\CleanupTest"

# ============================================
# Empty Recycle Bin
# ============================================

try {

    Clear-RecycleBin -Force

    $cleanedPaths += "Recycle Bin"

}

catch {}

$after = (Get-PSDrive C).Free

$recovered = [math]::Round(($after - $before) / 1GB,2)

$executionTime = [math]::Round(
    ((Get-Date) - $startTime).TotalSeconds,
    2
)

$result = @{

    status = "SUCCESS"

    files_deleted = $deletedFiles

    folders_deleted = $deletedFolders

    recovered_gb = $recovered

    execution_time_sec = $executionTime

    cleanup_paths = $cleanedPaths

    completed_at = (Get-Date).ToString("yyyy-MM-dd HH:mm:ss")

}

$result |

ConvertTo-Json -Depth 5 |

Set-Content "$PSScriptRoot\cleanup_result.json"

Write-Host ""
Write-Host "==========================================="
Write-Host " Disk Cleanup Completed"
Write-Host "==========================================="
Write-Host " Files Deleted    : $deletedFiles"
Write-Host " Folders Deleted  : $deletedFolders"
Write-Host " Space Recovered  : $recovered GB"
Write-Host " Execution Time   : $executionTime sec"
Write-Host "==========================================="

exit 0