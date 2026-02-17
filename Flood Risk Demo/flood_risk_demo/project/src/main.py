"""
main.py
=======
Entry point for the Inland / Pluvial + Riverine Flood Risk Demo.

Usage
-----
    python src/main.py                         # runs all three sample datasets
    python src/main.py --csv path/to/file.csv  # run a single custom CSV
    python src/main.py --dataset midwest        # run a named sample dataset

Outputs
-------
All figures + summary CSVs are written to /project/output/
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# ── path setup so relative imports work when run from anywhere ─────────────────
_SRC = Path(__file__).resolve().parent
_PROJECT = _SRC.parent
sys.path.insert(0, str(_SRC))

from data_loader import load_csv
from metrics import compute_all_metrics
from risk_states import assign_risk_states, summary_table
from visualization import plot_all_panels


# ── sample dataset registry ───────────────────────────────────────────────────
SAMPLE_DATASETS = {
    "midwest":  (_PROJECT / "data" / "sample_midwest_flood.csv",       "Midwest 2019"),
    "ahr":      (_PROJECT / "data" / "sample_europe_2021_ahr.csv",     "Europe 2021 Ahr"),
    "future":   (_PROJECT / "data" / "sample_future_intensified_precip.csv", "Future Intensified"),
}

OUTPUT_DIR = _PROJECT / "output"


def run_dataset(csv_path: Path, label: str) -> None:
    print(f"\n{'='*60}")
    print(f"  Dataset : {label}")
    print(f"  File    : {csv_path.name}")
    print(f"{'='*60}")

    # 1. Load
    hourly = load_csv(csv_path)

    # 2. Compute metrics
    hourly, daily = compute_all_metrics(hourly)

    # 3. Assign risk states
    daily = assign_risk_states(daily)

    # 4. Visualise
    safe_label = label.replace(" ", "_").replace("/", "-")
    plot_all_panels(
        hourly=hourly,
        daily=daily,
        title_prefix=label,
        output_dir=OUTPUT_DIR,
        filename=f"{safe_label}_flood_risk.png",
    )

    # 5. Save summary CSV
    tbl = summary_table(daily)
    csv_out = OUTPUT_DIR / f"{safe_label}_summary.csv"
    tbl.to_csv(csv_out)
    print(f"  [main] Summary CSV → {csv_out}")

    # 6. Print summary table
    print(f"\n  Summary — {label}")
    print(tbl.to_string())
    print()


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Inland Flood Compound Risk Demo"
    )
    parser.add_argument(
        "--csv", type=str, default=None,
        help="Path to a custom CSV file (must conform to the required schema).",
    )
    parser.add_argument(
        "--dataset", type=str, default=None,
        choices=list(SAMPLE_DATASETS.keys()),
        help="Run a single named sample dataset.",
    )
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.csv:
        csv_path = Path(args.csv)
        run_dataset(csv_path, label=csv_path.stem)
    elif args.dataset:
        csv_path, label = SAMPLE_DATASETS[args.dataset]
        run_dataset(csv_path, label)
    else:
        # Run all sample datasets
        for key, (csv_path, label) in SAMPLE_DATASETS.items():
            run_dataset(csv_path, label)

    print(f"\nAll outputs saved to: {OUTPUT_DIR}")


if __name__ == "__main__":
    main()
