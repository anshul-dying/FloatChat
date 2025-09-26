@echo off
echo Converting NetCDF files to Parquet...

REM Activate virtual environment
call conda activate ./venv

REM Run NetCDF to Parquet conversion
echo Converting NetCDF files from data/raw to Parquet...
python src\data_ingestion\nc_to_parquet.py

echo NetCDF to Parquet conversion completed!
pause
