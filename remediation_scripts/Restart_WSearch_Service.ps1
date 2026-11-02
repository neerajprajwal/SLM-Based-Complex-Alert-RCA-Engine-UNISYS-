# =====================================================
# Restart_WSearch_Service.ps1
# =====================================================

Write-Host ""
Write-Host "===== WINDOWS SEARCH SERVICE RECOVERY ====="
Write-Host ""

$service = "WSearch"

try {

    $svc = Get-Service $service

    Write-Host "Current Status : $($svc.Status)"

    if ($svc.Status -eq "Running") {

        Write-Host ""
        Write-Host "Service is already running."

        Write-Host "No remediation required."

        exit 0

    }

    Write-Host ""
    Write-Host "Service stopped."

    Write-Host "Starting Windows Search..."

    Start-Service $service

    Start-Sleep -Seconds 2

    $svc = Get-Service $service

    Write-Host ""

    Write-Host "New Status : $($svc.Status)"

    if ($svc.Status -eq "Running") {

        Write-Host ""

        Write-Host "===== SERVICE RECOVERY SUCCESSFUL ====="

        exit 0

    }

    else {

        Write-Host ""

        Write-Host "===== SERVICE FAILED TO START ====="

        exit 1

    }

}
catch {

    Write-Host ""

    Write-Host "Recovery Failed"

    Write-Host $_

    exit 1

} 
