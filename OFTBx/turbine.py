from pathlib import Path
import shutil
import numpy as np
import re
import os
from shutil import which
import platform

class Turbine:
    """
    Represents a fully structured OpenFAST turbine model.

    Source of truth = model_path (produced by builder)
    """

    def __init__(self, name: str, model_path: str):
        self.name = name
        self.model_path = Path(model_path).resolve()

        if not self.model_path.exists():
            raise FileNotFoundError(
                f"Turbine model not found: {self.model_path}"
            )

    # ------------------------------------------------------------
    # RUN CASE GENERATION
    # ------------------------------------------------------------
    def inflow_sweep(
        self,
        run_name: str,
        U_min: float,
        U_max: float,
        n: int,
        runs_dir: str = "runs"
    ):
        """
        Generate multiple OpenFAST cases with varying inflow velocity.

        Creates:
            runs/run_name/U_xx.x/
                case.fst
                InflowWind.dat
        """

        run_root = Path(runs_dir) / run_name

        if run_root.exists():
            shutil.rmtree(run_root)

        run_root.mkdir(parents=True)

        # ------------------------------------------------------------
        # 1. Get base fst
        # ------------------------------------------------------------
        base_fst = next(self.model_path.glob("*.fst"))

        # ------------------------------------------------------------
        # 2. Find base inflow file from fst
        # ------------------------------------------------------------
        inflow_dir = self.model_path / "inflow"
        base_inflow = next(inflow_dir.glob("*"))

        # ------------------------------------------------------------
        # 3. Velocity grid
        # ------------------------------------------------------------
        velocities = np.linspace(U_min, U_max, n)

        case_dirs = []

        for U in velocities:
            case_name = f"U_{U:.1f}"
            case_dir = run_root / case_name
            case_dir.mkdir()

            # --------------------------------------------------------
            # Copy and modify inflow
            # --------------------------------------------------------
            inflow_target = case_dir / base_inflow.name
            shutil.copy2(base_inflow, inflow_target)

            self._set_inflow_velocity(inflow_target, U)

            # --------------------------------------------------------
            # Copy and patch fst
            # --------------------------------------------------------
            case_fst = case_dir / "case.fst"

            self._relocalize_fst_paths(
                fst_path=base_fst,
                model_root=self.model_path,
                case_dir=case_dir
            )

            case_dirs.append(case_dir)

        return case_dirs

    def _relocalize_fst_paths(self, fst_path: Path, model_root: Path, case_dir: Path):
        """
        Rewrite ONLY INPUT FILES section of FST so case becomes self-contained.
        """

        lines = fst_path.read_text().splitlines()

        new_lines = []
        in_input_files = False

        for line in lines:

            # ------------------------------------------------------------
            # Detect section start
            # ------------------------------------------------------------
            if "INPUT FILES" in line:
                in_input_files = True
                new_lines.append(line)
                continue

            # ------------------------------------------------------------
            # Detect section end
            # ------------------------------------------------------------
            if in_input_files and line.startswith("---------------------- OUTPUT"):
                in_input_files = False
                new_lines.append(line)
                continue

            # ------------------------------------------------------------
            # Outside INPUT FILES → DO NOT TOUCH
            # ------------------------------------------------------------
            if not in_input_files:
                new_lines.append(line)
                continue

            # ------------------------------------------------------------
            # Inside INPUT FILES → apply relocalization
            # ------------------------------------------------------------

            if "InflowFile" in line or "InflowWind" in line:
                matches = re.findall(r'"([^"]+)"', line)

                for m in matches:
                    if m.lower() == "none":
                        continue

                    inflow_name = Path(m).name  # strip any folder structure

                    line = line.replace(f'"{m}"', f'"{inflow_name}"')

                new_lines.append(line)
                continue

            matches = re.findall(r'"([^"]+)"', line)

            if not matches:
                new_lines.append(line)
                continue

            for m in matches:

                if m.lower() == "none":
                    continue

                # # ignore junk tokens that are not files
                # if "/" not in m and "\\" not in m and not m.endswith((".dat", ".txt", ".inp")):
                #     continue

                abs_path = (model_root / m)

                if not abs_path.exists():
                    continue

                
                rel_path = Path(os.path.relpath(abs_path, start=case_dir))

                line = line.replace(f'"{m}"', f'"{rel_path}"')

            new_lines.append(line)

        (case_dir / "case.fst").write_text("\n".join(new_lines) + "\n")

    def _set_inflow_velocity(self, inflow_path: Path, U: float):
        """
        Set HWindSpeed in an InflowWind file.
        """

        lines = inflow_path.read_text().splitlines()

        for i, line in enumerate(lines):
            if "HWindSpeed" in line:
                parts = line.split()
                parts[0] = f"{U:.3f}"
                lines[i] = "   ".join(parts)
                break
        else:
            raise RuntimeError("HWindSpeed not found in inflow file")

        inflow_path.write_text("\n".join(lines) + "\n")

    def _set_wind_type(self, inflow_path: Path, wind: int):
        """
        Set WindType in an InflowWind file.
        """

        lines = inflow_path.read_text().splitlines()

        for i, line in enumerate(lines):
            if "WindType" in line:
                parts = line.split()
                parts[0] = f"{wind:d}"
                lines[i] = "   ".join(parts)
                break
        else:
            raise RuntimeError("WindType not found in inflow file")

        inflow_path.write_text("\n".join(lines) + "\n")

    def _modify_inflowwind(self, inflow_path: Path, params: dict):
        """
        Modify parameters in an InflowWind file using a dictionary.

        Parameters
        ----------
        inflow_path : Path
            Path to InflowWind input file.

        params : dict
            Example:
            {
                "WindType": 3,
                "HWindSpeed": 12.0,
                "AnalysisTime": 720.0
            }
        """

        lines = inflow_path.read_text().splitlines()

        found = set()

        for i, line in enumerate(lines):
            stripped = line.strip()

            # skip empty or separator lines
            if not stripped or stripped.startswith("=") or stripped.startswith("-"):
                continue

            parts = stripped.split()

            if len(parts) < 2:
                continue

            param_name = parts[1]

            if param_name not in params:
                continue

            value = params[param_name]

            # ---- format value ----
            if isinstance(value, bool):
                value_str = "True" if value else "False"

            elif isinstance(value, str):
                value_str = f'"{value}"' if " " in value else value

            elif isinstance(value, int):
                value_str = f"{value:d}"

            else:
                value_str = str(value)

            # replace only the value column
            parts[0] = value_str
            lines[i] = "    ".join(parts)

            found.add(param_name)

        missing = set(params.keys()) - found

        if missing:
            raise RuntimeError(
                f"InflowWind parameters not found: {sorted(missing)}"
            )

        inflow_path.write_text("\n".join(lines) + "\n")

    def _make_turbsim_inp(
        self,
        inp_path: Path,
        params: dict,
            ):
            """
            Modify parameters in a TurbSim .inp file.

            Parameters
            ----------
            inp_path : Path
                TurbSim input file.

            params : dict
                Dictionary of parameter names and values, e.g.

                {
                    "URef": 12.0,
                    "RandSeed1": 12345,
                    "PLExp": 0.14,
                    "IECturbc": "A",
                    "Clockwise": True,
                }
            """

            lines = inp_path.read_text().splitlines()

            found = set()

            for i, line in enumerate(lines):

                stripped = line.strip()

                if not stripped:
                    continue

                parts = stripped.split()

                if len(parts) < 2:
                    continue

                parameter = parts[1]

                if parameter not in params:
                    continue

                value = params[parameter]

                # format value
                if isinstance(value, bool):
                    value_str = "True" if value else "False"

                elif isinstance(value, str):
                    if " " in value:
                        value_str = f'"{value}"'
                    else:
                        value_str = value

                else:
                    value_str = str(value)

                parts[0] = value_str

                lines[i] = "    ".join(parts)

                found.add(parameter)

            missing = set(params.keys()) - found

            if missing:
                raise RuntimeError(
                    f"Parameters not found in TurbSim file: {sorted(missing)}"
                )

            inp_path.write_text("\n".join(lines) + "\n")

    def _replace_inflow_path(self, fst_text: str, inflow_filename: str):
        lines = fst_text.splitlines()

        for i, line in enumerate(lines):
            if "InflowFile" in line:
                parts = line.split()
                # replace last quoted field safely
                for j, p in enumerate(parts):
                    if ".dat" in p or ".txt" in p:
                        parts[j] = f'"{inflow_filename}"'
                        break
                lines[i] = "  ".join(parts)

        return "\n".join(lines) + "\n"


    def _replace_inflow_path(self, fst_path: Path, new_name: str):
        lines = fst_path.read_text().splitlines()

        for i, line in enumerate(lines):
            if "InflowFile" in line:
                import re
                lines[i] = re.sub(r'"([^"]+)"', f'"{new_name}"', line)
                break

        fst_path.write_text("\n".join(lines) + "\n")

    def run_case(self, case_dir: str, exe: str = None):
        """
        Cross-platform OpenFAST execution.
        """

        import subprocess
        from pathlib import Path

        case_dir = Path(case_dir).resolve()
        fst_file = case_dir / "case.fst"

        if not fst_file.exists():
            raise FileNotFoundError(f"Missing FST: {fst_file}")

        exe = self._resolve_openfast_exe(exe)

        cmd = [exe, str(fst_file.name)]

        process = subprocess.run(
            cmd,
            cwd=case_dir,
            capture_output=True,
            text=True
        )

        return {
            "case": str(case_dir),
            "success": process.returncode == 0,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exe_used": exe
        }

    def run_turbsim(self, case_dir: str, exe: str = None):
        """
        Cross-platform TurbSim execution.
        """

        import subprocess
        from pathlib import Path

        case_dir = Path(case_dir).resolve()

        inp_files = list(case_dir.glob("*.in"))

        if len(inp_files) == 0:
            raise FileNotFoundError(
                f"No .inp file found in {case_dir}"
            )

        if len(inp_files) > 1:
            raise RuntimeError(
                f"Multiple .inp files found in {case_dir}: "
                f"{[f.name for f in inp_files]}"
            )

        inp_file = inp_files[0]

        exe = self._resolve_turbsim_exe(exe)

        cmd = [exe, inp_file.name]

        process = subprocess.run(
            cmd,
            cwd=case_dir,
            capture_output=True,
            text=True
        )

        return {
            "case": str(case_dir),
            "success": process.returncode == 0,
            "stdout": process.stdout,
            "stderr": process.stderr,
            "exe_used": exe
        }
    
    # ------------------------------------------------------------
    # STRUCTURE ACCESSORS
    # ------------------------------------------------------------
    def path(self):
        return self.model_path

    def module(self, name: str):
        return self.model_path / name

    def aerodyn(self):
        return self.model_path / "aerodyn"

    def airfoils(self):
        return self.model_path / "aerodyn" / "airfoils"

    def elastodyn(self):
        return self.model_path / "elastodyn"

    def servodyn(self):
        return self.model_path / "servodyn"

    # ------------------------------------------------------------
    def __repr__(self):
        return f"Turbine(name={self.name}, model={self.model_path})"

    def _resolve_openfast_exe(self, exe: str | None = None):
        """
        Resolve OpenFAST executable in a cross-platform way.
        """

        # 1. user override always wins
        if exe is not None:
            return exe

        system = platform.system().lower()

        # 2. platform defaults
        if system == "windows":
            candidates = ["OpenFAST.exe", "openfast.exe"]
        else:
            candidates = ["openfast"]

        # 3. try PATH lookup
        for c in candidates:
            if which(c) is not None:
                return c

        raise FileNotFoundError(
            "OpenFAST executable not found. "
            "Please install it or pass exe=..."
        )
    
    def _resolve_turbsim_exe(self, exe: str | None = None):
        """
        Resolve TurbSim executable in a cross-platform way.
        """

        # 1. user override always wins
        if exe is not None:
            return exe

        system = platform.system().lower()

        # 2. platform defaults
        if system == "windows":
            candidates = [
                "TurbSim.exe",
                "turbsim.exe"
            ]
        else:
            candidates = [
                "TurbSim",
                "turbsim"
            ]

        # 3. try PATH lookup
        for c in candidates:
            if which(c) is not None:
                return c

        raise FileNotFoundError(
            "TurbSim executable not found. "
            "Please install it or pass exe=..."
        )

    # ------------------------------------------------------------
    # MAKE IEC Case 1.3
    # ------------------------------------------------------------
    def IEC_case(
        self,
        run_name: str,
        case: str,
        runs_dir: str = "runs"
    ):
        """
        Generate multiple OpenFAST cases with varying inflow velocity.

        Creates:
            runs/run_name/U_xx.x/
                case.fst
                InflowWind.dat
        """

        run_root = Path(runs_dir) / run_name

        if run_root.exists():
            shutil.rmtree(run_root)

        run_root.mkdir(parents=True)

        # ------------------------------------------------------------
        # 1. Get base fst
        # ------------------------------------------------------------
        base_fst = next(self.model_path.glob("*.fst"))

        # ------------------------------------------------------------
        # 2. Find base inflow file and turbsim inp from fst
        # ------------------------------------------------------------
        inflow_dir = self.model_path / "inflow"
        base_inflow = next(inflow_dir.glob("*.dat"))
        base_inp = next(inflow_dir.glob("*.in"))

        # ------------------------------------------------------------
        # 3. Velocity grid
        # ------------------------------------------------------------

        if case == '1_3':
            velocities = [8.65, 10.65, 12.65, 25]

            case_dirs = []

            for U in velocities:
                case_name = f"U_{U:.1f}"
                case_dir = run_root / case_name
                case_dir.mkdir()

                # --------------------------------------------------------
                # Copy and modify inflow
                # --------------------------------------------------------
                inflow_target = case_dir / base_inflow.name
                shutil.copy2(base_inflow, inflow_target)

                self._set_wind_type(inflow_target, 3)

                # --------------------------------------------------------
                # Make turbsim file inp file
                # --------------------------------------------------------
                turbsim_target = case_dir / base_inp.name
                shutil.copy2(base_inp, turbsim_target)

                self._make_turbsim_inp(
                    turbsim_target,
                    {
                        "URef": U,
                        "RandSeed1": 987654,
                        "PLExp": 0.12,
                        "IECturbc": "A",
                        "Clockwise": False,
                        "AnalysisTime": 3600,
                        "GridHeight": 260, 
                        "GridWidth": 260
                    },
                )

                self._modify_inflowwind(
                    inflow_target,
                    {
                        "FileName_BTS": str(turbsim_target)
                    }
                )
                # --------------------------------------------------------
                # Run TurbSim
                # --------------------------------------------------------
                print(f"running turbsim for case {turbsim_target}")
                ts_result = self.run_turbsim(case_dir)

                if not ts_result["success"]:
                    raise RuntimeError(
                        f"TurbSim failed for {case_dir}\n\n"
                        f"{ts_result['stdout']}\n"
                        f"{ts_result['stderr']}"
                    )
                # --------------------------------------------------------
                # Copy and patch fst
                # --------------------------------------------------------
                case_fst = case_dir / "case.fst"

                self._relocalize_fst_paths(
                    fst_path=base_fst,
                    model_root=self.model_path,
                    case_dir=case_dir
                )

                case_dirs.append(case_dir)

                self._modify_openfast_like_file(
                    case_fst,
                    {
                        "TMax": 3600
                    }
                )

        return case_dirs
    

    def _modify_openfast_like_file(self, file_path: Path, params: dict):
        """
        Generic modifier for OpenFAST / InflowWind / TurbSim-style input files.
        """

        lines = file_path.read_text().splitlines()

        found = set()

        for i, line in enumerate(lines):

            stripped = line.strip()

            # skip blank or separator lines
            if not stripped or stripped.startswith(("-", "=")):
                continue

            parts = stripped.split()

            if len(parts) < 2:
                continue

            key = parts[1]

            if key not in params:
                continue

            value = params[key]

            # -------- formatting --------
            if isinstance(value, bool):
                value_str = "True" if value else "False"

            elif isinstance(value, str):
                # keep quotes if needed
                if value.startswith('"') and value.endswith('"'):
                    value_str = value
                else:
                    value_str = f'"{value}"' if " " in value else value

            else:
                value_str = str(value)

            # replace ONLY the first column (value)
            parts[0] = value_str

            # IMPORTANT: preserve readability better than naive join
            lines[i] = "  ".join(parts)

            found.add(key)

        missing = set(params.keys()) - found

        if missing:
            raise RuntimeError(f"Parameters not found: {sorted(missing)}")

        file_path.write_text("\n".join(lines) + "\n")