from pathlib import Path
from concurrent.futures import ProcessPoolExecutor, as_completed
from OFTBx.turbine import Turbine

cases_dir = Path("runs/inflow_sweep_mom")
case_dirs = sorted([
    d for d in cases_dir.iterdir()
    if d.is_dir() and (d / "case.fst").exists()
])

def run_case(case_dir):

    turbine = Turbine(
        name="IEA15MW_MOM",
        model_path="models/IEA15MW_MOM"
    )

    print(f"[RUN] {case_dir.name}")

    return turbine.run_case(
        case_dir,
        exe="openfast"
    )

if __name__ == "__main__":

    results = [None] * len(case_dirs)

    with ProcessPoolExecutor(max_workers=4) as executor:

        future_to_idx = {
            executor.submit(run_case, case_dir): i
            for i, case_dir in enumerate(case_dirs)
        }

        for future in as_completed(future_to_idx):

            i = future_to_idx[future]

            try:
                results[i] = future.result()
                print(f"[DONE] {case_dirs[i].name}")

            except Exception as e:
                print(f"[FAILED] {case_dirs[i].name}: {e}")

    print("DONE")