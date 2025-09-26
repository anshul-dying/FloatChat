import psycopg2
import pandas as pd
import yaml
from pathlib import Path
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def init_db():
    """Initialize PostgreSQL database and create tables"""
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Create table for ARGO profile levels data (matching actual ARGO data structure)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS argo_data (
                id SERIAL PRIMARY KEY,
                source_file VARCHAR(255),
                profile_index INTEGER,
                platform_number VARCHAR(20),
                cycle_number INTEGER,
                juld TIMESTAMP,
                latitude DECIMAL(10, 6),
                longitude DECIMAL(10, 6),
                level_index INTEGER,
                pressure_dbar DECIMAL(10, 2),
                temperature_c DECIMAL(10, 4),
                salinity_psu DECIMAL(10, 4),
                pres_qc VARCHAR(10),
                temp_qc VARCHAR(10),
                psal_qc VARCHAR(10),
                pres_variable VARCHAR(50),
                temp_variable VARCHAR(50),
                psal_variable VARCHAR(50),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create indexes for better query performance
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_argo_platform ON argo_data(platform_number);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_argo_cycle ON argo_data(cycle_number);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_argo_time ON argo_data(juld);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_argo_location ON argo_data(latitude, longitude);
        """)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_argo_pressure ON argo_data(pressure_dbar);
        """)
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info("Initialized PostgreSQL database with argo_data table and indexes")
        
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL database: {e}")
        raise

def insert_data_from_csv(csv_file_path):
    """Insert ARGO data from CSV file using efficient copy_from method"""
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Clear existing data to avoid duplicates
        cursor.execute("DELETE FROM argo_data")
        logger.info("Cleared existing ARGO data from PostgreSQL")
        
        # Define column mapping for copy_from
        db_columns = (
            'source_file', 'profile_index', 'platform_number', 'cycle_number', 'juld',
            'latitude', 'longitude', 'level_index', 'pressure_dbar', 'temperature_c',
            'salinity_psu', 'pres_qc', 'temp_qc', 'psal_qc', 'pres_variable',
            'temp_variable', 'psal_variable'
        )
        
        # Use copy_from for efficient bulk loading
        with open(csv_file_path, "r") as f:
            next(f)  # Skip header row
            cursor.copy_from(
                file=f,
                table="argo_data",
                sep=",",
                columns=db_columns,
                null=""
            )
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Successfully loaded data from {csv_file_path} into PostgreSQL using copy_from")
        
    except Exception as e:
        logger.error(f"Failed to insert data from CSV into PostgreSQL: {e}")
        raise

def insert_data(df):
    """Insert ARGO data from DataFrame into PostgreSQL database"""
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Clear existing data to avoid duplicates
        cursor.execute("DELETE FROM argo_data")
        logger.info("Cleared existing ARGO data from PostgreSQL")
        
        # Prepare data for insertion
        insert_count = 0
        batch_size = 1000
        
        for i in range(0, len(df), batch_size):
            batch_df = df.iloc[i:i+batch_size]
            batch_data = []
            
            for _, row in batch_df.iterrows():
                # Map ARGO data columns to database columns
                # Handle different possible column names
                source_file = None
                profile_index = None
                platform_number = None
                cycle_number = None
                juld = None
                latitude = None
                longitude = None
                level_index = None
                pressure_dbar = None
                temperature_c = None
                salinity_psu = None
                pres_qc = None
                temp_qc = None
                psal_qc = None
                pres_variable = None
                temp_variable = None
                psal_variable = None
                
                # Try to find the correct columns
                for col in df.columns:
                    col_lower = col.lower()
                    if 'source_file' in col_lower:
                        source_file = str(row[col]) if pd.notna(row[col]) else None
                    elif 'profile_index' in col_lower:
                        profile_index = int(row[col]) if pd.notna(row[col]) else None
                    elif 'platform' in col_lower or 'float' in col_lower:
                        platform_number = str(row[col]) if pd.notna(row[col]) else None
                    elif 'cycle' in col_lower:
                        cycle_number = int(row[col]) if pd.notna(row[col]) else None
                    elif 'juld' in col_lower or 'time' in col_lower:
                        juld = row[col] if pd.notna(row[col]) else None
                    elif 'lat' in col_lower:
                        latitude = float(row[col]) if pd.notna(row[col]) else None
                    elif 'lon' in col_lower:
                        longitude = float(row[col]) if pd.notna(row[col]) else None
                    elif 'level_index' in col_lower:
                        level_index = int(row[col]) if pd.notna(row[col]) else None
                    elif 'pressure' in col_lower or 'pres' in col_lower:
                        pressure_dbar = float(row[col]) if pd.notna(row[col]) else None
                    elif 'temp' in col_lower or 'temperature' in col_lower:
                        temperature_c = float(row[col]) if pd.notna(row[col]) else None
                    elif 'psal' in col_lower or 'salinity' in col_lower:
                        salinity_psu = float(row[col]) if pd.notna(row[col]) else None
                    elif 'pres_qc' in col_lower:
                        pres_qc = int(row[col]) if pd.notna(row[col]) else None
                    elif 'temp_qc' in col_lower:
                        temp_qc = int(row[col]) if pd.notna(row[col]) else None
                    elif 'psal_qc' in col_lower:
                        psal_qc = int(row[col]) if pd.notna(row[col]) else None
                    elif 'pres_variable' in col_lower:
                        pres_variable = str(row[col]) if pd.notna(row[col]) else None
                    elif 'temp_variable' in col_lower:
                        temp_variable = str(row[col]) if pd.notna(row[col]) else None
                    elif 'psal_variable' in col_lower:
                        psal_variable = str(row[col]) if pd.notna(row[col]) else None
                
                # Only insert if we have essential data
                if platform_number and latitude is not None and longitude is not None:
                    batch_data.append((
                        source_file, profile_index, platform_number, cycle_number, juld,
                        latitude, longitude, level_index, pressure_dbar, temperature_c,
                        salinity_psu, pres_qc, temp_qc, psal_qc, pres_variable,
                        temp_variable, psal_variable
                    ))
            
            # Insert batch
            if batch_data:
                cursor.executemany("""
                    INSERT INTO argo_data (
                        source_file, profile_index, platform_number, cycle_number, juld,
                        latitude, longitude, level_index, pressure_dbar, temperature_c,
                        salinity_psu, pres_qc, temp_qc, psal_qc, pres_variable,
                        temp_variable, psal_variable
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """, batch_data)
                insert_count += len(batch_data)
                logger.info(f"Inserted batch of {len(batch_data)} records")
        
        conn.commit()
        cursor.close()
        conn.close()
        logger.info(f"Successfully inserted {insert_count} records into PostgreSQL")
        
    except Exception as e:
        logger.error(f"Failed to insert data into PostgreSQL: {e}")
        raise

def get_data_count():
    """Get count of records in argo_data table"""
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM argo_data")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count
    except Exception as e:
        logger.error(f"Failed to get data count: {e}")
        return 0

def query_data(limit=100):
    """Query ARGO profile levels data from PostgreSQL"""
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute(f"""
            SELECT platform_number, latitude, longitude, juld, pressure_dbar, 
                   temperature_c, salinity_psu, cycle_number, level_index
            FROM argo_data 
            ORDER BY created_at DESC 
            LIMIT %s
        """, (limit,))
        
        results = cursor.fetchall()
        cursor.close()
        conn.close()
        
        return results
    except Exception as e:
        logger.error(f"Failed to query data: {e}")
        return []

def test_postgresql_connection():
    """Test PostgreSQL connection and return status"""
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        cursor.execute("SELECT version();")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        
        logger.info(f"PostgreSQL connection successful. Version: {version}")
        return True, version
    except Exception as e:
        logger.error(f"PostgreSQL connection failed: {e}")
        return False, str(e)

if __name__ == "__main__":
    init_db()