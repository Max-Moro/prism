"""
Генерирует Pydantic-модели из JSON-Schema.

Public-контракты (`SizingResult`, `Project`, `LoadProfile`) лежат
в пакете **prism-common**, остальные схемы остаются локально.

| Schema-файл                  | Где лежит                             | Выходной модуль                    |
| -----------------------------|---------------------------------------|------------------------------------|
| blueprint.schema.json        | core-model/src/bims/prism/schemas/    | models/_gen/blueprint_gen/ (pkg)   |
| load_profile.schema.json     | common/src/bims/prism/common/schemas/ | models/_gen/load_profile_gen.py    |
| project.schema.json          |   »                                   | models/_gen/project_gen/  (pkg)    |
| sizing_result.schema.json    |   »                                   | models/_gen/sizing_result_gen.py   |

Запуск из корня репозитория (Windows / *nix):
> python scripts\\gen_models.py
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

# ──────────────────────────── paths ───────────────────────────────
ROOT = Path(__file__).resolve().parent.parent.parent

# локальные (внутренние) схемы ядра
CORE_SCHEMA_DIR    = ROOT / "core-model" / "src" / "bims" / "prism" / "schemas"
# публичные схемы (prism-common)
COMMON_SCHEMA_DIR  = (
    ROOT / "common" / "src" / "bims" / "prism" / "common" / "schemas"
)

OUT_DIR = ROOT / "core-model" / "src" / "bims" / "prism" / "models" / "_gen"
OUT_DIR.mkdir(parents=True, exist_ok=True)

# файл → (каталог-схем,  output-путь, is_dir)
SCHEMAS = [
    # schema                    # out-rel-path            # dir?
    ("blueprint.schema.json",    CORE_SCHEMA_DIR,   "blueprint_gen",        True),
    ("load_profile.schema.json", COMMON_SCHEMA_DIR, "load_profile_gen.py",  False),
    ("project.schema.json",      COMMON_SCHEMA_DIR, "project_gen",          True),
    ("sizing_result.schema.json",COMMON_SCHEMA_DIR, "sizing_result_gen.py", False),
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
for schema_name, schema_dir, rel_out, as_dir in SCHEMAS:
    in_path = schema_dir / schema_name
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
