#!/usr/bin/env python3
"""
Script to recreate the argo_data table with correct schema
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.relational_db import load_config, test_postgresql_connection
from src.utils.logging import get_logger
import psycopg2

logger = get_logger(__name__)

def recreate_argo_table():
    """Drop and recreate the argo_data table with correct schema"""
    print("=" * 60)
    print("Recreating argo_data table with correct schema")
    print("=" * 60)
    
    # Test connection first
    success, info = test_postgresql_connection()
    if not success:
        print(f"✗ Connection failed: {info}")
        return False
    
    print("✓ PostgreSQL connection successful")
    
    # Get database configuration
    config = load_config()
    conn_params = config["database"]["postgresql"]
    
    try:
        conn = psycopg2.connect(**conn_params)
        cursor = conn.cursor()
        
        # Drop existing table
        print("Dropping existing argo_data table...")
        cursor.execute("DROP TABLE IF EXISTS argo_data CASCADE")
        
        # Create new table with correct schema
        print("Creating new argo_data table...")
        cursor.execute("""
            CREATE TABLE argo_data (
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
        
        # Create indexes
        print("Creating indexes...")
        cursor.execute("CREATE INDEX idx_argo_platform ON argo_data(platform_number);")
        cursor.execute("CREATE INDEX idx_argo_cycle ON argo_data(cycle_number);")
        cursor.execute("CREATE INDEX idx_argo_time ON argo_data(juld);")
        cursor.execute("CREATE INDEX idx_argo_location ON argo_data(latitude, longitude);")
        cursor.execute("CREATE INDEX idx_argo_pressure ON argo_data(pressure_dbar);")
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print("✓ Table recreated successfully!")
        print("✓ QC columns are now VARCHAR(10) to handle byte strings")
        return True
        
    except Exception as e:
        print(f"✗ Failed to recreate table: {e}")
        return False

if __name__ == "__main__":
    recreate_argo_table()
