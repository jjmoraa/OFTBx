import numpy as np

with open("models/IEA15MW_reference/elastodyn/blade_elastodyn.dat") as f:
    lines = f.readlines()

# locate table
for i, line in enumerate(lines):
    if "BlFract" in line:
        header_idx = i
        break

data_start = header_idx + 2

# find mode shape section
for i in range(data_start, len(lines)):
    if "BLADE MODE SHAPES" in lines[i]:
        data_end = i
        break

# read 51x6 table
data = np.loadtxt(lines[data_start:data_end])

# resample
r_new = np.linspace(0.0, 1.0, 50)

data_new = np.column_stack([
    np.interp(r_new, data[:,0], data[:,j])
    for j in range(data.shape[1])
])

data_new[:,0] = r_new

# update NBlInpSt
for i, line in enumerate(lines):
    if "NBlInpSt" in line:
        lines[i] = "50                     NBlInpSt    - Number of blade input stations (-)\n"
        break

# rebuild table
table_lines = [
    " {:24.15e} {:24.15e} {:24.15e} {:24.15e} {:24.15e} {:24.15e}\n".format(*row)
    for row in data_new
]

new_lines = (
    lines[:data_start]
    + table_lines
    + lines[data_end:]
)

with open("dfl_blade_elastodyn_50.dat", "w") as f:
    f.writelines(new_lines)