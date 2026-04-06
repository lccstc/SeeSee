param(
    [string]$PythonExe = "C:\Users\lccst\AppData\Local\Programs\Python\Python311\python.exe"
)

$ErrorActionPreference = "Stop"
$ProjectRoot = "C:\SeeSee\wxbot\bookkeeping-platform"

if (-not (Test-Path -LiteralPath $ProjectRoot)) {
    throw "Project root not found: $ProjectRoot"
}

if (-not (Test-Path -LiteralPath $PythonExe)) {
    throw "Python not found: $PythonExe"
}

Set-Location -LiteralPath $ProjectRoot
Write-Host "Starting WeChat adapter..." -ForegroundColor Cyan
Write-Host "Project: $ProjectRoot"
Write-Host "Python : $PythonExe"

& $PythonExe -m wechat_adapter.main
