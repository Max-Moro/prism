import typer
from . import build_report

app = typer.Typer(help="PRISM XLSX-report CLI")

@app.command()
def generate(result_json: str, out_file: str = "report.xlsx"):
    """
    Принимает SizingResult в виде JSON-файла, отдаёт XLSX.
    CLI-обвязка для локальных smoke-тестов.
    """
    # пока не парсим JSON — передаём None
    data = build_report(None)
    with open(out_file, "wb") as fh:
        fh.write(data)

if __name__ == "__main__":
    app()
