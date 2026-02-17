"""
data_loader.py
==============
Loads and validates flood-risk input CSVs.

Required columns : timestamp, rainfall_mm, soil_moisture, river_discharge_m3s
Optional columns : groundwater_index, impervious_fraction
"""

import pandas as pd
from pathlib import Path


REQUIRED_COLS = ["timestamp", "rainfall_mm", "soil_moisture", "river_discharge_m3s"]
OPTIONAL_COLS = ["groundwater_index", "impervious_fraction"]


def load_csv(path: str | Path) -> pd.DataFrame:
    """
    Load a flood CSV, parse timestamps, validate schema, and return a clean DataFrame.

    Parameters
    ----------
    path : str or Path
        Path to the CSV file.

    Returns
    -------
    pd.DataFrame
        Cleaned DataFrame indexed by timestamp (hourly resolution expected).

    Raises
    ------
    ValueError
        If required columns are missing or data types cannot be coerced.
    """
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"CSV not found: {path}")

    df = pd.read_csv(path, parse_dates=["timestamp"])

    # --- validate required columns ---
    missing = [c for c in REQUIRED_COLS if c not in df.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    # --- coerce numeric columns ---
    numeric_cols = [c for c in REQUIRED_COLS[1:] + OPTIONAL_COLS if c in df.columns]
    for col in numeric_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # --- clip physical ranges ---
    df["soil_moisture"] = df["soil_moisture"].clip(0.0, 1.0)
    df["river_discharge_m3s"] = df["river_discharge_m3s"].clip(lower=0.0)
    df["rainfall_mm"] = df["rainfall_mm"].clip(lower=0.0)

    if "groundwater_index" in df.columns:
        df["groundwater_index"] = df["groundwater_index"].clip(0.0, 1.0)
    if "impervious_fraction" in df.columns:
        df["impervious_fraction"] = df["impervious_fraction"].clip(0.0, 1.0)

    df = df.sort_values("timestamp").reset_index(drop=True)
    df = df.set_index("timestamp")

    n_null = df[numeric_cols].isnull().sum().sum()
    if n_null > 0:
        print(f"  [data_loader] Warning: {n_null} NaN values found after coercion — forward-filling.")
        df[numeric_cols] = df[numeric_cols].ffill().bfill()

    print(f"  [data_loader] Loaded '{path.name}': {len(df)} hourly rows "
          f"({df.index[0].date()} → {df.index[-1].date()})")
    return df
