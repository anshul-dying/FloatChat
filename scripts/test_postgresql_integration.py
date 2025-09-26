#!/usr/bin/env python3
"""
Test script to verify PostgreSQL integration with ARGO data storage
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.database.relational_db import (
    test_postgresql_connection, 
    init_db, 
    get_data_count, 
    query_data
)
from src.database.query_engine import get_argo_data_summary
from src.utils.logging import get_logger

logger = get_logger(__name__)

def test_postgresql_integration():
    """Test complete PostgreSQL integration"""
    print("=" * 60)
    print("PostgreSQL Integration Test")
    print("=" * 60)
    
    # Test 1: Connection
    print("\n1. Testing PostgreSQL Connection...")
    success, info = test_postgresql_connection()
    if success:
        print(f"✓ Connection successful!")
        print(f"  PostgreSQL version: {info}")
    else:
        print(f"✗ Connection failed: {info}")
        return False
    
    # Test 2: Database Initialization
    print("\n2. Testing Database Initialization...")
    try:
        init_db()
        print("✓ Database initialized successfully!")
    except Exception as e:
        print(f"✗ Database initialization failed: {e}")
        return False
    
    # Test 3: Data Count
    print("\n3. Testing Data Count...")
    count = get_data_count()
    print(f"✓ Current data count: {count} records")
    
    # Test 4: Data Query
    print("\n4. Testing Data Query...")
    if count > 0:
        try:
            sample_data = query_data(limit=5)
            print(f"✓ Retrieved {len(sample_data)} sample records")
            if sample_data:
                print("  Sample record:")
                print(f"    Platform: {sample_data[0][0]}")
                print(f"    Location: ({sample_data[0][1]:.4f}, {sample_data[0][2]:.4f})")
                print(f"    Time: {sample_data[0][3]}")
                print(f"    Pressure: {sample_data[0][4]} dbar")
                print(f"    Temperature: {sample_data[0][5]}°C")
                print(f"    Salinity: {sample_data[0][6]} PSU")
                print(f"    Cycle: {sample_data[0][7]}")
                print(f"    Level: {sample_data[0][8]}")
        except Exception as e:
            print(f"✗ Data query failed: {e}")
            return False
    else:
        print("ℹ No data found - run CSV loading first")
    
    # Test 5: Summary Statistics
    print("\n5. Testing Summary Statistics...")
    if count > 0:
        try:
            summary = get_argo_data_summary()
            if not summary.empty:
                print("✓ Summary statistics retrieved:")
                row = summary.iloc[0]
                print(f"  Total records: {row['total_records']}")
                print(f"  Unique platforms: {row['unique_platforms']}")
                print(f"  Unique cycles: {row['unique_cycles']}")
                print(f"  Time range: {row['earliest_time']} to {row['latest_time']}")
                print(f"  Latitude range: {row['min_latitude']:.4f} to {row['max_latitude']:.4f}")
                print(f"  Longitude range: {row['min_longitude']:.4f} to {row['max_longitude']:.4f}")
                print(f"  Pressure range: {row['min_pressure']:.2f} to {row['max_pressure']:.2f} dbar")
                print(f"  Average temperature: {row['avg_temperature']:.4f}°C")
                print(f"  Average salinity: {row['avg_salinity']:.4f} PSU")
                print(f"  Good temperature readings: {row['good_temp_readings']}")
                print(f"  Good salinity readings: {row['good_salinity_readings']}")
            else:
                print("ℹ No summary data available")
        except Exception as e:
            print(f"✗ Summary statistics failed: {e}")
            return False
    else:
        print("ℹ No data available for summary statistics")
    
    print("\n" + "=" * 60)
    print("PostgreSQL Integration Test Completed Successfully!")
    print("=" * 60)
    return True

if __name__ == "__main__":
    test_postgresql_integration()
