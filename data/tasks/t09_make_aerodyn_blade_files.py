import numpy as np
from scipy.io import loadmat

filename = "./models/IEA15MW_reference/refBlade_20260607.mat"

# -------------------------------------------------
# 1. Load MAT file
# -------------------------------------------------
data = loadmat(filename, squeeze_me=True, struct_as_record=False)

blade = data["S"].fastBlade

import numpy as np

S = data["S"]

# --------------------------------------------
# AeroDyn blade file
# --------------------------------------------

adb = S.geometryVec      # <- replace with actual field name

span  = np.array(adb.span).squeeze()
twist = np.array(adb.degreestwist).squeeze()
chord = np.array(adb.chord).squeeze()
afid  = np.array(adb.afID).squeeze()

prebend = np.array(adb.prebend).squeeze().astype(float)
sweep   = np.array(adb.sweep).squeeze().astype(float)

outfile = "blade_aerodyn.dat"

with open(outfile, "w") as f:

    f.write("------- AERODYN v15.00.* BLADE DEFINITION INPUT FILE -------------------------------------\n")
    f.write(f"Generated from MATLAB blade design file {filename}\n")
    f.write("======  Blade Properties =================================================================\n")

    f.write(
        f"{len(span):d}          NumBlNds    - Number of blade nodes used in the analysis (-)\n"
    )

    f.write(
        "    BlSpn        BlCrvAC        BlSwpAC        BlCrvAng       BlTwist        BlChord          BlAFID    BlCb    BlCenBn    BlCenBt\n"
    )

    f.write(
        "     (m)           (m)            (m)            (deg)         (deg)           (m)              (-)     (-)     (m)        (m)\n"
    )

    for i in range(len(span)):

        f.write(
            f"{span[i]:23.15e} "
            f"{prebend[i]:23.15e} "
            f"{sweep[i]:23.15e} "
            f"{0.0:23.15e} "
            f"{twist[i]:23.15e} "
            f"{chord[i]:23.15e} "
            f"{int(afid[i]):8d} "
            f"{0.0:8.1f} "
            f"{0.0:8.1f} "
            f"{0.0:8.1f}\n"
        )

print("Wrote:", outfile)