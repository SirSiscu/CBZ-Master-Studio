# Build script for CBZ Master Studio
# Requires PyInstaller: pip install pyinstaller

# Get the absolute paths relative to the script location
$ScriptDir = $PSScriptRoot
$ProjectRoot = (Get-Item $ScriptDir).Parent.FullName
$SrcDir = Join-Path $ProjectRoot "src"
$IconPath = Join-Path $SrcDir "assets\icon.ico"

Write-Host "Building CBZ Master Studio..." -ForegroundColor Cyan
Write-Host "Project Root: $ProjectRoot" -ForegroundColor Gray

# Check for icon
if (Test-Path $IconPath) {
    Write-Host "Found icon.ico" -ForegroundColor Green
    $IconArg = "--icon=`"$IconPath`""
}
else {
    Write-Host "Warning: icon.ico not found at $IconPath. Building without icon." -ForegroundColor Yellow
    $IconArg = ""
}

# Run PyInstaller via python -m to handle environments without PyInstaller in PATH
# --noconsole: Hide terminal window
# --onefile: Bundle everything into a single EXE
# --paths: Tell PyInstaller where to look for submodules
# --clean: Clear cache before building
python -m PyInstaller --noconsole --onefile --clean `
    $IconArg `
    --paths "`"$SrcDir`"" `
    --add-data "`"$SrcDir\assets;assets`"" `
    --name "CBZ_Master_Studio" `
    --distpath "`"$ProjectRoot\dist`"" `
    --workpath "`"$ProjectRoot\build`"" `
    --specpath "`"$ProjectRoot\build`"" `
    "`"$SrcDir\main.py`""

Write-Host "Build complete! The executable is in the 'dist' folder." -ForegroundColor Green
