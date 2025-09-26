from pathlib import Path
import yaml
from src.utils.logging import get_logger
from src.data_ingestion.complete_pipeline import run_complete_ingestion

logger = get_logger(__name__)

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def ingest_argo_data():
    """Ingest ARGO data using the complete pipeline: NetCDF -> Parquet -> PostgreSQL"""
    logger.info("Starting ARGO data ingestion using complete pipeline")
    
    try:
        success = run_complete_ingestion()
        if success:
            logger.info("ARGO data ingestion completed successfully!")
        else:
            logger.error("ARGO data ingestion failed!")
            raise Exception("Pipeline execution failed")
            
    except Exception as e:
        logger.error(f"Failed to ingest ARGO data: {e}")
        raise

if __name__ == "__main__":
    ingest_argo_data()