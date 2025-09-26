"""
Complete ARGO data ingestion pipeline: NetCDF -> Parquet -> PostgreSQL
"""

from pathlib import Path
import pandas as pd
import yaml
from src.utils.logging import get_logger
from src.data_ingestion.nc_to_parquet import convert_nc_to_parquet
from src.database.relational_db import init_db, insert_data_from_csv

logger = get_logger(__name__)

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def run_complete_ingestion():
    """Run the complete ARGO data ingestion pipeline"""
    config = load_config()
    raw_path = Path(config["data"]["raw_path"])
    processed_path = Path(config["data"]["processed_path"])
    processed_path.mkdir(parents=True, exist_ok=True)
    
    logger.info("Starting complete ARGO data ingestion pipeline")
    logger.info(f"Raw data path: {raw_path}")
    logger.info(f"Processed data path: {processed_path}")
    
    try:
        # Step 1: Convert NetCDF files to Parquet
        logger.info("Step 1: Converting NetCDF files to Parquet...")
        parquet_file = processed_path / "argo_profiles_long.parquet"
        
        result_df = convert_nc_to_parquet(raw_path, parquet_file)
        
        if result_df is None or len(result_df) == 0:
            logger.error("No data converted from NetCDF files!")
            return False
        
        logger.info(f"✓ Successfully converted {len(result_df)} records to Parquet")
        
        # Step 2: Initialize PostgreSQL database
        logger.info("Step 2: Initializing PostgreSQL database...")
        init_db()
        logger.info("✓ PostgreSQL database initialized")
        
        # Step 3: Load Parquet data into PostgreSQL
        logger.info("Step 3: Loading Parquet data into PostgreSQL...")
        
        # Convert Parquet to CSV for copy_from method
        csv_file = processed_path / "argo_profiles_long.csv"
        result_df.to_csv(csv_file, index=False)
        logger.info(f"✓ Converted Parquet to CSV: {csv_file}")
        
        # Load CSV into PostgreSQL using copy_from
        insert_data_from_csv(csv_file)
        logger.info("✓ Data loaded into PostgreSQL successfully")
        
        # Step 4: Verify data
        from src.database.relational_db import get_data_count
        count = get_data_count()
        logger.info(f"✓ Verification: {count} records in PostgreSQL database")
        
        logger.info("=" * 60)
        logger.info("ARGO DATA INGESTION PIPELINE COMPLETED SUCCESSFULLY!")
        logger.info("=" * 60)
        logger.info(f"NetCDF files processed: {len(list(raw_path.glob('*.nc')))}")
        logger.info(f"Records converted: {len(result_df)}")
        logger.info(f"Records in PostgreSQL: {count}")
        logger.info(f"Parquet file: {parquet_file}")
        logger.info(f"CSV file: {csv_file}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        raise

def main():
    """Main function for command line usage"""
    success = run_complete_ingestion()
    if success:
        logger.info("Pipeline completed successfully!")
    else:
        logger.error("Pipeline failed!")
        exit(1)

if __name__ == "__main__":
    main()
