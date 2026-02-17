"""
risk_states.py
==============
Assigns a daily risk state and computes the nonlinear risk multiplier.

Risk States
-----------
Stable    : CFL < 80   AND PSe < 4  AND compound_streak < 2
Straining : CFL >= 80  OR  PSe >= 4  OR  compound_streak >= 2
Failure   : CFL >= 160 OR  PSe >= 8  OR  compound_streak >= 4

Risk Multiplier
---------------
risk_multiplier = 1 + (CFL / 80) + (PSe / 4) + (compound_streak * 0.5)
"""

import numpy as np
import pandas as pd


# ── thresholds ─────────────────────────────────────────────────────────────────
STABLE_CFL_MAX       = 80.0
STABLE_PSE_MAX       = 4.0
STABLE_STREAK_MAX    = 2      # exclusive upper bound (< 2 → streak 0 or 1)

FAILURE_CFL_MIN      = 160.0
FAILURE_PSE_MIN      = 8.0
FAILURE_STREAK_MIN   = 4

# ── labels ─────────────────────────────────────────────────────────────────────
STATE_STABLE    = "Stable"
STATE_STRAINING = "Straining"
STATE_FAILURE   = "Failure"

# Colour mapping for visualisations
STATE_COLORS = {
    STATE_STABLE:    "#2ecc71",   # green
    STATE_STRAINING: "#f39c12",   # amber
    STATE_FAILURE:   "#e74c3c",   # red
}


def assign_risk_states(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Add `risk_state` and `risk_multiplier` columns to the daily metrics DataFrame.

    Parameters
    ----------
    daily : pd.DataFrame
        Must contain: daily_CFL, daily_PSe, consecutive_compound_cycles

    Returns
    -------
    pd.DataFrame
        Same frame with two new columns appended in-place (copy returned).
    """
    daily = daily.copy()

    cfl     = daily["daily_CFL"].fillna(0.0)
    pse     = daily["daily_PSe"].fillna(0.0)
    streak  = daily["consecutive_compound_cycles"].fillna(0).astype(int)

    # ── risk_state ─────────────────────────────────────────────────────────────
    state = np.full(len(daily), STATE_STABLE, dtype=object)

    straining_mask = (cfl >= STABLE_CFL_MAX) | (pse >= STABLE_PSE_MAX) | (streak >= STABLE_STREAK_MAX)
    failure_mask   = (cfl >= FAILURE_CFL_MIN) | (pse >= FAILURE_PSE_MIN) | (streak >= FAILURE_STREAK_MIN)

    state[straining_mask] = STATE_STRAINING
    state[failure_mask]   = STATE_FAILURE   # failure overwrites straining

    daily["risk_state"] = state

    # ── risk_multiplier ────────────────────────────────────────────────────────
    daily["risk_multiplier"] = (
        1.0
        + (cfl / 80.0)
        + (pse / 4.0)
        + (streak * 0.5)
    )

    return daily


def summary_table(daily: pd.DataFrame) -> pd.DataFrame:
    """
    Return a concise summary DataFrame suitable for printing.
    """
    cols = [
        "daily_CFL",
        "daily_PSe",
        "compound",
        "risk_state",
        "risk_multiplier",
    ]
    present = [c for c in cols if c in daily.columns]
    tbl = daily[present].copy()
    tbl.index.name = "date"
    tbl.index = tbl.index.date   # show date only
    tbl["daily_CFL"]       = tbl["daily_CFL"].round(2)
    tbl["daily_PSe"]       = tbl["daily_PSe"].round(3)
    tbl["risk_multiplier"] = tbl["risk_multiplier"].round(3)
    return tbl
