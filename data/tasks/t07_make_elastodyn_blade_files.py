import numpy as np
from scipy.io import loadmat

filename = "./models/IEA15MW_DFL/dfl_blade_design20260605_090747.mat"

# -------------------------------------------------
# 1. Load MAT file
# -------------------------------------------------
data = loadmat(filename, squeeze_me=True, struct_as_record=False)

blade = data["S"].fastBlade

import numpy as np

S = data["S"]

# -----------------------------
# 1. Geometry / interpolation
# -----------------------------
r = np.array(S.ispan).squeeze()
chord = np.array(S.ichord).squeeze()
twist = np.array(S.idegreestwist).squeeze()

# -----------------------------
# 2. Secprops (correct parsing)
# -----------------------------
labels = [str(x) for x in S.secprops.labels]
sec_data = np.array(S.secprops.data)

sec = {labels[i]: sec_data[:, i] for i in range(len(labels))}


# -----------------------------
# 3. Output file
# -----------------------------
out = "blade_elastodyn.dat"

blade = S.fastBlade

with open(out, "w") as f:

    # -------------------------
    # HEADER
    # -------------------------
    f.write("------- ELASTODYN V1.00.* INDIVIDUAL BLADE INPUT FILE --------------------------\n")
    f.write(f"Generated from MATLAB blade design file {filename}\n")

    # -------------------------
    # BLADE PARAMETERS
    # -------------------------
    bld_fl_dmp = np.asarray(blade.BldFlDmp).squeeze()
    bld_ed_dmp = np.asarray(blade.BldEdDmp).squeeze()

    fl_dmp1 = float(bld_fl_dmp[0])
    fl_dmp2 = float(bld_fl_dmp[1])
    ed_dmp1 = float(np.atleast_1d(bld_ed_dmp)[0])

    f.write("---------------------- BLADE PARAMETERS ----------------------------------------\n")
    f.write(f"{len(r):<22d} NBlInpSt    - Number of blade input stations (-)\n")
    f.write(f"{fl_dmp1:<22.6f} BldFlDmp1   - Blade flap mode #1 structural damping (% critical)\n")
    f.write(f"{fl_dmp2:<22.6f} BldFlDmp2   - Blade flap mode #2 structural damping (% critical)\n")
    f.write(f"{ed_dmp1:<22.6f} BldEdDmp1   - Blade edge mode #1 structural damping (% critical)\n")

    # -------------------------
    # TUNING FACTORS
    # -------------------------
    flst = np.asarray(blade.FlStTunr).squeeze()

    f.write("---------------------- BLADE ADJUSTMENT FACTORS --------------------------------\n")
    f.write(f"{float(flst[0]):<22.6f} FlStTunr1\n")
    f.write(f"{float(flst[1]):<22.6f} FlStTunr2\n")
    f.write(f"{float(blade.AdjBlMs):<22.6f} AdjBlMs\n")
    f.write(f"{float(blade.AdjFlSt):<22.6f} AdjFlSt\n")
    f.write(f"{float(blade.AdjEdSt):<22.6f} AdjEdSt\n")

    # -------------------------
    # DISTRIBUTED PROPERTIES
    # -------------------------
    f.write("---------------------- DISTRIBUTED BLADE PROPERTIES ----------------------------\n")
    f.write("    BlFract      PitchAxis      StrcTwst       BMassDen        FlpStff        EdgStff\n")
    f.write("      (-)           (-)          (deg)          (kg/m)         (Nm^2)         (Nm^2)\n")

    r_norm = (r - r.min()) / (r.max() - r.min())

    for i in range(len(r)):
        f.write(
            f"{r_norm[i]: .15e}  "
            f"{0.5: .15e}  "  # TODO: replace with actual pitch axis if available
            f"{twist[i]: .15e}  "
            f"{sec['mass'][i]: .15e}  "
            f"{sec['ei_flap'][i]: .15e}  "
            f"{sec['ei_lag'][i]: .15e}\n"
        )

    # -------------------------
    # BLADE MODE SHAPES
    # -------------------------
    f.write("---------------------- BLADE MODE SHAPES ---------------------------------------\n")

    fl1 = np.asarray(blade.BldFl1Sh).squeeze()[1:]
    fl2 = np.asarray(blade.BldFl2Sh).squeeze()[1:]
    edg = np.asarray(blade.BldEdgSh).squeeze()[1:]

    # Flap mode 1
    for i, val in enumerate(fl1, start=2):
        if i == 2:
            desc = f"BldFl1Sh({i}) - Flap mode 1, coeff of x^{i}"
        else:
            desc = f"BldFl1Sh({i}) -            , coeff of x^{i}"
        f.write(f"{val:<24.15f} {desc}\n")

    # Flap mode 2
    for i, val in enumerate(fl2, start=2):
        if i == 2:
            desc = f"BldFl2Sh({i}) - Flap mode 2, coeff of x^{i}"
        else:
            desc = f"BldFl2Sh({i}) -            , coeff of x^{i}"
        f.write(f"{val:<24.15f} {desc}\n")

    # Edge mode 1
    for i, val in enumerate(edg, start=2):
        if i == 2:
            desc = f"BldEdgSh({i}) - Edge mode 1, coeff of x^{i}"
        else:
            desc = f"BldEdgSh({i}) -            , coeff of x^{i}"
        f.write(f"{val:<24.15f} {desc}\n")

print("Wrote:", out)