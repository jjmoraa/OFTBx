from pathlib import Path
from collections import deque
from io import StringIO
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

cases_dir = Path("runs/inflow_sweep_dfl")
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

    print(f"[POST] {case_dir.name}")

    with open(out_file, "r") as f:

        # Read OpenFAST header
        header_lines = [next(f) for _ in range(8)]

        # Keep only last 20 data rows
        last100 = deque(f, maxlen=20)

    # Rebuild minimal parseable text:
    # variable names + last 100 data rows
    text = header_lines[6] + "".join(last100)

    df = pd.read_csv(
        StringIO(text),
        delim_whitespace=True
    )

    # average last 100 timesteps
    avg_last100 = df.mean().to_dict()

    # store row
    avg_last100["case"] = case_dir.name

    summary_rows.append(avg_last100)

# final table only
summary_df = pd.DataFrame(summary_rows)

# move case column first
summary_df.insert(0, "case", summary_df.pop("case"))

summary_df.to_csv("last100_averages.csv", index=False)

print(summary_df)

wind_speed = summary_df["Wind1VelX"]
oop_dfl    = summary_df["OoPDefl1"]
gen_pwr    = summary_df["GenPwr"]/1000
bld_pitch  = summary_df["BldPitch1"]

# sort by wind speed (important!)
idx = wind_speed.argsort()

wind_speed = wind_speed.iloc[idx]
oop_dfl    = oop_dfl.iloc[idx]
gen_pwr    = gen_pwr.iloc[idx]
bld_pitch  = bld_pitch.iloc[idx]

fig, ax = plt.subplots(figsize=(10, 4))

ax.plot(wind_speed, gen_pwr, marker="o", label="Power")
ax.plot(wind_speed, bld_pitch, marker="o", label="Blade Pitch")
ax.plot(wind_speed, oop_dfl, marker="o", label="OoP Deflection")

ax.set_xlabel("Wind Speed (m/s)")
ax.set_ylabel("Mean value (last 20 timesteps)")
ax.set_title("OpenFAST Sweep Response vs Wind Speed")

ax.legend()
ax.grid(True)

plt.tight_layout()
plt.show()