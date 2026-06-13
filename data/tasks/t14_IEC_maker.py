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
    name="IEA15MW_ref",
    model_path="models/IEA15MW_reference"
)

# ----- create directories for openfast simulation
turbine.IEC_case(
    run_name="IEC_1_3_ref",
    case='1_3'
)