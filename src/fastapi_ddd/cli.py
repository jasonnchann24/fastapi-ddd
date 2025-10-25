# cli.py
import typer
import uvicorn
import subprocess


cli = typer.Typer()


@cli.command()
def dev():
    """Run FastAPI development server."""
    # uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
    subprocess.run(["fastapi", "dev", "src/fastapi_ddd/main.py"])


@cli.command()
def run():
    """Run FastAPI server."""
    subprocess.run(["fastapi", "run", "src/fastapi_ddd/main.py"])


@cli.command()
def seed():
    """Seed the database."""
    print("Seeding DB...")


if __name__ == "__main__":
    cli()
