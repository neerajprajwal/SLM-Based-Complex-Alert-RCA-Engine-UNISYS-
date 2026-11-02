while ($true) {

    Write-Host "🚀 Running Alert Pipeline..."

    powershell `
        -ExecutionPolicy Bypass `
        -File "$PSScriptRoot\module1.ps1"

    Write-Host "⏳ Waiting 30 seconds..."

    Start-Sleep -Seconds 30
}