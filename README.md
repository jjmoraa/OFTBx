# OFTBx — OpenFAST Extended Toolbox

**OFTBx** is a Python toolbox for building, organizing, and running **OpenFAST** wind turbine models programmatically.

The goal is to simplify repetitive OpenFAST workflows such as:

* Building reusable turbine models from `.fst` files
* Managing turbine objects
* Generating simulation sweeps
* Creating organized run directories
* Executing OpenFAST cases from Python

---

## Installation

Clone the repository:

```bash
git clone https://github.com/yourusername/OFTBx.git
cd OFTBx
```

Install in editable mode:

```bash
pip install -e .
```

---

## Quick Start

### 1. Build a model from an OpenFAST `.fst` file

The model builder creates a reusable turbine model directory.

```python
from OFTBx.builder import build_model_from_fst

model_path = build_model_from_fst(
    fst_path="data/IEA-15-240-RWT/OpenFAST/IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile.fst",
    model_name="iea15mw"
)
```

---

### 2. Load a turbine object

Once the model has been built, create a `Turbine` object.

```python
from OFTBx.builder import build_model_from_fst
from OFTBx.turbine import Turbine

# ------------------------------------------------------------
# 1. Build model (only once per turbine)
# ------------------------------------------------------------
model_dir = build_model_from_fst(
    fst_path="data/IEA-15-240-RWT/OpenFAST/IEA-15-240-RWT-Monopile/IEA-15-240-RWT-Monopile.fst",
    model_name="IEA15MW"
)

# ------------------------------------------------------------
# 2. Load turbine object
# ------------------------------------------------------------
turbine = Turbine(
    name="IEA15MW",
    model_path=model_dir
)
```

---

### 3. Generate an inflow sweep

Create multiple OpenFAST simulation cases across a wind speed range.

```python
from OFTBx.turbine import Turbine

turbine = Turbine(
    name="IEA15MW",
    model_path="models/IEA15MW"
)

# Create simulation directories
turbine.inflow_sweep(
    run_name="inflow_sweep",
    U_min=4,
    U_max=25,
    n=10
)
```

This generates a directory structure similar to:

```text
runs/
└── inflow_sweep/
    ├── case_01/
    │   └── case.fst
    ├── case_02/
    │   └── case.fst
    ├── ...
    └── case_10/
        └── case.fst
```

---

### 4. Run OpenFAST cases from Python

Execute previously generated cases programmatically.

```python
from pathlib import Path
from OFTBx.turbine import Turbine

turbine = Turbine(
    name="IEA15MW",
    model_path="models/IEA15MW"
)

cases_dir = Path("runs/inflow_sweep")

case_dirs = sorted([
    d for d in cases_dir.iterdir()
    if d.is_dir() and (d / "case.fst").exists()
])

results = [None] * len(case_dirs)

for i, case_dir in enumerate(case_dirs):

    print(f"[RUN] {case_dir.name}")

    results[i] = turbine.run_case(
        case_dir,
        exe="openfast"      # or full executable path
    )

print("DONE")
```

---

## Project Structure

Example project organization:

```text
project/
│
├── data/
│   └── OpenFAST input files
│
├── models/
│   └── IEA15MW/
│
├── runs/
│   └── inflow_sweep/
│
└── scripts/
    └── simulation scripts
```

---

## Requirements

* Python 3.10+
* OpenFAST installed and accessible from terminal

Verify your OpenFAST installation:

```bash
openfast --version
```

If OpenFAST is not on your PATH, provide the full executable path:

```python
turbine.run_case(
    case_dir,
    exe="/path/to/openfast"
)
```

---

## Roadmap

Planned / ongoing features:

* [ ] Batch execution utilities
* [ ] Parallel case execution
* [ ] Parametric studies
* [ ] Postprocessing tools
* [ ] Controller parameter sweeps
* [ ] Visualization utilities

---

## License

MIT License
