from pathlib import Path
from collections import deque
from io import StringIO

import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
# USER INPUT
# =============================================================================

cases_dirs = [
    Path("runs/inflow_sweep_dfl"),
    Path("runs/inflow_sweep_mom"),
    Path("runs/inflow_sweep_ref"),
]

# =============================================================================
# DATA GENERATION
# =============================================================================

all_results = {}

for cases_dir in cases_dirs:

    print(f"\nProcessing {cases_dir}")

    case_dirs = sorted([
        d for d in cases_dir.iterdir()
        if d.is_dir() and (d / "case.fst").exists()
    ])

    summary_rows = []

    for case_dir in case_dirs:

        out_file = case_dir / "case.out"

        if not out_file.exists():
            print(f"[WARNING] Missing {out_file}")
            continue

        with open(out_file, "r") as f:

            header_lines = [next(f) for _ in range(8)]
            last20 = deque(f, maxlen=20)

        text = header_lines[6] + "".join(last20)

        df = pd.read_csv(
            StringIO(text),
            sep=r"\s+"
        )

        avg = df.mean().to_dict()
        avg["case"] = case_dir.name

        summary_rows.append(avg)

    summary_df = pd.DataFrame(summary_rows)

    if summary_df.empty:
        continue

    summary_df.insert(0, "case", summary_df.pop("case"))

    csv_file = f"{cases_dir.name}_last20_averages.csv"
    summary_df.to_csv(csv_file, index=False)

    print(f"Saved {csv_file}")

    all_results[cases_dir.name] = summary_df

# =============================================================================
# PLOTTING
# =============================================================================

fig, axes = plt.subplots(
    3,
    1,
    figsize=(10, 10),
    sharex=True
)

for label, summary_df in all_results.items():

    wind_speed = summary_df["Wind1VelX"]
    gen_pwr    = summary_df["GenPwr"] / 1000
    bld_pitch  = summary_df["BldPitch1"]
    oop_dfl    = summary_df["OoPDefl1"]

    idx = wind_speed.argsort()

    wind_speed = wind_speed.iloc[idx]
    gen_pwr    = gen_pwr.iloc[idx]
    bld_pitch  = bld_pitch.iloc[idx]
    oop_dfl    = oop_dfl.iloc[idx]

    axes[0].plot(
        wind_speed,
        gen_pwr,
        marker="o",
        label=label
    )

    axes[1].plot(
        wind_speed,
        bld_pitch,
        marker="o",
        label=label
    )

    axes[2].plot(
        wind_speed,
        oop_dfl,
        marker="o",
        label=label
    )

# -------------------------------------------------------------------------
# Formatting
# -------------------------------------------------------------------------

# axes[0].set_title("Generator Power")
axes[0].set_ylabel("Power (kW)")

# axes[1].set_title("Blade Pitch")
axes[1].set_ylabel("Pitch (deg)")

# axes[2].set_title("Out-of-Plane Deflection")
axes[2].set_ylabel("OoP Deflection")
axes[2].set_xlabel("Wind Speed (m/s)")

for ax in axes:
    ax.grid(True)
    ax.legend()

plt.tight_layout()
plt.show()