import subprocess
from pathlib import Path

yaml_file = Path("models/IEA15MW_reference/servodyn/IEA15MW.yaml").resolve()
out_dir = Path("models/IEA15MW_reference/servodyn").resolve()

cp_file = out_dir / "Cp_Ct_Cq.IEA15MW.txt"
discon_file = out_dir / "DISCON.IN"

code = f"""
from rosco.toolbox import controller as ROSCO_controller
from rosco.toolbox import turbine as ROSCO_turbine
from rosco.toolbox.utilities import write_DISCON
from rosco.toolbox.inputs.validation import load_rosco_yaml
from pathlib import Path

yaml_file = Path(r'{yaml_file}')
cp_file = Path(r'{cp_file}')
discon_file = Path(r'{discon_file}')

inps = load_rosco_yaml(str(yaml_file))
path_params = inps['path_params']
turbine_params = inps['turbine_params']
controller_params = inps['controller_params']

model_root = yaml_file.parent
fast_dir = model_root / path_params['FAST_directory']

# IMPORTANT: use CP file from OUTSIDE, not inside model folder
turbine = ROSCO_turbine.Turbine(turbine_params)

turbine.load_from_fast(
    path_params['FAST_InputFile'],
    str(fast_dir),
    rot_source='txt',
    txt_filename=str(cp_file)
)

controller = ROSCO_controller.Controller(controller_params)
controller.tune_controller(turbine)

write_DISCON(
    turbine,
    controller,
    param_file=str(discon_file),
    txt_filename=str(cp_file)
)

print("Controller tuning complete")
"""

subprocess.run(
    [
        "/home/jjmoraa/miniconda3/envs/rosco-env_2.9/bin/python",
        "-c",
        code,
    ],
    cwd="/home/jjmoraa/work/project/OFTBx",
    check=True,
)