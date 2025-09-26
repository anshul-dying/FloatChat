"""
Comprehensive ARGO Data Download Script for FloatChat
Downloads ARGO data for Indian Ocean region with multiple time periods and parameters
"""

from pathlib import Path
import argopy
import pandas as pd
import xarray as xr
import yaml
import time
from datetime import datetime, timedelta
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_config():
    """Load configuration from config.yaml"""
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def setup_argopy():
    """Configure argopy for optimal data access"""
    # Set data source (default is 'erddap' which is good for most cases)
    argopy.set_options(src='erddap')
    
    # Optional: Set cache directory for faster repeated downloads
    cache_dir = Path("data/cache")
    cache_dir.mkdir(parents=True, exist_ok=True)
    argopy.set_options(cachedir=str(cache_dir))
    
    logger.info("Argopy configured successfully")

def download_indian_ocean_data():
    """Download comprehensive ARGO data for Indian Ocean region"""
    config = load_config()
    processed_path = Path(config["data"]["processed_path"])
    processed_path.mkdir(parents=True, exist_ok=True)
    
    setup_argopy()
    
    # Indian Ocean region definition
    # Longitude: 40°E to 100°E (covers Arabian Sea, Bay of Bengal, Andaman Sea)
    # Latitude: -20°S to 20°N (covers equatorial and tropical regions)
    lon_min, lon_max = 40, 100
    lat_min, lat_max = -20, 20
    
    logger.info(f"Downloading ARGO data for Indian Ocean region:")
    logger.info(f"Longitude: {lon_min}°E to {lon_max}°E")
    logger.info(f"Latitude: {lat_min}°S to {lat_max}°N")
    
    # Define time periods for comprehensive data coverage
    time_periods = [
        ('2022-01', '2022-12'),  # 2022 data
        ('2023-01', '2023-12'),  # 2023 data
        ('2024-01', '2024-12'),  # 2024 data (if available)
    ]
    
    all_dataframes = []
    
    for start_date, end_date in time_periods:
        logger.info(f"Downloading data for period: {start_date} to {end_date}")
        
        try:
            # Fetch data for this time period
            ds = argopy.DataFetcher().region([
                lon_min, lon_max, lat_min, lat_max, 
                0, 2000,  # Depth range: 0-2000m
                start_date, end_date
            ]).to_xarray()
            
            # Convert to DataFrame
            df = ds.to_dataframe()
            
            if not df.empty:
                logger.info(f"Downloaded {len(df)} records for {start_date}-{end_date}")
                all_dataframes.append(df)
            else:
                logger.warning(f"No data found for period {start_date}-{end_date}")
                
            # Add delay to avoid overwhelming the server
            time.sleep(2)
            
        except Exception as e:
            logger.error(f"Error downloading data for {start_date}-{end_date}: {e}")
            continue
    
    if all_dataframes:
        # Combine all dataframes
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Remove duplicates based on platform_number, cycle_number, and time
        combined_df = combined_df.drop_duplicates(
            subset=['PLATFORM_NUMBER', 'CYCLE_NUMBER', 'TIME'], 
            keep='first'
        )
        
        logger.info(f"Total combined records: {len(combined_df)}")
        
        # Save combined data
        output_file = processed_path / "argo_data_comprehensive.parquet"
        combined_df.to_parquet(output_file)
        logger.info(f"Saved comprehensive data to {output_file}")
        
        # Also save as backup with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_file = processed_path / f"argo_data_backup_{timestamp}.parquet"
        combined_df.to_parquet(backup_file)
        logger.info(f"Saved backup to {backup_file}")
        
        return combined_df
    else:
        logger.error("No data was successfully downloaded")
        return None

def download_specific_floats():
    """Download data for specific ARGO floats in Indian Ocean"""
    config = load_config()
    processed_path = Path(config["data"]["processed_path"])
    
    # Known Indian Ocean ARGO floats (you can expand this list)
    indian_ocean_floats = [
        '2901506', '2901507', '2901508',  # Example float IDs
        '1901443', '1901739', '1901804',  # More example floats
    ]
    
    logger.info(f"Downloading data for specific floats: {indian_ocean_floats}")
    
    all_dataframes = []
    
    for float_id in indian_ocean_floats:
        try:
            logger.info(f"Downloading data for float {float_id}")
            
            # Fetch data for specific float
            ds = argopy.DataFetcher().float(float_id).to_xarray()
            df = ds.to_dataframe()
            
            if not df.empty:
                logger.info(f"Downloaded {len(df)} records for float {float_id}")
                all_dataframes.append(df)
            else:
                logger.warning(f"No data found for float {float_id}")
                
            time.sleep(1)  # Delay between requests
            
        except Exception as e:
            logger.error(f"Error downloading data for float {float_id}: {e}")
            continue
    
    if all_dataframes:
        combined_df = pd.concat(all_dataframes, ignore_index=True)
        
        # Save specific floats data
        output_file = processed_path / "argo_data_specific_floats.parquet"
        combined_df.to_parquet(output_file)
        logger.info(f"Saved specific floats data to {output_file}")
        
        return combined_df
    else:
        logger.error("No specific float data was downloaded")
        return None

def download_recent_data():
    """Download recent ARGO data (last 6 months)"""
    config = load_config()
    processed_path = Path(config["data"]["processed_path"])
    
    # Calculate date range for last 6 months
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months ago
    
    start_str = start_date.strftime('%Y-%m')
    end_str = end_date.strftime('%Y-%m')
    
    logger.info(f"Downloading recent data: {start_str} to {end_str}")
    
    try:
        # Indian Ocean region
        ds = argopy.DataFetcher().region([
            40, 100, -20, 20,  # Indian Ocean bounds
            0, 2000,  # Depth range
            start_str, end_str
        ]).to_xarray()
        
        df = ds.to_dataframe()
        
        if not df.empty:
            output_file = processed_path / "argo_data_recent.parquet"
            df.to_parquet(output_file)
            logger.info(f"Saved recent data ({len(df)} records) to {output_file}")
            return df
        else:
            logger.warning("No recent data found")
            return None
            
    except Exception as e:
        logger.error(f"Error downloading recent data: {e}")
        return None

def main():
    """Main function to download ARGO data"""
    logger.info("Starting comprehensive ARGO data download...")
    
    # Option 1: Download comprehensive Indian Ocean data
    logger.info("=" * 60)
    logger.info("OPTION 1: Comprehensive Indian Ocean Data")
    logger.info("=" * 60)
    comprehensive_data = download_indian_ocean_data()
    
    # Option 2: Download specific floats
    logger.info("=" * 60)
    logger.info("OPTION 2: Specific Float Data")
    logger.info("=" * 60)
    specific_data = download_specific_floats()
    
    # Option 3: Download recent data
    logger.info("=" * 60)
    logger.info("OPTION 3: Recent Data (Last 6 months)")
    logger.info("=" * 60)
    recent_data = download_recent_data()
    
    # Summary
    logger.info("=" * 60)
    logger.info("DOWNLOAD SUMMARY")
    logger.info("=" * 60)
    
    if comprehensive_data is not None:
        logger.info(f"✅ Comprehensive data: {len(comprehensive_data)} records")
    else:
        logger.info("❌ Comprehensive data: Failed")
        
    if specific_data is not None:
        logger.info(f"✅ Specific floats data: {len(specific_data)} records")
    else:
        logger.info("❌ Specific floats data: Failed")
        
    if recent_data is not None:
        logger.info(f"✅ Recent data: {len(recent_data)} records")
    else:
        logger.info("❌ Recent data: Failed")
    
    logger.info("ARGO data download completed!")

if __name__ == "__main__":
    main()
