"""
Simple ARGO Data Download Script for FloatChat
Downloads Indian Ocean ARGO data with progress tracking
"""

from pathlib import Path
import argopy
import pandas as pd
import xarray as xr
import yaml
import time
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def download_indian_ocean_argo():
    """Download ARGO data for Indian Ocean region"""
    config = load_config()
    processed_path = Path(config["data"]["processed_path"])
    processed_path.mkdir(parents=True, exist_ok=True)
    
    # Configure argopy
    argopy.set_options(src='erddap')
    logger.info("Argopy configured for ERDDAP data source")
    
    # Indian Ocean region definition
    # Longitude: 40°E to 100°E (Arabian Sea, Bay of Bengal, Andaman Sea)
    # Latitude: -20°S to 20°N (equatorial and tropical regions)
    lon_min, lon_max = 40, 100
    lat_min, lat_max = -20, 20
    
    logger.info("=" * 60)
    logger.info("🌊 DOWNLOADING INDIAN OCEAN ARGO DATA")
    logger.info("=" * 60)
    logger.info(f"Region: {lon_min}°E to {lon_max}°E, {lat_min}°S to {lat_max}°N")
    logger.info(f"Depth: 0-2000m")
    logger.info(f"Time: 2022-2024")
    
    try:
        # Download data for multiple years
        years = ['2022', '2023', '2024']
        all_dataframes = []
        
        for year in years:
            logger.info(f"📥 Downloading {year} data...")
            
            try:
                # Fetch data for this year
                ds = argopy.DataFetcher().region([
                    lon_min, lon_max, lat_min, lat_max,
                    0, 2000,  # Depth range: 0-2000m
                    f'{year}-01', f'{year}-12'
                ]).to_xarray()
                
                # Convert to DataFrame
                df = ds.to_dataframe()
                
                if not df.empty:
                    logger.info(f"✅ Downloaded {len(df)} records for {year}")
                    all_dataframes.append(df)
                else:
                    logger.warning(f"⚠️ No data found for {year}")
                    
                # Small delay to be nice to the server
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"❌ Error downloading {year} data: {e}")
                continue
        
        if all_dataframes:
            # Combine all data
            logger.info("🔄 Combining all data...")
            combined_df = pd.concat(all_dataframes, ignore_index=True)
            
            # Remove duplicates
            original_count = len(combined_df)
            combined_df = combined_df.drop_duplicates(
                subset=['PLATFORM_NUMBER', 'CYCLE_NUMBER', 'TIME'],
                keep='first'
            )
            final_count = len(combined_df)
            
            logger.info(f"📊 Data Summary:")
            logger.info(f"   Original records: {original_count}")
            logger.info(f"   After deduplication: {final_count}")
            logger.info(f"   Removed duplicates: {original_count - final_count}")
            
            # Save the data
            output_file = processed_path / "argo_data.parquet"
            combined_df.to_parquet(output_file)
            logger.info(f"💾 Saved data to: {output_file}")
            
            # Show data summary
            logger.info("=" * 60)
            logger.info("📈 DATA SUMMARY")
            logger.info("=" * 60)
            logger.info(f"Total records: {len(combined_df)}")
            logger.info(f"Unique floats: {combined_df['PLATFORM_NUMBER'].nunique()}")
            logger.info(f"Date range: {combined_df['TIME'].min()} to {combined_df['TIME'].max()}")
            logger.info(f"Latitude range: {combined_df['LATITUDE'].min():.2f}° to {combined_df['LATITUDE'].max():.2f}°")
            logger.info(f"Longitude range: {combined_df['LONGITUDE'].min():.2f}° to {combined_df['LONGITUDE'].max():.2f}°")
            
            # Show available parameters
            params = ['TEMP', 'PSAL', 'PRES']
            available_params = [p for p in params if p in combined_df.columns]
            logger.info(f"Available parameters: {', '.join(available_params)}")
            
            logger.info("=" * 60)
            logger.info("✅ DOWNLOAD COMPLETED SUCCESSFULLY!")
            logger.info("=" * 60)
            
            return combined_df
        else:
            logger.error("❌ No data was downloaded")
            return None
            
    except Exception as e:
        logger.error(f"❌ Fatal error during download: {e}")
        return None

def download_sample_data():
    """Download a small sample for testing"""
    config = load_config()
    processed_path = Path(config["data"]["processed_path"])
    processed_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("📥 Downloading sample data for testing...")
    
    try:
        # Download just one month of data
        ds = argopy.DataFetcher().region([
            40, 100, -20, 20,  # Indian Ocean bounds
            0, 1000,  # Depth: 0-1000m
            '2023-03', '2023-04'  # Just March-April 2023
        ]).to_xarray()
        
        df = ds.to_dataframe()
        
        if not df.empty:
            output_file = processed_path / "argo_data_sample.parquet"
            df.to_parquet(output_file)
            logger.info(f"✅ Sample data saved: {len(df)} records")
            logger.info(f"💾 File: {output_file}")
            return df
        else:
            logger.error("❌ No sample data found")
            return None
            
    except Exception as e:
        logger.error(f"❌ Error downloading sample: {e}")
        return None

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "sample":
        download_sample_data()
    else:
        download_indian_ocean_argo()
