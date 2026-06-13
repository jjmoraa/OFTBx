from pathlib import Path
from collections import deque
from io import StringIO
import re

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# =============================================================================
# USER INPUT
# =============================================================================

cases_dirs = [
    Path("runs/IEC_1_3_dfl"),
    Path("runs/IEC_1_3_mom"),
    Path("runs/IEC_1_3_ref"),
]

boxplot_channels = [
    "GenPwr",
    "BldPitch1",
    "OoPDefl1",
    "RootMxb1",
    "RootMyb1",
    "RotThrust",
    "TwrBsMyt"
]

# =============================================================================
# HELPERS
# =============================================================================

def get_wind_speed(name):
    """
    Extract wind speed from folder name.
    Adjust regex if your naming is different.
    """
    match = re.search(r'(\d+)', name)
    if match:
        return float(match.group(1))
    raise ValueError(f"Cannot parse wind speed from {name}")

# =============================================================================
# DATA STORAGE
# =============================================================================

all_statistics = {}
boxplot_data = {}  # (turbine, ws, channel)

# =============================================================================
# DATA GENERATION
# =============================================================================

for cases_dir in cases_dirs:

    print(f"\nProcessing {cases_dir}")

    case_dirs = sorted([
        d for d in cases_dir.iterdir()
        if d.is_dir() and (d / "case.out").exists()
    ])

    summary_rows = []

    for case_dir in case_dirs:

        out_file = case_dir / "case.out"

        if not out_file.exists():
            print(f"[WARNING] Missing {out_file}")
            continue

        ws = get_wind_speed(case_dir.name)
        turbine = cases_dir.name

        with open(out_file, "r") as f:
            header_lines = [next(f) for _ in range(8)]
            last20 = deque(f, maxlen=20)

        text = header_lines[6] + "".join(last20)

        df = pd.read_csv(StringIO(text), sep=r"\s+")

        # -------------------------
        # statistics
        # -------------------------
        row = {
            "case": case_dir.name,
            "wind_speed": ws
        }

        for col in df.columns:

            values = df[col].dropna()

            row[f"{col}_mean"]   = values.mean()
            row[f"{col}_std"]    = values.std()
            row[f"{col}_median"] = values.median()
            row[f"{col}_min"]    = values.min()
            row[f"{col}_max"]    = values.max()
            row[f"{col}_p05"]    = np.percentile(values, 5)
            row[f"{col}_p95"]    = np.percentile(values, 95)
            row[f"{col}_absmax"] = np.abs(values).max()
            row[f"{col}_rms"]    = np.sqrt(np.mean(values**2))

        summary_rows.append(row)

        # -------------------------
        # boxplot storage
        # -------------------------
        for channel in boxplot_channels:

            if channel not in df.columns:
                continue

            key = (turbine, ws, channel)

            if key not in boxplot_data:
                boxplot_data[key] = []

            boxplot_data[key].extend(df[channel].dropna().tolist())

    summary_df = pd.DataFrame(summary_rows)

    csv_file = f"{cases_dir.name}_statistics.csv"
    summary_df.to_csv(csv_file, index=False)

    print(f"Saved {csv_file}")

    all_statistics[cases_dir.name] = summary_df

# =============================================================================
# PLOTTING (2x2 GRID PER CHANNEL)
# =============================================================================

wind_speeds = sorted({ws for (_, ws, _) in boxplot_data.keys()})

for channel in boxplot_channels:

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharey=True)
    axes = axes.flatten()

    for i, ws in enumerate(wind_speeds):

        ax = axes[i]

        data = []
        labels = []

        for turbine in all_statistics.keys():

            key = (turbine, ws, channel)

            if key not in boxplot_data:
                continue

            if len(boxplot_data[key]) == 0:
                continue

            data.append(boxplot_data[key])
            labels.append(turbine)

        if len(data) == 0:
            ax.set_title(f"{ws} m/s (no data)")
            ax.axis("off")
            continue

        ax.boxplot(data, tick_labels=labels, showfliers=True)
        ax.set_title(f"{ws} m/s")
        ax.grid(True)

    # turn off unused axes
    for j in range(len(wind_speeds), 4):
        axes[j].axis("off")

    fig.suptitle(channel)
    plt.tight_layout()
    plt.show()