from pathlib import Path

import typer

from .eval import MiniEvalEngine
from typing import Optional

from .models.blueprint import Blueprint
from .models.project import Project

app = typer.Typer(help="PRISM Sizing CLI")

@app.command()
def calculate(
    project_file: Path = typer.Argument(..., exists=True, help="*.sizing.yaml"),
    blueprint_dir: Optional[Path] = typer.Argument(
        None,
        exists=True,
        readable=True,
        dir_okay=True,
        file_okay=True,
        help="Каталог или файл Blueprint (default: ./blueprints)",
    ),
    json_out: Path = typer.Option(None, help="Куда сохранить JSON-результат"),
):
    """Запускает расчёт сайзинга для всех зон проекта."""
    project = Project.parse_file(project_file)

    # соберём все Blueprint-ы в памяти
    bp_files = (
        list(blueprint_dir.glob("*.blueprint.yaml")) if blueprint_dir else []
    )
    blueprints = [Blueprint.parse_file(p) for p in bp_files]

    engine = MiniEvalEngine(blueprints, project)
    result = engine.run()
    if json_out:
        json_out.write_text(result.model_dump_json(indent=2))
    else:
        typer.echo(result.json(indent=2))

if __name__ == "__main__":
    app()
