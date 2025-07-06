"""
Генерирует Pydantic-модели из JSON-Schema для:
  • blueprint.schema.json     →  models/_gen/blueprint_gen/   (каталог-пакет)
  • load_profile.schema.json  →  models/_gen/load_profile_gen.py
  • project.schema.json       →  models/_gen/project_gen.py

Запуск из корня репозитория (Windows / *nix):
> python scripts\\gen_models.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ──────────────────────────── paths ───────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent

SCHEMA_DIR = ROOT / "core-model" / "src" / "bims" / "prism" / "schemas"
OUT_DIR    = ROOT / "core-model" / "src" / "bims" / "prism" / "models" / "_gen"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# (schema-file,   output-relative-path, is_directory_output?)
SCHEMAS = [
    # schema-file               # output-relative-path      # is_directory_output
    ("blueprint.schema.json",    "blueprint_gen",          True),   # каталог
    ("load_profile.schema.json", "load_profile_gen.py",    False),  # файл
    ("project.schema.json",      "project_gen",            True),   # каталог  ← FIX
]

BASE_CMD = [
    sys.executable,
    "-m",
    "datamodel_code_generator",
    "--input-file-type", "jsonschema",
    "--base-class",      "pydantic.BaseModel",
    "--target-python-version", "3.12",
    "--disable-timestamp",
    "--field-constraints",
]

# ──────────────────────────── run generator ───────────────────────
for schema_name, rel_out, as_dir in SCHEMAS:
    in_path = SCHEMA_DIR / schema_name
    out_path = OUT_DIR / rel_out

    if as_dir:
        # каталог:  datamodel-code-generator сам создаст __init__.py + модули
        cmd = BASE_CMD + ["--input", str(in_path), "--output", str(out_path)]
    else:
        # одиночный файл
        cmd = BASE_CMD + ["--input", str(in_path), "--output", str(out_path)]

    print(f"▶  Generating {rel_out} …")
    subprocess.check_call(cmd)
    print(f"   ✔ Saved to {out_path.relative_to(ROOT)}")

# ──────────────────────────── auto-format (optional) ──────────────
try:
    subprocess.check_call(["ruff", "format", str(OUT_DIR)])
except FileNotFoundError:
    print("⚠ Ruff not found — skipping formatting.")

print("✅  All models regenerated.")
