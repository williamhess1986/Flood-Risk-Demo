# Inland / Pluvial + Riverine Flood Risk Demo

> **"Beyond single storms: saturation, recovery windows, and system margins matter more."**

Most flood-risk frameworks ask: *how much rain fell?* This project asks a harder question:
*how much strain has the system accumulated, and how much margin remains before it fails?*

A single intense storm on dry ground may cause localised flash flooding but remain manageable.
The same storm arriving after a week of near-saturated soils, with rivers already running
elevated, triggers a fundamentally different outcome — one that standard rainfall thresholds
consistently miss. This tool captures that difference through compound metrics that account for
antecedent wetness, cumulative load, and the absence of recovery windows between events.

---

## Table of Contents

1. [Project Structure](#project-structure)  
2. [Metric Definitions](#metric-definitions)  
3. [Risk States](#risk-states)  
4. [Nonlinear Escalation](#nonlinear-escalation)  
5. [Quick Start](#quick-start)  
6. [Using Your Own Data](#using-your-own-data)  
7. [Sample Datasets](#sample-datasets)  
8. [Output Files](#output-files)  
9. [Requirements](#requirements)  
10. [License](#license)  

---

## Project Structure

```
/project
  /src
    data_loader.py          # CSV ingestion & validation
    metrics.py              # EFD, CFL, PSe, streak counters
    risk_states.py          # threshold logic, risk multiplier
    visualization.py        # 5-panel matplotlib figures
    main.py                 # entry point
    generate_datasets.py    # script to regenerate synthetic CSVs
  /data
    sample_midwest_flood.csv
    sample_europe_2021_ahr.csv
    sample_future_intensified_precip.csv
  /notebooks
    demo.ipynb              # interactive walkthrough
  /output                   # auto-created; figures + summary CSVs written here
  README.md
  requirements.txt
  LICENSE
```

---

## Metric Definitions

### Effective Flood Driver (EFD) — *hourly*

```
EFD = rainfall_mm + 50.0 × soil_moisture + 0.001 × river_discharge_m3s
```

EFD combines the three primary flood drivers into a single hourly index.
The soil-moisture coefficient (50) is large by design: a fully saturated catchment
contributes as much to flood risk as 50 mm of additional rainfall, even with no rain
falling — because infiltration capacity is near zero and any additional rain becomes
near-total runoff.

---

### Cumulative Flood Load (CFL) — *daily + running cumulative*

```
CFL_hour       = max(EFD − 30, 0)
daily_CFL      = Σ CFL_hour  (per calendar day)
cumulative_CFL = running sum of daily_CFL
```

The baseline (30) represents the normal EFD level a healthy catchment can absorb.
Daily CFL measures how much excess driver energy accumulated in a given day.
Cumulative CFL tracks how much total load has built up over the event window —
a rising cumulative curve that does not flatten signals a system with no recovery.

---

### Persistent Saturation Excess (PSe) — *daily + running cumulative*

```
PSe_hour       = max(soil_moisture − 0.8, 0)
daily_PSe      = Σ PSe_hour  (per calendar day)
cumulative_PSe = running sum of daily_PSe
```

PSe measures the degree and duration of soil over-saturation. A day with PSe = 4
means the soil spent the entire 24 hours at full saturation — no infiltration buffer
exists. Days without recovery (`no_drying_day`: max SM > 0.8 throughout) are tracked
as a consecutive counter; long streaks signal structural catchment stress.

---

### Compound Strain

```
high_rain_day   = (daily_CFL  > 60)
saturated_day   = (daily_PSe  > 4)
compound        = high_rain_day AND saturated_day

consecutive_high_rain_days  : running streak of high_rain_day
consecutive_saturated_days  : running streak of saturated_day
consecutive_compound_cycles : running streak of compound days
```

A compound day is one where both intense rainfall loading *and* soil saturation
co-occur. Single compound days are manageable; consecutive compound cycles indicate
the system has lost its ability to absorb further stress between events.

---

## Risk States

| State       | Condition                                                            | Colour |
|-------------|----------------------------------------------------------------------|--------|
| **Stable**     | CFL < 80 **and** PSe < 4 **and** compound_streak < 2            | 🟢 Green |
| **Straining**  | CFL ≥ 80 **or** PSe ≥ 4 **or** compound_streak ≥ 2              | 🟡 Amber |
| **Failure**    | CFL ≥ 160 **or** PSe ≥ 8 **or** compound_streak ≥ 4             | 🔴 Red   |

The OR logic for Straining and Failure means any single dimension crossing its
threshold is sufficient to elevate risk. Failure is not a dramatic cliff edge in
one dimension — it is a convergence of sustained stress across multiple pathways.

---

## Nonlinear Escalation

```
risk_multiplier = 1 + (CFL / 80) + (PSe / 4) + (compound_streak × 0.5)
```

The risk multiplier is the key insight of this framework. A multiplier of 1.0 means
baseline risk. A multiplier of 5.0 means five times the expected flood impact for a
given storm of the same magnitude.

**Why nonlinear?**  
When CFL doubles, PSe doubles, *and* a compound streak is active, the multiplier
does not merely add — it stacks multiplicatively in effect, because:

- Saturated soils produce nearly 100% runoff regardless of rainfall intensity.  
- Elevated river discharge leaves zero headroom for tributary contributions.  
- Emergency infrastructure (pumps, barriers, emergency services) faces simultaneous
  demands from multiple sites.  

The 2021 Ahr Valley flood is a textbook example: the extreme rainfall of 14–15 July
struck a catchment already saturated by preceding weeks of above-normal precipitation.
The resulting disaster was not solely caused by peak rainfall intensity — it was the
*antecedent wetness* that transformed an unusual storm into a catastrophe.

---

## Quick Start

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Run all three sample datasets

```bash
python src/main.py
```

Figures and summary tables are written to `/output/`.

### 3. Run a single named dataset

```bash
python src/main.py --dataset midwest
python src/main.py --dataset ahr
python src/main.py --dataset future
```

### 4. Regenerate the synthetic CSVs

```bash
python src/generate_datasets.py
```

---

## Using Your Own Data

Prepare a CSV with the following columns:

| Column | Type | Notes |
|--------|------|-------|
| `timestamp` | ISO 8601 string | Hourly resolution recommended |
| `rainfall_mm` | float ≥ 0 | mm per hour |
| `soil_moisture` | float 0–1 | Volumetric or fractional moisture |
| `river_discharge_m3s` | float ≥ 0 | m³/s at nearest gauge |
| `groundwater_index` *(optional)* | float 0–1 | — |
| `impervious_fraction` *(optional)* | float 0–1 | Land-cover fraction |

Then run:

```bash
python src/main.py --csv path/to/your_data.csv
```

Output figures and summary CSV will be saved to `/output/`.

**Tips for real data:**  
- Missing values are forward-filled; flag gaps in source data before loading.  
- Daily timestep data will work but streak metrics lose sub-daily resolution.  
- For multi-site data, run `main.py` once per gauge/catchment.

---

## Sample Datasets

| File | Scenario | Duration | Key Feature |
|------|----------|----------|-------------|
| `sample_midwest_flood.csv` | US Midwest spring flood 2019-style | 30 days | Two sequential pulse events; full soil saturation on second event |
| `sample_europe_2021_ahr.csv` | Ahr Valley Germany 2021-style | 21 days | Pre-event wetting followed by catastrophic 3-day extreme rainfall |
| `sample_future_intensified_precip.csv` | 2055 climate-intensified scenario | 45 days | Five short intense bursts with no recovery window; multiplier escalation to 50+ |

All datasets are synthetically generated with physically plausible dynamics.

---

## Output Files

Each dataset run produces:

- `<dataset>_flood_risk.png` — 5-panel analysis figure
- `<dataset>_summary.csv` — daily table: CFL, PSe, compound flag, risk_state, risk_multiplier

---

## Requirements

```
pandas
numpy
matplotlib
plotly
```

Install with: `pip install -r requirements.txt`

---

## License

MIT — see `LICENSE`.
