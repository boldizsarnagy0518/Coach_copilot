# Restart Coach Copilot server
# Usage: .\restart.ps1

Write-Host "Stopping any running Python servers..." -ForegroundColor Yellow
Get-Process | Where-Object { $_.ProcessName -like "*python*" } | Stop-Process -Force -ErrorAction SilentlyContinue

Start-Sleep -Seconds 2

Write-Host "Starting Coach Copilot..." -ForegroundColor Green
uv run coach
