$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$openrgb = if ($env:OPENRGB_DIR) { $env:OPENRGB_DIR } else { "C:\Program Files\OpenRGB" }
$version = (Select-String -Path "$root\app\rgbunitbars\__init__.py" -Pattern '"(.+)"').Matches[0].Groups[1].Value
$tocVersion = (Select-String -Path "$root\addon\RGBUnitBars\RGBUnitBars.toc" -Pattern '## Version: (.+)').Matches[0].Groups[1].Value
if ($version -ne $tocVersion) { throw "App version $version does not match addon version $tocVersion" }
if (-not (Test-Path "$openrgb\OpenRGB.exe")) { throw "OpenRGB not found in $openrgb (set OPENRGB_DIR)" }

python -m PyInstaller --noconfirm --clean --onefile --windowed --name RGBUnitBars `
    --icon "$root\packaging\icon.ico" --paths "$root\app" `
    --add-data "$openrgb;openrgb" --add-data "$root\packaging\THIRD_PARTY_NOTICES.md;." `
    --exclude-module numpy --exclude-module soundcard --exclude-module tkinter --exclude-module matplotlib `
    --distpath "$root\build\out" --workpath "$root\build\work" --specpath "$root\build" "$root\packaging\entry.py"
if ($LASTEXITCODE -ne 0) { throw "PyInstaller failed" }

New-Item -ItemType Directory -Force "$root\dist" | Out-Null
Copy-Item "$root\build\out\RGBUnitBars.exe" "$root\dist\RGBUnitBars-$version.exe" -Force
$zip = "$root\dist\RGBUnitBars-$version.zip"
if (Test-Path $zip) { Remove-Item $zip }
Compress-Archive -Path "$root\addon\RGBUnitBars" -DestinationPath $zip
Get-ChildItem "$root\dist\RGBUnitBars-$version*" | Select-Object Name, Length
