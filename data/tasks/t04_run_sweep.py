from pathlib import Path
from OFTBx.turbine import Turbine

turbine = Turbine(
    name="IEA15MW",
    model_path="models/IEA15MW"
)

cases_dir = Path("runs/inflow_sweep")
case_dirs = sorted([d for d in cases_dir.iterdir() if d.is_dir() and (d / "case.fst").exists()])

# preallocate results (same size as cases)
results = [None] * len(case_dirs)

for i, case_dir in enumerate(case_dirs):

    print(f"[RUN] {case_dir.name}")

    results[i] = turbine.run_case(
        case_dir,
        exe="openfast"   # or full path if needed
    )

print(f'DONE')