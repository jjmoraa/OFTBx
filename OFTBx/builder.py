from pathlib import Path
import shutil
import warnings

def build_model_from_fst(fst_path: str, model_name: str, models_dir="models"):
    fst_path = Path(fst_path).resolve()

    if not fst_path.exists():
        raise FileNotFoundError(f"FST not found: {fst_path}")

    model_dir = Path(models_dir) / model_name

    if model_dir.exists():
        shutil.rmtree(model_dir)

    model_dir.mkdir(parents=True)

    # 1. collect all files
    files = collect_dependency_tree(fst_path)

    # 2. copy with structure
    path_map = copy_with_structure(files, model_dir)

    # 3. rewrite paths
    rewrite_all_files(path_map)

    print(f"[BUILD] Model created at: {model_dir}")
    print(f"[BUILD] Files copied: {len(files)}")

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

def collect_dependency_tree(fst_path: Path):
    visited = set()
    stack = [fst_path]

    while stack:
        current = stack.pop()

        if current in visited:
            continue

        visited.add(current)

        try:
            refs = extract_file_references(current)
        except Exception:
            continue

        for ref in refs:
            ref_path = (current.parent / ref).resolve()

            if not ref_path.exists():
                warnings.warn(f"[MISSING] {ref_path} referenced in {current}")
                continue

            stack.append(ref_path)

    return visited

def classify_file(path: Path):
    name = path.name.lower()
    parent = path.parent.name.lower()

    if name.endswith(".fst"):
        return "" 
    
    # --- Airfoils (better heuristic)
    if parent == "airfoils":
        return "aerodyn/airfoils"
    
    # --- AeroDyn main file
    if "aerodyn" in name:
        return "aerodyn"

    #if any(x in name for x in ["du", "ffa", "naca"]):
    #    return "aerodyn/airfoils"

    # --- other modules
    if "elastodyn" in name:
        return "elastodyn"
    if "beamdyn" in name:
        return "beamdyn"
    if "inflow" in name:
        return "inflow"
    if "servo" in name:
        return "servodyn"
    if "hydro" in name:
        return "hydrodyn"
    if "subdyn" in name:
        return "subdyn"

    return "misc"

from os.path import relpath

def copy_with_structure(files, model_dir):
    path_map = {}

    for f in files:
        subfolder = classify_file(f)
        target_path = model_dir / subfolder / f.name

        target_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(f, target_path)

        path_map[f.resolve()] = target_path.resolve()

    return path_map

def rewrite_all_files(path_map):
    from os.path import relpath

    for old, new in path_map.items():
        try:
            with open(new, "r") as f:
                lines = f.readlines()
        except Exception:
            continue  # skip binary or unreadable files

        new_lines = []

        for line in lines:
            updated = line

            for old_path, new_path in path_map.items():
                if old_path.name in updated:
                    rel = relpath(new_path, start=new.parent)
                    updated = updated.replace(old_path.name, rel)

            new_lines.append(updated)

        with open(new, "w") as f:
            f.writelines(new_lines)