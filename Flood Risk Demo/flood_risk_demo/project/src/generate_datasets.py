"""generate_datasets.py — run once to create the three sample CSVs."""
import numpy as np
import pandas as pd
from pathlib import Path

rng = np.random.default_rng(42)
DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DATA_DIR.mkdir(exist_ok=True)


def _save(df, name):
    p = DATA_DIR / name
    df.to_csv(p, index=False)
    print(f"Saved {p}  ({len(df)} rows)")


# ── helpers ────────────────────────────────────────────────────────────────────
def _hourly_index(start, days):
    return pd.date_range(start, periods=days * 24, freq="h")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 1. Midwest-style flood (30 days, two pulse events)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
days = 30
idx  = _hourly_index("2019-03-10", days)
n    = len(idx)
hour = np.arange(n)

# rainfall: two multi-day events (days 5-9, days 18-24)
rain = rng.exponential(0.5, n)
for d in range(5, 10):
    rain[d*24:(d+1)*24] += rng.gamma(3, 4, 24)
for d in range(18, 25):
    rain[d*24:(d+1)*24] += rng.gamma(4, 5, 24)
rain = np.clip(rain, 0, None)

# soil moisture: rises with rain, slow drying
sm = np.zeros(n)
sm[0] = 0.45
for i in range(1, n):
    sm[i] = sm[i-1] + 0.004 * rain[i] - 0.003 + rng.normal(0, 0.002)
    sm[i] = np.clip(sm[i], 0.05, 0.99)

# discharge: lagged rainfall response
Q = np.zeros(n)
Q[0] = 200
for i in range(1, n):
    Q[i] = 0.92 * Q[i-1] + 1.5 * rain[i] + rng.normal(0, 5)
    Q[i] = max(Q[i], 50)

df1 = pd.DataFrame({
    "timestamp": idx,
    "rainfall_mm": np.round(rain, 3),
    "soil_moisture": np.round(sm, 4),
    "river_discharge_m3s": np.round(Q, 2),
    "groundwater_index": np.round(np.clip(sm * 0.85 + rng.normal(0, 0.02, n), 0, 1), 4),
    "impervious_fraction": np.full(n, 0.22),
})
_save(df1, "sample_midwest_flood.csv")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 2. Europe 2021 Ahr valley style (21 days, catastrophic peak)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
days = 21
idx  = _hourly_index("2021-07-01", days)
n    = len(idx)

rain = rng.exponential(0.3, n)
# extreme 2-day event days 11-12
for d in range(11, 14):
    rain[d*24:(d+1)*24] += rng.gamma(8, 10, 24)
# pre-event wetting days 8-10
for d in range(8, 11):
    rain[d*24:(d+1)*24] += rng.gamma(3, 5, 24)
rain = np.clip(rain, 0, None)

sm = np.zeros(n)
sm[0] = 0.60   # already moist
for i in range(1, n):
    sm[i] = sm[i-1] + 0.005 * rain[i] - 0.002 + rng.normal(0, 0.001)
    sm[i] = np.clip(sm[i], 0.10, 0.99)

Q = np.zeros(n)
Q[0] = 80
for i in range(1, n):
    Q[i] = 0.88 * Q[i-1] + 4.0 * rain[i] + rng.normal(0, 8)
    Q[i] = max(Q[i], 10)

df2 = pd.DataFrame({
    "timestamp": idx,
    "rainfall_mm": np.round(rain, 3),
    "soil_moisture": np.round(sm, 4),
    "river_discharge_m3s": np.round(Q, 2),
    "groundwater_index": np.round(np.clip(sm * 0.9 + rng.normal(0, 0.015, n), 0, 1), 4),
    "impervious_fraction": np.full(n, 0.15),
})
_save(df2, "sample_europe_2021_ahr.csv")


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 3. Future intensified precipitation (45 days, repeated shorter but intense bursts)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
days = 45
idx  = _hourly_index("2055-06-01", days)
n    = len(idx)

rain = rng.exponential(0.4, n)
# five intense short bursts
burst_days = [5, 11, 19, 27, 36]
for bd in burst_days:
    rain[bd*24:(bd+2)*24] += rng.gamma(10, 8, 48)
rain = np.clip(rain, 0, None)

sm = np.zeros(n)
sm[0] = 0.55
for i in range(1, n):
    sm[i] = sm[i-1] + 0.006 * rain[i] - 0.0015 + rng.normal(0, 0.002)
    sm[i] = np.clip(sm[i], 0.15, 0.99)

Q = np.zeros(n)
Q[0] = 120
for i in range(1, n):
    Q[i] = 0.90 * Q[i-1] + 2.5 * rain[i] + rng.normal(0, 6)
    Q[i] = max(Q[i], 30)

df3 = pd.DataFrame({
    "timestamp": idx,
    "rainfall_mm": np.round(rain, 3),
    "soil_moisture": np.round(sm, 4),
    "river_discharge_m3s": np.round(Q, 2),
    "groundwater_index": np.round(np.clip(sm * 0.88 + rng.normal(0, 0.02, n), 0, 1), 4),
    "impervious_fraction": np.full(n, 0.35),  # more urban in future scenario
})
_save(df3, "sample_future_intensified_precip.csv")

print("\nAll three sample datasets generated successfully.")
