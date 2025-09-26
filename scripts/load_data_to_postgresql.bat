@echo off
echo Loading Parquet/CSV data into PostgreSQL...

REM Activate virtual environment
call conda activate ./venv

REM Check if Parquet file exists
if exist "data\processed\argo_profiles_long.parquet" (
    echo Found Parquet file, converting to CSV first...
    python -c "import pandas as pd; df = pd.read_parquet('data/processed/argo_profiles_long.parquet'); df.to_csv('data/processed/argo_profiles_long.csv', index=False); print(f'Converted {len(df)} records to CSV')"
    
    echo Loading CSV data into PostgreSQL...
    python scripts\load_argo_csv.py data\processed\argo_profiles_long.csv
) else if exist "data\processed\argo_profiles_long.csv" (
    echo Found CSV file, loading directly...
    python scripts\load_argo_csv.py data\processed\argo_profiles_long.csv
) else (
    echo No Parquet or CSV file found in data/processed/
    echo Please run the NetCDF conversion first or place your CSV file there.
)

echo Data loading completed!
pause
