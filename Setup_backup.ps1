# Setup.ps1 - Automated Setup for Alert Agent System
# This script automates steps from SLM_Guide.docx

Write-Host "--- SLM Setup Script Starting ---`n"

# 2. Check Python Installation
Write-Host "[Step 2] Checking Python installation..."
$pythonVersion = & python --version 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "Python is not installed or not in PATH. Please install Python 3.11+ and enable 'Add Python to PATH'."
    Start-Process "https://www.python.org/downloads/"
    exit 1
} else {
    Write-Host "Python version found: $pythonVersion"
}

# 3. Show Python Path and Suggest Path Update
Write-Host "[Step 3] Checking Python executable path..."
$pythonPath = (Get-Command python).Source
Write-Host "Python executable path: $pythonPath"
Write-Host "If project files contain old Python paths, update them to: $pythonPath"
Write-Host "Files to check: start_system.bat, module1.ps1, setup_scheduletask.ps1"

# 4. Enable PowerShell Script Execution
Write-Host "[Step 4] Setting PowerShell execution policy... (Requires Admin)"
try {
    Set-ExecutionPolicy RemoteSigned -Scope LocalMachine -Force
    Write-Host "Execution policy set to RemoteSigned."
} catch {
    Write-Host "Failed to set execution policy. Please run this script as Administrator."
}

# 5. Run Task Scheduler Setup
Write-Host "[Step 5] Creating Task Scheduler job... (Requires Admin)"
if (Test-Path "./setup_scheduletask.ps1") {
    try {
        & ./setup_scheduletask.ps1
        Write-Host "Task Scheduler job created."
    } catch {
        Write-Host "Failed to run setup_scheduletask.ps1. Please check for errors."
    }
} else {
    Write-Host "setup_scheduletask.ps1 not found in current directory."
}


# 6. Ollama Installation (Automated)
$ollamaInstaller = "$env:TEMP\OllamaSetup.exe"
if (-not (Get-Command ollama -ErrorAction SilentlyContinue)) {
    Write-Host "[Step 6] Downloading and installing Ollama..."
    try {
        Invoke-WebRequest -Uri "https://ollama.com/download/OllamaSetup.exe" -OutFile $ollamaInstaller -UseBasicParsing
        Write-Host "Running Ollama installer... (may require admin privileges)"
        Start-Process -FilePath $ollamaInstaller -Wait
        Write-Host "Ollama installation completed."
    } catch {
        Write-Host "Failed to download or install Ollama. Please install manually from: https://ollama.com/download/OllamaSetup.exe"
    }
} else {
    Write-Host "Ollama is already installed."
}
Write-Host "After installation, run: ollama run phi3:mini"

# 7. Install Required Python Libraries
Write-Host "[Step 7] Installing required Python libraries..."
$requirements = @('requests', 'watchdog', 'flask')
foreach ($pkg in $requirements) {
    Write-Host "Installing $pkg..."
    pip install $pkg
}

.\start_system.bat

Write-Host "--- SLM Setup Script Complete ---"
