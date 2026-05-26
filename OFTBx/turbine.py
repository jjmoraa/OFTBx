from pathlib import Path
import shutil
import numpy as np
import re
import os

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
    
    import platform
    from shutil import which


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