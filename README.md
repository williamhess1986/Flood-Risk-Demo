# Flood-Risk-DemInland Flood Compound Risk Demo
Understanding Flood Risk Beyond Single Storm Events

This demo app computes daily inland flood‑risk metrics from hourly rainfall, soil moisture, and river discharge data. It captures how antecedent wetness, persistent saturation, and multi‑day rainfall sequences drive real‑world flood risk — not just isolated heavy storms.

Core idea:

Beyond single storms: saturation, recovery windows, and system margins matter more.

Flooding becomes dangerous when soils stay saturated, rivers remain elevated, and drainage systems lose recovery windows. This demo quantifies those compounding dynamics using a transparent, reproducible metric framework.

📁 Project Structure
Code
/project
  /src
    data_loader.py
    metrics.py
    risk_states.py
    visualization.py
    main.py
  /data
    sample_midwest_flood.csv
    sample_europe_2021_ahr.csv
    sample_future_intensified_precip.csv
  /notebooks
    demo.ipynb
  README.md
  requirements.txt
  LICENSE
1. 🌧️ Conceptual Overview
Inland flooding is driven by three interacting forces:

Rainfall intensity and duration

Antecedent soil moisture and groundwater levels

River baseflow and drainage capacity

Flood risk accelerates when:

soils cannot absorb new rainfall

rivers remain elevated between storms

nighttime drying windows disappear

storms arrive in multi‑day clusters

This app quantifies:

Effective Flood Driver (EFD)

Cumulative Flood Load (CFL)

Persistent Saturation Excess (PSe)

Compound day–night saturation cycles

Streaks of high‑risk days

Nonlinear escalation

The result is a daily risk state that reflects system strain, not just rainfall totals.

2. 📐 Key Metrics
The app computes four core metrics from hourly data.

2.1 Effective Flood Driver (EFD)
A combined proxy for rainfall, soil saturation, and river discharge:

Code
EFD = rainfall_mm + 50.0 * soil_moisture + 0.001 * river_discharge_m3s
Rainfall drives immediate runoff

Soil moisture amplifies runoff

River discharge reflects basin‑scale stress

2.2 Cumulative Flood Load (CFL)
Daily flood‑forcing above infiltration capacity.

Code
baseline_flood = 30.0
CFL_hour = max(EFD - baseline_flood, 0)
daily_CFL = sum(CFL_hour)
cumulative_CFL = running sum
This captures how much of the day exceeds infiltration and drainage thresholds.

2.3 Persistent Saturation Excess (PSe)
Measures whether soils remain saturated and unable to recover.

Code
saturation_threshold = 0.8
PSe_hour = max(soil_moisture - saturation_threshold, 0)
daily_PSe = sum(PSe_hour)
cumulative_PSe = running sum
Track days without drying:

Code
no_drying_day = (max(soil_moisture over 00:00–23:59) > saturation_threshold)
consecutive_no_drying_days = running streak
High PSe indicates no recovery window, a major driver of real‑world flood escalation.

2.4 Compound Day–Night Strain
Code
high_rain_day = (daily_CFL > 60.0)
saturated_day = (daily_PSe > 4.0)
compound = high_rain_day and saturated_day
Track streaks:

consecutive_high_rain_days

consecutive_saturated_days

consecutive_compound_cycles

Compound cycles indicate multi‑day hydrologic overload.

3. 🚦 Daily Risk States
Risk states are assigned using daily metrics:

Code
Stable:
  CFL < 80.0 and PSe < 4.0 and compound_streak < 2

Straining:
  CFL >= 80.0 or PSe >= 4.0 or compound_streak >= 2

Failure:
  CFL >= 160.0 or PSe >= 8.0 or compound_streak >= 4
Stable → soils absorb water; rivers remain manageable

Straining → soils saturated; rivers elevated; drainage stressed

Failure → multi‑day overload; flash‑flood and river‑flood potential high

4. 📊 Visualization Suite
The app generates five panels:

Panel 1 — Timeline
rainfall_mm

soil_moisture

river_discharge_m3s

EFD overlay

Panel 2 — CFL Curve
cumulative_CFL

Panel 3 — PSe Bars
daily_PSe

Panel 4 — Risk State Band
green = Stable

amber = Straining

red = Failure

Panel 5 — Nonlinear Escalation Gauge
Code
risk_multiplier = 1 + (CFL / 80.0) + (PSe / 4.0) + (compound_streak * 0.5)
This reflects how antecedent wetness + repeated storms + failed drying create nonlinear increases in flood potential.

5. ▶️ Running the App
1. Install dependencies
Code
pip install -r requirements.txt
2. Run the main script
Code
python src/main.py
3. View outputs
/project/output/metrics_daily.csv

/project/output/risk_states.csv

/project/output/figures/*.png

6. 📥 Using Your Own CSV
Your CSV must include:

Code
timestamp
rainfall_mm
soil_moisture
river_discharge_m3s
Optional:

Code
groundwater_index
impervious_fraction
Place your file in /project/data/ and update the filename in main.py.

7. 📄 License
MIT License — free to use, modify, and distribute.o
