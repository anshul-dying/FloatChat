import psycopg2
import pandas as pd
import yaml
from src.utils.logging import get_logger
import threading
import time

logger = get_logger(__name__)

# Simple connection cache (not a full pool, but better than nothing)
_connection_cache = {}
_cache_lock = threading.Lock()

def get_cached_connection():
    """Get a cached connection or create a new one"""
    thread_id = threading.get_ident()
    
    with _cache_lock:
        if thread_id in _connection_cache:
            conn = _connection_cache[thread_id]
            try:
                # Test if connection is still alive
                cursor = conn.cursor()
                cursor.execute("SELECT 1")
                cursor.close()
                return conn
            except:
                # Connection is dead, remove it
                try:
                    conn.close()
                except:
                    pass
                del _connection_cache[thread_id]
        
        # Create new connection
        config = load_config()
        conn_params = config["database"]["postgresql"]
        conn = psycopg2.connect(**conn_params)
        _connection_cache[thread_id] = conn
        return conn

def load_config():
    with open("config/config.yaml", "r") as f:
        return yaml.safe_load(f)

def execute_sql_query(query, timeout=15, max_rows=100):
    """Execute SQL query against PostgreSQL database with aggressive timeout and limits"""
    try:
        conn = get_cached_connection()
        cursor = conn.cursor()
        
        # Set aggressive statement timeout (15 seconds)
        cursor.execute(f"SET statement_timeout = {timeout * 1000}")  # Convert to milliseconds
        
        # Add LIMIT if not present and query looks like it could return many rows
        if not any(word in query.upper() for word in ['LIMIT', 'COUNT', 'GROUP BY', 'HAVING']):
            if 'SELECT' in query.upper() and 'FROM' in query.upper():
                query = f"{query.rstrip(';')} LIMIT {max_rows}"
        
        start_time = time.time()
        cursor.execute(query)
        results = cursor.fetchall()
        execution_time = time.time() - start_time
        
        # Get column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []
        
        cursor.close()
        
        # Convert to DataFrame for easier handling
        if results and columns:
            df = pd.DataFrame(results, columns=columns)
            logger.info(f"SQL query executed in {execution_time:.2f}s, returned {len(df)} rows")
            return df
        else:
            logger.info(f"SQL query executed in {execution_time:.2f}s, no results returned")
            return pd.DataFrame()
            
    except psycopg2.errors.QueryCanceled:
        logger.error(f"SQL query timed out after {timeout} seconds")
        raise Exception(f"Query timed out after {timeout} seconds. Try refining your query or reducing the data scope.")
    except Exception as e:
        logger.error(f"Failed to execute SQL query: {e}")
        raise

def query_vector_db(collection, query_text, n_results=5):
    """Query vector database for similar documents"""
    try:
        results = collection.query(query_texts=[query_text], n_results=n_results)
        logger.info(f"Vector query returned {len(results['documents'][0])} results")
        return results
    except Exception as e:
        logger.error(f"Failed to query vector database: {e}")
        raise

def get_argo_data_summary():
    """Get summary statistics of ARGO profile levels data in PostgreSQL"""
    query = """
        SELECT 
            COUNT(*) as total_records,
            COUNT(DISTINCT platform_number) as unique_platforms,
            COUNT(DISTINCT cycle_number) as unique_cycles,
            MIN(juld) as earliest_time,
            MAX(juld) as latest_time,
            MIN(latitude) as min_latitude,
            MAX(latitude) as max_latitude,
            MIN(longitude) as min_longitude,
            MAX(longitude) as max_longitude,
            MIN(pressure_dbar) as min_pressure,
            MAX(pressure_dbar) as max_pressure,
            AVG(temperature_c) as avg_temperature,
            AVG(salinity_psu) as avg_salinity,
            COUNT(CASE WHEN temp_qc = '1' THEN 1 END) as good_temp_readings,
            COUNT(CASE WHEN psal_qc = '1' THEN 1 END) as good_salinity_readings
        FROM argo_data
    """
    return execute_sql_query(query)