$ErrorActionPreference = "Stop"

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$python = Join-Path $projectRoot ".venv\Scripts\python.exe"
$launcher = Join-Path $projectRoot "run_desktop.bat"
$iconPath = Join-Path $projectRoot "static\img\luffy.ico"

if (-not (Test-Path $python)) {
    throw "Install the project requirements before creating the shortcut."
}

if (-not (Test-Path $iconPath)) {
    throw "The Luffy icon is missing: $iconPath"
}

$shell = New-Object -ComObject WScript.Shell
$shortcut = $shell.CreateShortcut(
    (Join-Path ([Environment]::GetFolderPath("Desktop")) "Luffy.lnk")
)
$shortcut.TargetPath = $launcher
$shortcut.WorkingDirectory = $projectRoot
$shortcut.IconLocation = "$iconPath,0"
$shortcut.Save()

Write-Output "Created the Luffy desktop shortcut for Barangay Bugay System."
