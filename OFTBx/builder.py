from pathlib import Path
import shutil
import warnings

def build_model_from_fst(fst_path: str, model_name: str, models_dir="models"):
    """
    Minimal builder:
    - takes an OpenFAST .fst file
    - creates a model folder
    - copies .fst into it as base definition
    """

    fst_path = Path(fst_path).resolve()

    if not fst_path.exists():
        raise FileNotFoundError(f"FST not found: {fst_path}")

    model_dir = Path(models_dir) / model_name

    # clean build
    if model_dir.exists():
        shutil.rmtree(model_dir)

    model_dir.mkdir(parents=True)

    copied_files = copy_dependency_tree(fst_path, model_dir)

    # copy main fst
    shutil.copy2(fst_path, model_dir / "base.fst")

    print(f"[BUILD] Model created at: {model_dir}")
    print(f"[BUILD] Files copied: {len(copied_files)}")

    return model_dir

import re
from pathlib import Path


def extract_file_references(file_path: Path):
    """
    Extract ONLY quoted file references from OpenFAST input files.
    This avoids numbers, comments, and garbage tokens.
    """

    refs = []

    with open(file_path, "r") as f:
        for line in f:
            # remove comments
            line = line.split("!")[0]

            # find quoted strings
            matches = re.findall(r'"([^"]+)"', line)

            for m in matches:
                # ignore "none"
                if m.lower() == "none":
                    continue

                refs.append(m)

    return refs

def copy_dependency_tree(fst_path: Path, model_dir: Path):
    """
    Recursively copies all files referenced by fst and subfiles.
    """

    visited = set()
    stack = [fst_path]

    base_dir = fst_path.parent

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        # copy file
        target_path = model_dir / current.name

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(current, target_path)

        # find references inside file
        try:
            refs = extract_file_references(current)
        except Exception:
            continue

        for ref in refs:
            ref_path = (current.parent / ref).resolve()

            for ref in refs:
                ref_path = (current.parent / ref).resolve()

                if not ref_path.exists():
                    warnings.warn(f"[MISSING] {ref_path} referenced in {current}")
                    continue

                stack.append(ref_path)

    return visited
    