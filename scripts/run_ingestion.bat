@echo off
echo Starting ARGO data ingestion pipeline...
echo Flow: NetCDF files -> Parquet -> PostgreSQL -> Vector DB

REM Activate virtual environment
call conda activate ./venv

REM Run the complete ingestion pipeline (NetCDF -> Parquet -> PostgreSQL)
echo Running complete ARGO data ingestion pipeline...
python src\data_ingestion\ingest_argo.py

REM Extract metadata for vector database
echo Extracting metadata for vector database...
python src\data_ingestion\metadata_extractor.py

REM Initialize vector database with metadata
echo Initializing vector database...
python src\database\vector_db.py

echo Data ingestion pipeline completed successfully!
echo.
echo Summary:
echo - NetCDF files converted to Parquet
echo - Data loaded into PostgreSQL (floatchat.argo_data)
echo - Metadata extracted for vector search
echo - Vector database initialized
pause