@echo off
echo Building TUIO Bridge...
call .venv\Scripts\activate
pyinstaller tuio_bridge.spec --clean --noconfirm
echo.
if exist "dist\TUIO Bridge\TUIO Bridge.exe" (
    echo Build successful: dist\TUIO Bridge\TUIO Bridge.exe
) else (
    echo Build FAILED - check output above
)
pause
