"""
Convert Argo NetCDF (profile files) into Parquet file
Based on the working ncToParquet_single.py code
"""

import os
import glob
import netCDF4 as nc
import numpy as np
import pandas as pd
from netCDF4 import num2date
from pathlib import Path
from src.utils.logging import get_logger

logger = get_logger(__name__)

# Configuration
PREFER_ADJUSTED = True
PARQUET_ENGINE = "pyarrow"
PARQUET_COMPRESSION = "snappy"

def safe_get_var(ds, preferred_names):
    """Safely get variable from NetCDF dataset"""
    for name in preferred_names:
        if name in ds.variables:
            return ds.variables[name], name
    return None, None

def to_numpy(arr):
    """Convert NetCDF array to numpy array, handling masked arrays"""
    if arr is None:
        return None
    if isinstance(arr, np.ma.MaskedArray):
        if np.issubdtype(arr.dtype, np.number):
            return np.array(arr.filled(np.nan))
        else:
            try:
                return np.array([
                    "".join(x).strip() if isinstance(x, (np.ndarray, list)) else x
                    for x in arr
                ])
            except Exception:
                return np.array(arr.tolist())
    return np.array(arr)

def process_file(ncfile):
    """Process a single NetCDF file and return DataFrame"""
    ds = nc.Dataset(ncfile, "r")
    logger.info(f"Processing file: {ncfile}")

    # Get variables with preference for adjusted values
    pres_var, pres_name = safe_get_var(ds, ["PRES_ADJUSTED", "PRES"])
    temp_var, temp_name = safe_get_var(ds, ["TEMP_ADJUSTED", "TEMP"])
    psal_var, psal_name = safe_get_var(ds, ["PSAL_ADJUSTED", "PSAL"])
    pres_qc_var, _ = safe_get_var(ds, ["PRES_ADJUSTED_QC", "PRES_QC"])
    temp_qc_var, _ = safe_get_var(ds, ["TEMP_ADJUSTED_QC", "TEMP_QC"])
    psal_qc_var, _ = safe_get_var(ds, ["PSAL_ADJUSTED_QC", "PSAL_QC"])

    # Get basic profile information
    lat_all = ds.variables["LATITUDE"][:]
    lon_all = ds.variables["LONGITUDE"][:]
    juld_var = ds.variables["JULD"]
    juld_units = getattr(juld_var, "units", None)
    cycle_num = ds.variables["CYCLE_NUMBER"][:] if "CYCLE_NUMBER" in ds.variables else None
    platform_number = ds.variables["PLATFORM_NUMBER"][:] if "PLATFORM_NUMBER" in ds.variables else None
    n_prof = lat_all.shape[0]

    rows = []

    for i in range(n_prof):
        # Extract profile-level data
        lat = float(np.array(lat_all[i]).item()) if not np.ma.is_masked(lat_all[i]) else np.nan
        lon = float(np.array(lon_all[i]).item()) if not np.ma.is_masked(lon_all[i]) else np.nan

        # Handle time conversion
        try:
            juld_arr = juld_var[:]
            juld_dt_i = num2date(juld_arr, juld_units)[i]
            juld_iso = juld_dt_i.isoformat()
        except Exception:
            juld_iso = str(juld_var[i])

        cyc = int(cycle_num[i]) if cycle_num is not None else None

        # Handle platform number conversion
        plat = None
        if platform_number is not None:
            try:
                plat = "".join([
                    c.decode("utf-8") if isinstance(c, bytes) else str(c)
                    for c in platform_number[i]
                ]).strip()
            except Exception:
                try:
                    plat = platform_number[i].tobytes().decode("utf-8").strip()
                except Exception:
                    plat = str(platform_number[i])

        # Get level data
        pres_vals = to_numpy(pres_var[i, :]) if pres_var is not None else None
        temp_vals = to_numpy(temp_var[i, :]) if temp_var is not None else None
        psal_vals = to_numpy(psal_var[i, :]) if psal_var is not None else None
        pres_qc_vals = to_numpy(pres_qc_var[i, :]) if pres_qc_var is not None else None
        temp_qc_vals = to_numpy(temp_qc_var[i, :]) if temp_qc_var is not None else None
        psal_qc_vals = to_numpy(psal_qc_var[i, :]) if psal_qc_var is not None else None

        # Determine number of levels
        n_levels = (
            pres_vals.shape[0]
            if pres_vals is not None else (
                temp_vals.shape[0]
                if temp_vals is not None else (
                    psal_vals.shape[0] if psal_vals is not None else 0
                )
            )
        )

        # Process each level
        for lev in range(n_levels):
            p = float(pres_vals[lev]) if pres_vals is not None else np.nan
            t = float(temp_vals[lev]) if temp_vals is not None else np.nan
            s = float(psal_vals[lev]) if psal_vals is not None else np.nan

            # Skip rows with no data
            if np.isnan(p) and np.isnan(t) and np.isnan(s):
                continue

            # Handle QC values properly - convert bytes to strings
            def safe_qc_convert(qc_val):
                if qc_val is None:
                    return None
                try:
                    # If it's a byte string, decode it
                    if isinstance(qc_val, bytes):
                        qc_str = qc_val.decode('utf-8').strip()
                    else:
                        qc_str = str(qc_val).strip()
                    
                    # Return as string (empty string for invalid values)
                    return qc_str if qc_str else None
                except (ValueError, UnicodeDecodeError):
                    return None

            rows.append({
                "source_file": os.path.basename(ncfile),
                "profile_index": int(i),
                "platform_number": plat,
                "cycle_number": cyc,
                "juld": juld_iso,
                "latitude": lat,
                "longitude": lon,
                "level_index": int(lev),
                "pressure_dbar": p,
                "temperature_c": t,
                "salinity_psu": s,
                "pres_qc": safe_qc_convert(pres_qc_vals[lev]) if pres_qc_vals is not None else None,
                "temp_qc": safe_qc_convert(temp_qc_vals[lev]) if temp_qc_vals is not None else None,
                "psal_qc": safe_qc_convert(psal_qc_vals[lev]) if psal_qc_vals is not None else None,
                "pres_variable": pres_name,
                "temp_variable": temp_name,
                "psal_variable": psal_name
            })

    ds.close()
    return pd.DataFrame(rows)

def find_files(path):
    """Find NetCDF files in the given path"""
    if os.path.isfile(path):
        return [path]
    patterns = ["*.nc", "*.nc4"]
    files = []
    for pat in patterns:
        files.extend(glob.glob(os.path.join(path, pat)))
    files.sort()
    return files

def convert_nc_to_parquet(input_path, output_path):
    """Convert NetCDF files to Parquet format"""
    logger.info(f"Starting NetCDF to Parquet conversion")
    logger.info(f"Input path: {input_path}")
    logger.info(f"Output path: {output_path}")
    
    # Find all NetCDF files
    files = find_files(input_path)
    logger.info(f"Found {len(files)} NetCDF files")
    
    if not files:
        logger.warning("No NetCDF files found!")
        return None
    
    # Process all files
    all_dfs = []
    total_rows = 0
    
    for f in files:
        try:
            df = process_file(f)
            total_rows += len(df)
            all_dfs.append(df)
            logger.info(f"Collected {len(df)} rows from {os.path.basename(f)}")
        except Exception as e:
            logger.error(f"Error processing {f}: {e}")
            continue
    
    if not all_dfs:
        logger.error("No data collected from any files!")
        return None
    
    # Combine all dataframes
    logger.info(f"Combining all {total_rows} rows...")
    final_df = pd.concat(all_dfs, ignore_index=True)
    
    # Ensure output directory exists
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # Write to Parquet
    logger.info(f"Writing to Parquet file: {output_path}")
    final_df.to_parquet(
        output_path,
        engine=PARQUET_ENGINE,
        compression=PARQUET_COMPRESSION,
        index=False
    )
    
    logger.info(f"Conversion completed! {len(final_df)} rows written to {output_path}")
    return final_df

def main():
    """Main function for command line usage"""
    from src.data_ingestion.ingest_argo import load_config
    
    config = load_config()
    raw_path = config["data"]["raw_path"]
    processed_path = config["data"]["processed_path"]
    
    # Set output file
    output_file = Path(processed_path) / "argo_profiles_long.parquet"
    
    # Convert NetCDF to Parquet
    result_df = convert_nc_to_parquet(raw_path, output_file)
    
    if result_df is not None:
        logger.info("NetCDF to Parquet conversion successful!")
        return result_df
    else:
        logger.error("NetCDF to Parquet conversion failed!")
        return None

if __name__ == "__main__":
    main()
