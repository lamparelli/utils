@echo off
set "FOLDER_PATH=%~1"
if "%FOLDER_PATH%"=="" set /p "FOLDER_PATH=Enter folder path: "
"%~dp0venv\Scripts\python.exe" "%~dp0process_slides.py" --folder "%FOLDER_PATH%" --write 1 --no_watermark 1 --split_pages 1
echo.
pause
