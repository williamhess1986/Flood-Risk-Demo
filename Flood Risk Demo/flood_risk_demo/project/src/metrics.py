"""
metrics.py
==========
Computes all flood-risk metrics from hourly input data.

Metrics
-------
EFD   : Effective Flood Driver         (hourly)
CFL   : Cumulative Flood Load          (daily + running cumulative)
PSe   : Persistent Saturation Excess   (daily + running cumulative)
Streak counters : consecutive_no_drying_days, consecutive_high_rain_days,
                  consecutive_saturated_days, consecutive_compound_cycles
"""

import numpy as np
import pandas as pd


# ── constants ──────────────────────────────────────────────────────────────────
BASELINE_FLOOD         = 30.0   # EFD units below which no CFL accumulates
SATURATION_THRESHOLD   = 0.80   # soil moisture fraction
HIGH_RAIN_DAILY_CFL    = 60.0   # daily CFL threshold for "high rain day"
SATURATED_DAILY_PSE    = 4.0    # daily PSe threshold for "saturated day"


# ── 3.1  Effective Flood Driver ────────────────────────────────────────────────
def compute_efd(df: pd.DataFrame) -> pd.Series:
    """
    EFD = rainfall_mm + 50.0 * soil_moisture + 0.001 * river_discharge_m3s
    """
    efd = (
        df["rainfall_mm"]
        + 50.0 * df["soil_moisture"]
        + 0.001 * df["river_discharge_m3s"]
    )
    return efd.rename("EFD")


# ── 3.2  Cumulative Flood Load ─────────────────────────────────────────────────
def compute_cfl(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """
    CFL_hour       = max(EFD - 30, 0)
    daily_CFL      = sum of CFL_hour per calendar day
    cumulative_CFL = running sum of daily_CFL
    """
    efd = compute_efd(df_hourly)
    cfl_hour = np.maximum(efd - BASELINE_FLOOD, 0.0)
    cfl_hour.name = "CFL_hour"

    daily_cfl = cfl_hour.resample("D").sum().rename("daily_CFL")
    daily_cfl = daily_cfl.to_frame()
    daily_cfl["cumulative_CFL"] = daily_cfl["daily_CFL"].cumsum()
    return daily_cfl


# ── 3.3  Persistent Saturation Excess ─────────────────────────────────────────
def compute_pse(df_hourly: pd.DataFrame) -> pd.DataFrame:
    """
    PSe_hour       = max(soil_moisture - 0.8, 0)
    daily_PSe      = sum of PSe_hour per calendar day
    cumulative_PSe = running sum of daily_PSe

    Also tracks:
        max_sm_day           : max soil moisture within each calendar day
        no_drying_day        : bool — max SM > saturation_threshold
        consecutive_no_drying_days : running streak counter
    """
    pse_hour = np.maximum(df_hourly["soil_moisture"] - SATURATION_THRESHOLD, 0.0)
    pse_hour.name = "PSe_hour"

    daily = pd.DataFrame()
    daily["daily_PSe"] = pse_hour.resample("D").sum()
    daily["cumulative_PSe"] = daily["daily_PSe"].cumsum()
    daily["max_sm_day"] = df_hourly["soil_moisture"].resample("D").max()
    daily["no_drying_day"] = daily["max_sm_day"] > SATURATION_THRESHOLD
    daily["consecutive_no_drying_days"] = _running_streak(daily["no_drying_day"])
    return daily


# ── 3.4  Compound Strain ───────────────────────────────────────────────────────
def compute_compound(daily_cfl: pd.DataFrame, daily_pse: pd.DataFrame) -> pd.DataFrame:
    """
    high_rain_day              : daily_CFL  > 60
    saturated_day              : daily_PSe  > 4
    compound                   : high_rain_day AND saturated_day

    consecutive_high_rain_days  : running streak
    consecutive_saturated_days  : running streak
    consecutive_compound_cycles : running streak
    """
    comp = pd.DataFrame(index=daily_cfl.index)
    comp["high_rain_day"] = daily_cfl["daily_CFL"] > HIGH_RAIN_DAILY_CFL
    comp["saturated_day"] = daily_pse["daily_PSe"] > SATURATED_DAILY_PSE
    comp["compound"] = comp["high_rain_day"] & comp["saturated_day"]

    comp["consecutive_high_rain_days"] = _running_streak(comp["high_rain_day"])
    comp["consecutive_saturated_days"] = _running_streak(comp["saturated_day"])
    comp["consecutive_compound_cycles"] = _running_streak(comp["compound"])
    return comp


# ── public entry point ─────────────────────────────────────────────────────────
def compute_all_metrics(df_hourly: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Run the full metric pipeline.

    Returns
    -------
    hourly_df : pd.DataFrame
        Original hourly data with EFD and CFL_hour appended.
    daily_df  : pd.DataFrame
        All daily metrics merged into one frame.
    """
    # hourly additions
    df_hourly = df_hourly.copy()
    df_hourly["EFD"] = compute_efd(df_hourly)
    df_hourly["CFL_hour"] = np.maximum(df_hourly["EFD"] - BASELINE_FLOOD, 0.0)
    df_hourly["PSe_hour"] = np.maximum(
        df_hourly["soil_moisture"] - SATURATION_THRESHOLD, 0.0
    )

    # daily metrics
    daily_cfl = compute_cfl(df_hourly)
    daily_pse = compute_pse(df_hourly)
    compound  = compute_compound(daily_cfl, daily_pse)

    daily = (
        daily_cfl
        .join(daily_pse, how="outer")
        .join(compound, how="outer")
    )
    return df_hourly, daily


# ── helper ─────────────────────────────────────────────────────────────────────
def _running_streak(bool_series: pd.Series) -> pd.Series:
    """
    Given a boolean Series, return a Series of the same index with
    the running count of consecutive True values (resets to 0 on False).
    """
    streak = np.zeros(len(bool_series), dtype=int)
    vals = bool_series.values
    for i in range(len(vals)):
        if vals[i]:
            streak[i] = streak[i - 1] + 1 if i > 0 else 1
        else:
            streak[i] = 0
    return pd.Series(streak, index=bool_series.index)
