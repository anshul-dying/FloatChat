#!/usr/bin/env python3
"""
Script to load ARGO CSV data into PostgreSQL using efficient copy_from method
"""

import sys
import os
from pathlib import Path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.relational_db import init_db, insert_data_from_csv, get_data_count, test_postgresql_connection
from src.utils.logging import get_logger

logger = get_logger(__name__)

def load_argo_csv_to_postgresql(csv_file_path):
    """Load ARGO CSV data into PostgreSQL using copy_from method"""
    print("=" * 60)
    print("ARGO CSV Data Loading to PostgreSQL")
    print("Database: floatchat, Table: argo_data")
    print("=" * 60)
    
    # Check if CSV file exists
    csv_path = Path(csv_file_path)
    if not csv_path.exists():
        print(f"✗ CSV file not found: {csv_file_path}")
        return False
    
    print(f"✓ Found CSV file: {csv_file_path}")
    
    # Test PostgreSQL connection
    print("\n1. Testing PostgreSQL Connection...")
    success, info = test_postgresql_connection()
    if not success:
        print(f"✗ Connection failed: {info}")
        return False
    print(f"✓ Connection successful!")
    
    # Initialize database
    print("\n2. Initializing Database...")
    try:
        init_db()
        print("✓ Database initialized successfully!")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    # Get initial count
    initial_count = get_data_count()
    print(f"✓ Initial record count: {initial_count}")
    
    # Load data
    print(f"\n3. Loading data from {csv_file_path}...")
    try:
        insert_data_from_csv(csv_file_path)
        print("✓ Data loaded successfully!")
    except Exception as e:
        print(f"✗ Data loading failed: {e}")
        return False
    
    # Get final count
    final_count = get_data_count()
    print(f"✓ Final record count: {final_count}")
    print(f"✓ Records loaded: {final_count - initial_count}")
    
    print("\n" + "=" * 60)
    print("ARGO CSV Data Loading Completed Successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python load_argo_csv.py <path_to_csv_file>")
        print("Example: python load_argo_csv.py ../argo_profiles_long.csv")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    load_argo_csv_to_postgresql(csv_file)
