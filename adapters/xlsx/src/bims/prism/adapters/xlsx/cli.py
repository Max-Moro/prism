import json
from pathlib import Path
from typing import Any, Dict

import typer

from . import build_report

app = typer.Typer(help="PRISM XLSX-report CLI")

@app.command()
def generate(result_json: str, out_file: str = "report.xlsx"):
    """
    Принимает SizingResult (JSON-файл) → сохраняет XLSX.
    """
    path = Path(result_json)
    if not path.exists():
        typer.echo(f"[ERR] Файл не найден: {path}", err=True)
        raise typer.Exit(code=1)

    try:
        sizing: Dict[str, Any] = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        typer.echo(f"[ERR] Некорректный JSON: {exc}", err=True)
        raise typer.Exit(code=2)

    if "zones" not in sizing:  # легчайшая валидация
        typer.echo("[ERR] JSON не похож на SizingResult: отсутствует ключ 'zones'", err=True)
        raise typer.Exit(code=3)

    data = build_report(sizing)
    with open(out_file, "wb") as fh:
        fh.write(data)

if __name__ == "__main__":
    app()
