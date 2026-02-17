"""
visualization.py
================
Generates all five analysis panels and saves them as a single multi-panel PNG.

Panel 1 — Timeline  : rainfall_mm, soil_moisture, river_discharge_m3s, EFD overlay
Panel 2 — CFL curve : cumulative_CFL
Panel 3 — PSe bars  : daily_PSe
Panel 4 — Risk band : colour-coded risk state per day
Panel 5 — Gauge     : nonlinear risk_multiplier over time
"""

from __future__ import annotations

from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.patches as mpatches
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from risk_states import STATE_COLORS, STATE_FAILURE, STATE_STABLE, STATE_STRAINING


# ── palette ────────────────────────────────────────────────────────────────────
_C = {
    "rain":        "#1f77b4",
    "sm":          "#8B4513",
    "discharge":   "#17becf",
    "efd":         "#d62728",
    "cfl":         "#ff7f0e",
    "pse":         "#9467bd",
    "multiplier":  "#2ca02c",
}


def _date_fmt(ax: plt.Axes, freq: str = "W") -> None:
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%b %d"))
    ax.xaxis.set_major_locator(mdates.WeekdayLocator(byweekday=mdates.MO, interval=1))
    ax.tick_params(axis="x", rotation=30, labelsize=7)


def plot_all_panels(
    hourly: pd.DataFrame,
    daily: pd.DataFrame,
    title_prefix: str = "",
    output_dir: str | Path = "output",
    filename: str = "flood_risk_analysis.png",
) -> Path:
    """
    Create the five-panel figure and save to `output_dir/filename`.

    Parameters
    ----------
    hourly : pd.DataFrame   hourly data with EFD column
    daily  : pd.DataFrame   daily metrics incl. risk_state, risk_multiplier
    title_prefix : str      prepended to figure suptitle
    output_dir   : path     directory to save PNG
    filename     : str      output filename

    Returns
    -------
    Path to saved figure.
    """
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    out_path = output_dir / filename

    fig, axes = plt.subplots(
        5, 1,
        figsize=(14, 20),
        sharex=False,
        gridspec_kw={"hspace": 0.55},
    )

    suptitle = f"{title_prefix} — Inland / Pluvial + Riverine Flood Risk Analysis"
    fig.suptitle(suptitle.strip(), fontsize=13, fontweight="bold", y=0.99)

    daily_dates = daily.index.to_pydatetime()

    # ── Panel 1 : Timeline ─────────────────────────────────────────────────────
    ax1 = axes[0]
    ax1_r1 = ax1.twinx()
    ax1_r2 = ax1.twinx()
    ax1_r2.spines["right"].set_position(("axes", 1.10))

    ax1.bar(hourly.index, hourly["rainfall_mm"], color=_C["rain"],
            alpha=0.55, width=1 / 24, label="Rainfall (mm/hr)")
    ax1_r1.plot(hourly.index, hourly["soil_moisture"], color=_C["sm"],
                lw=1.4, label="Soil Moisture")
    ax1_r2.plot(hourly.index, hourly["river_discharge_m3s"], color=_C["discharge"],
                lw=1.2, alpha=0.8, label="Discharge (m³/s)")
    ax1.plot(hourly.index, hourly["EFD"], color=_C["efd"],
             lw=1.0, alpha=0.7, label="EFD")

    ax1.set_ylabel("Rainfall mm / EFD", fontsize=8)
    ax1_r1.set_ylabel("Soil Moisture (0–1)", fontsize=8)
    ax1_r2.set_ylabel("Discharge m³/s", fontsize=8)
    ax1.set_title("Panel 1 — Hourly Inputs & EFD", fontsize=9, fontweight="bold")

    handles = [
        mpatches.Patch(color=_C["rain"],      label="Rainfall mm/hr"),
        mpatches.Patch(color=_C["sm"],        label="Soil Moisture"),
        mpatches.Patch(color=_C["discharge"], label="Discharge m³/s"),
        mpatches.Patch(color=_C["efd"],       label="EFD"),
    ]
    ax1.legend(handles=handles, loc="upper left", fontsize=7, ncol=2)
    _date_fmt(ax1)

    # ── Panel 2 : Cumulative CFL ───────────────────────────────────────────────
    ax2 = axes[1]
    ax2.plot(daily_dates, daily["cumulative_CFL"], color=_C["cfl"],
             lw=2, marker="o", markersize=3)
    ax2.fill_between(daily_dates, daily["cumulative_CFL"], alpha=0.15, color=_C["cfl"])
    ax2.set_ylabel("Cumulative CFL", fontsize=8)
    ax2.set_title("Panel 2 — Cumulative Flood Load (CFL)", fontsize=9, fontweight="bold")
    ax2.grid(True, alpha=0.3)
    _date_fmt(ax2)

    # ── Panel 3 : Daily PSe bars ───────────────────────────────────────────────
    ax3 = axes[2]
    bar_width = max(0.6, 0.8 * (daily_dates[1] - daily_dates[0]).days) if len(daily_dates) > 1 else 0.8
    ax3.bar(daily_dates, daily["daily_PSe"], color=_C["pse"], alpha=0.75, width=bar_width)
    ax3.axhline(4.0, color="red", lw=1, ls="--", label="Saturated threshold (4.0)")
    ax3.set_ylabel("Daily PSe", fontsize=8)
    ax3.set_title("Panel 3 — Daily Persistent Saturation Excess (PSe)", fontsize=9, fontweight="bold")
    ax3.legend(fontsize=7)
    ax3.grid(True, alpha=0.3, axis="y")
    _date_fmt(ax3)

    # ── Panel 4 : Risk state band ──────────────────────────────────────────────
    ax4 = axes[3]
    risk_num = daily["risk_state"].map(
        {STATE_STABLE: 0, STATE_STRAINING: 1, STATE_FAILURE: 2}
    ).fillna(0)

    for i, (dt, rs) in enumerate(zip(daily_dates, daily["risk_state"])):
        color = STATE_COLORS.get(rs, "#2ecc71")
        w = bar_width if 'bar_width' in dir() else 0.8
        ax4.bar(dt, 1, color=color, alpha=0.85, width=w)

    ax4.set_yticks([])
    ax4.set_ylim(0, 1.2)
    ax4.set_title("Panel 4 — Daily Risk State", fontsize=9, fontweight="bold")
    legend_handles = [
        mpatches.Patch(color=STATE_COLORS[STATE_STABLE],    label=STATE_STABLE),
        mpatches.Patch(color=STATE_COLORS[STATE_STRAINING], label=STATE_STRAINING),
        mpatches.Patch(color=STATE_COLORS[STATE_FAILURE],   label=STATE_FAILURE),
    ]
    ax4.legend(handles=legend_handles, loc="upper right", fontsize=7)
    _date_fmt(ax4)

    # ── Panel 5 : Nonlinear risk multiplier ───────────────────────────────────
    ax5 = axes[4]
    ax5.plot(daily_dates, daily["risk_multiplier"], color=_C["multiplier"],
             lw=2, marker="s", markersize=3)
    ax5.fill_between(daily_dates, 1, daily["risk_multiplier"],
                     alpha=0.15, color=_C["multiplier"])
    ax5.axhline(1.0, color="grey", lw=1, ls="--", label="Baseline (1.0)")
    ax5.set_ylabel("Risk Multiplier", fontsize=8)
    ax5.set_title(
        "Panel 5 — Nonlinear Escalation Gauge  "
        r"[$1 + \frac{CFL}{80} + \frac{PSe}{4} + streak \times 0.5$]",
        fontsize=9, fontweight="bold",
    )
    ax5.legend(fontsize=7)
    ax5.grid(True, alpha=0.3)
    _date_fmt(ax5)

    fig.savefig(out_path, dpi=150, bbox_inches="tight")
    plt.close(fig)
    print(f"  [visualization] Saved figure → {out_path}")
    return out_path
