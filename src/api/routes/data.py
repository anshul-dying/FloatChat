from flask import Blueprint, request, jsonify
from src.database.query_engine import execute_sql_query
from src.utils.logging import get_logger
import os
import pandas as pd
import duckdb

data_bp = Blueprint("data", __name__)
logger = get_logger(__name__)

@data_bp.route("/data", methods=["GET"])
def get_data():
    query = request.args.get("query", default="")
    results = execute_sql_query(query)
    return jsonify({"results": results})

@data_bp.route("/parquet", methods=["GET"])
def get_parquet():
    """Return rows from a processed parquet file without PostgreSQL.

    Query params:
      - file: optional parquet filename in data/processed (default: argo_profiles_long.parquet)
      - limit: max rows to return (default: 500)
    """
    filename = request.args.get("file", default="argo_profiles_long.parquet")
    try:
        limit = int(request.args.get("limit", default="500"))
    except ValueError:
        limit = 500

    base_dir = os.path.join("data", "processed")
    safe_path = os.path.normpath(os.path.join(base_dir, filename))
    if not safe_path.startswith(os.path.abspath(base_dir)) and not safe_path.startswith(base_dir):
        return jsonify({"error": "Invalid path"}), 400

    if not os.path.isfile(safe_path):
        return jsonify({"error": f"File not found: {filename}"}), 404

    try:
        df = pd.read_parquet(safe_path)
        if limit > 0:
            df = df.head(limit)
        records = df.to_dict(orient="records")
        return jsonify({"results": records, "file": filename, "count": len(records)})
    except Exception as e:
        logger.error(f"Failed reading parquet {filename}: {e}")
        return jsonify({"error": str(e)}), 500

@data_bp.route("/parquet_sql", methods=["POST"])
def parquet_sql():
    """Execute a SQL query against one or more Parquet files using DuckDB.

    Body JSON:
      - query: required SQL query string
      - files: optional list of parquet filenames in data/processed
      - limit: optional max rows to return (default 500)
    """
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    files = body.get("files") or ["argo_profiles_long.parquet"]
    try:
        limit = int(body.get("limit") or 500)
    except Exception:
        limit = 500

    if not query:
        return jsonify({"error": "Missing SQL query"}), 400

    base_dir = os.path.join("data", "processed")

    resolved = []
    for fname in files:
        safe_path = os.path.normpath(os.path.join(base_dir, fname))
        if not safe_path.startswith(os.path.abspath(base_dir)) and not safe_path.startswith(base_dir):
            return jsonify({"error": f"Invalid path: {fname}"}), 400
        if not os.path.isfile(safe_path):
            return jsonify({"error": f"File not found: {fname}"}), 404
        resolved.append(safe_path)

    try:
        con = duckdb.connect()
        # Register each parquet as a view p0, p1, ...
        for idx, path in enumerate(resolved):
            # DuckDB does not allow parameters in DDL; embed sanitized literal
            safe_literal = path.replace("'", "''")
            con.execute(f"CREATE OR REPLACE VIEW p{idx} AS SELECT * FROM read_parquet('{safe_literal}')")

        # Safeguard: append LIMIT if none present on a plain SELECT
        q_upper = query.upper()
        if "SELECT" in q_upper and " FROM " in q_upper and " LIMIT " not in q_upper:
            query = f"{query.rstrip(';')} LIMIT {limit}"

        df = con.execute(query).fetch_df()
        records = df.to_dict(orient="records")
        return jsonify({"results": records, "count": len(records)})
    except Exception as e:
        logger.error(f"DuckDB parquet_sql error: {e}")
        return jsonify({"error": str(e)}), 500

@data_bp.route("/sql", methods=["POST"])
def postgres_sql():
    """Execute SQL against PostgreSQL with safety limits."""
    body = request.get_json(silent=True) or {}
    query = (body.get("query") or "").strip()
    try:
        limit = int(body.get("limit") or 200)
    except Exception:
        limit = 200

    if not query:
        return jsonify({"error": "Missing SQL query"}), 400

    try:
        df = execute_sql_query(query, timeout=15, max_rows=limit)
        records = df.to_dict(orient="records")
        return jsonify({"results": records, "count": len(records)})
    except Exception as e:
        logger.error(f"Postgres SQL error: {e}")
        return jsonify({"error": str(e)}), 500
