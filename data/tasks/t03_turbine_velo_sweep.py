from OFTBx.builder import build_model_from_fst
from OFTBx.turbine import Turbine

# ------------------------------------------------------------
# 1. Build model (only once per turbine)
# ------------------------------------------------------------
# model_dir = build_model_from_fst(
#     fst_path="data/IEA-15-240-RWT/OpenFAST/IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile.fst",
#     model_name="IEA15MW"
# )

# ------------------------------------------------------------
# 2. Load turbine object
# ------------------------------------------------------------
turbine = Turbine(
    name="IEA15MW",
    model_path="models/IEA15MW"
)

# ----- create directories for openfast simulation
turbine.inflow_sweep(
    run_name="inflow_sweep",
    U_min=4,
    U_max=25,
    n=10
)