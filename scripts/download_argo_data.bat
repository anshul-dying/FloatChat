@echo off
echo 🌊 FloatChat ARGO Data Download
echo ================================
echo.
echo This script will download ARGO data for the Indian Ocean region
echo Data will be saved to: data\processed\argo_data.parquet
echo.
echo Choose download option:
echo 1. Full Indian Ocean data (2022-2024) - Large download
echo 2. Sample data (March-April 2023) - Quick test
echo.
set /p choice="Enter your choice (1 or 2): "

if "%choice%"=="1" (
    echo.
    echo 📥 Downloading full Indian Ocean ARGO data...
    echo This may take several minutes depending on your internet connection
    echo.
    python src\data_ingestion\get_argo_data.py
) else if "%choice%"=="2" (
    echo.
    echo 📥 Downloading sample ARGO data...
    echo.
    python src\data_ingestion\get_argo_data.py sample
) else (
    echo Invalid choice. Please run the script again and choose 1 or 2.
    pause
    exit
)

echo.
echo ✅ Download completed!
echo.
echo Next steps:
echo 1. Run metadata extraction: python src\data_ingestion\metadata_extractor.py
echo 2. Start the API server: python src\api\main.py
echo 3. Start the frontend: streamlit run src\frontend\chat_interface.py
echo.
pause
