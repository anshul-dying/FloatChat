@echo off
echo Loading ARGO CSV data into PostgreSQL...

REM Activate virtual environment
call conda activate ./venv

REM Check if CSV file path is provided
if "%1"=="" (
    echo Usage: load_argo_csv.bat ^<path_to_csv_file^>
    echo Example: load_argo_csv.bat ../argo_profiles_long.csv
    pause
    exit /b 1
)

REM Load CSV data into PostgreSQL
echo Loading data from: %1
python scripts\load_argo_csv.py %1

echo CSV loading completed!
pause
