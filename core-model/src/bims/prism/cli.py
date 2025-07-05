from pathlib import Path

import typer

from .eval import MiniEvalEngine
from .models.blueprint import Blueprint
from .models.load_profile import LoadProfile

app = typer.Typer(help="PRISM Sizing CLI")

@app.command("calculate")
def calculate(
    blueprint_path: Path = typer.Argument(..., exists=True, help="*.blueprint.yaml"),
    load_path: Path = typer.Argument(..., exists=True, help="load_profile.yaml"),
    json_out: Path = typer.Option(None, help="Куда сохранить JSON-результат")
):
    """Запускает расчёт сайзинга."""
    bp = Blueprint.parse_file(blueprint_path)
    lp = LoadProfile.parse_file(load_path)
    engine = MiniEvalEngine(bp, lp)
    result = engine.run()
    if json_out:
        json_out.write_text(result.model_dump_json(indent=2))
    else:
        typer.echo(result.json(indent=2))

if __name__ == "__main__":
    app()
