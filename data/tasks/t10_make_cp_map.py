import subprocess
from pathlib import Path

yaml_file = Path("models/IEA15MW_reference/servodyn/IEA15MW.yaml").resolve()
output_file = Path("models/IEA15MW_reference/servodyn/Cp_Ct_Cq.IEA15MW.txt").resolve()

code = f"""
from rosco.toolbox import turbine as ROSCO_turbine
from rosco.toolbox.utilities import write_rotor_performance
from rosco.toolbox.inputs.validation import load_rosco_yaml
from pathlib import Path

yaml_file = Path(r'{yaml_file}')
output_file = Path(r'{output_file}')

inps = load_rosco_yaml(str(yaml_file))

path_params = inps['path_params']
turbine_params = inps['turbine_params']

turbine = ROSCO_turbine.Turbine(turbine_params)

fast_dir = yaml_file.parent / path_params['FAST_directory']

turbine.load_from_fast(
    path_params['FAST_InputFile'],
    str(fast_dir),
    rot_source='cc-blade',
    txt_filename=None
)

write_rotor_performance(
    turbine,
    txt_filename=str(output_file)
)
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