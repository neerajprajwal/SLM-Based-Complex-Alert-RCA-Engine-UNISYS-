Write-Host "=================================="
Write-Host "Running Demo Remediation..."
Write-Host "=================================="

try {

    # Launch Notepad
    Start-Process notepad.exe

    Write-Host "Notepad launched successfully."

    exit 0

}
catch {

    Write-Host "Failed to launch Notepad."

    exit 1

}