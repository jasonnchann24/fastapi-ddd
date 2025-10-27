# cli.py
import typer
import subprocess
import os
from pathlib import Path
from dotenv import load_dotenv
from fastapi_ddd.core import database

# Get project root by going up from this file's location
# cli.py is at: /src/fastapi_ddd/cli.py
# Project root is: /
CLI_DIR = Path(
    __file__
).parent.parent.parent  # /src/fastapi_ddd -> /src -> /fastapi_ddd -> /
PROJECT_ROOT = CLI_DIR

load_dotenv(PROJECT_ROOT / ".env")

cli = typer.Typer()


def _get_domain_path(domain: str) -> str:
    return PROJECT_ROOT / "src" / "fastapi_ddd" / "domains" / domain


@cli.command()
def dev():
    """Run FastAPI development server."""
    # uvicorn.run("src.main:app", host="127.0.0.1", port=8000, reload=True)
    subprocess.run(["fastapi", "dev", "src/fastapi_ddd/main.py"])


@cli.command()
def run():
    """Run FastAPI server."""
    subprocess.run(["fastapi", "run", "src/fastapi_ddd/main.py"])


def _config_db(domain: str):
    domain_path = _get_domain_path(domain)
    db_url = database.get_db_url()

    # open env.py file if db url already set
    os.open(domain_path / "alembic" / "env.py", os.O_RDWR)
    # read file and replace db url
    with open(domain_path / "alembic" / "env.py", "r") as file:
        content = file.read()

    import_line = (
        "# AUTOIMPORT db_url\nfrom fastapi_ddd.core.database import get_db_url"
    )

    if content.find("from fastapi_ddd.core.database import get_db_url") == -1:
        # Find the last import statement
        lines = content.splitlines()
        last_import_index = -1
        for i, line in enumerate(lines):
            if line.strip().startswith(
                ("import ", "from ")
            ) and not line.strip().startswith("# "):
                last_import_index = i

        # Insert import_line after the last import
        if last_import_index != -1:
            lines.insert(last_import_index + 1, import_line)
            content = "\n".join(lines)

    content = content.replace("url=url,", "url=get_db_url(),")
    with open(domain_path / "alembic" / "env.py", "w") as file:
        file.write(content)


@cli.command()
def config_db_url(
    domain: str = typer.Argument(..., help="Domain name (e.g., user, profile)"),
):
    _config_db(domain)


@cli.command()
def migrations_init(
    domain: str = typer.Option(..., help="Domain name (e.g., user, profile)"),
):
    """Initialize Alembic for a specific domain."""
    domain_path = _get_domain_path(domain)
    alembic_path = domain_path / "alembic"

    print(f"Initializing Alembic for domain: {domain}")
    print(f"Path: {alembic_path}")

    # Change to domain directory and run alembic init
    subprocess.run(["alembic", "init", "alembic"], cwd=str(domain_path))

    # Replace script.py.mako with custom template
    template_path = PROJECT_ROOT / "templates" / "alembic" / "script.py.mako"
    target_path = alembic_path / "script.py.mako"
    if template_path.exists():
        subprocess.run(
            ["cp", str(template_path), str(target_path)],
            cwd=str(domain_path),
        )
    else:
        print("Custom Alembic template not found; using default.")

    _config_db(domain)

    # ====
    # open env.py file, check run_migrations_online() function which calls context.configure function
    # update the function from context.configure(
    #     connection=connection, target_metadata=target_metadata
    # ) to context.configure(
    #     connection=connection, target_metadata=target_metadata, version_table='alembic_version_<domain>'
    # )
    env_path = domain_path / "alembic" / "env.py"
    with open(env_path, "r") as f:
        lines = f.readlines()

    updated_lines = []
    inside_run_migrations = False
    inside_configure = False
    indent = ""

    with open(env_path, "r") as f:
        lines = f.readlines()

    updated_lines = []
    inside_run_migrations = False
    inside_configure = False
    inserted_include = False
    indent = ""

    for i, line in enumerate(lines):
        # Before we hit run_migrations_online, insert include_object (once)
        if not inserted_include and "def run_migrations_online" in line:
            include_func = (
                "\n\ndef include_object(object, name, type_, reflected, compare_to):\n"
                "    if type_ == 'table' and reflected and compare_to is None:\n"
                "        return False\n"
                "    else:\n"
                "        return True\n\n"
            )
            updated_lines.append(include_func)
            inserted_include = True

        # Detect entering run_migrations_online()
        if "def run_migrations_online" in line:
            inside_run_migrations = True

        if (
            inside_run_migrations
            and line.strip().startswith("def ")
            and "run_migrations_online" not in line
        ):
            inside_run_migrations = False

        # If inside run_migrations_online, add logic before connectable
        if inside_run_migrations:
            if "connectable = engine_from_config(" in line:
                # Insert our new line before connectable
                updated_lines.append(
                    f"    config.set_main_option('sqlalchemy.url', get_db_url())\n"
                )

        # If inside run_migrations_online, look for context.configure(
        if inside_run_migrations and "context.configure(" in line:
            inside_configure = True
            indent = line[: len(line) - len(line.lstrip())]  # preserve indentation
            updated_lines.append(line)
            continue

        # While inside context.configure( block
        if inside_configure:
            if ")" in line.strip():  # closing line found
                # Insert our new line before the closing parenthesis
                updated_lines.append(
                    f",\n{indent}    version_table='alembic_version_{domain}', include_object=include_object\n"
                )
                updated_lines.append(line)
                inside_configure = False
            else:
                updated_lines.append(line)
            continue

        updated_lines.append(line)

        with open(env_path, "w") as f:
            f.writelines(updated_lines)
    subprocess.run(["ruff", "format", str(domain_path / "alembic" / "env.py")])

    # ====


@cli.command()
def migrations_update(
    domain: str = typer.Option(..., help="Domain name (e.g., user, profile)"),
):
    """Create new Alembic migration for a specific domain."""
    domain_path = _get_domain_path(domain)

    print(f"Generating migration for domain: {domain}")

    # Set environment variable so env.py knows which domain to migrate
    env = os.environ.copy()
    env["ALEMBIC_DOMAIN"] = domain

    # open models file of the domain, and get class which inherits SQLModel
    import importlib
    import inspect
    from sqlmodel import SQLModel

    # Import the models module dynamically
    models_module = importlib.import_module(f"fastapi_ddd.domains.{domain}.models")

    # Get all classes that inherit from SQLModel and are tables
    model_classes = []

    for name, obj in inspect.getmembers(models_module):
        if inspect.isclass(obj) and issubclass(obj, SQLModel) and obj is not SQLModel:
            # Check if class has table=True by looking for __table__ or __tablename__
            has_table = getattr(obj, "__table__", None) is not None
            if has_table:
                model_classes.append(name)

    print(f"Found model classes for migration: {model_classes}")

    # ensure env.py has all models listed and imported and target_metadata set
    with open(domain_path / "alembic" / "env.py", "r") as file:
        content = file.read()

    # Create import line for all models
    if model_classes:
        import_line = f"# AUTOGENERATED IMPORT\nfrom fastapi_ddd.domains.{domain}.models import {', '.join(model_classes)}"
        # remove 2 lines above
        if "# AUTOGENERATED IMPORT" in content:
            # remove first two lines
            content_lines = content.splitlines()
            content_lines = content_lines[2:]
            content = "\n".join(content_lines)
        # add new lines at the top
        content = import_line + "\n" + content

        # replace target_metadata line with combined metadata
        metadata_list = ", ".join(map(lambda x: f"{x}.metadata", model_classes))
        content_lines = content.splitlines(keepends=True)
        updated_lines = []
        found = False
        for line in content_lines:
            if line.strip().startswith("target_metadata") and not found:
                # Replace the entire target_metadata line
                updated_lines.append(f"target_metadata = [{metadata_list}]\n")
                found = True
            else:
                updated_lines.append(line)
        content = "".join(updated_lines)

    # Write updated env.py
    with open(domain_path / "alembic" / "env.py", "w") as file:
        file.write(content)

    # Run alembic from the domain directory
    subprocess.run(
        [
            "alembic",
            "revision",
            "--autogenerate",
            "-m",
            f"Update {domain} models",
        ],
        cwd=str(domain_path),
        env=env,
    )

    subprocess.run(["ruff", "format", str(domain_path / "alembic" / "env.py")])


@cli.command()
def migrations_run(
    domain: str = typer.Option(
        None,
        help="Domain name (e.g., user, profile). If not specified, runs for all domains.",
    ),
):
    """Run migrations for a specific domain or all domains."""
    from fastapi_ddd.core.config import INSTALLED_DOMAINS

    if domain:
        # Run migration for specific domain
        domain_path = _get_domain_path(domain)
        print(f"Running migrations for domain: {domain}")

        subprocess.run(
            [
                "alembic",
                "upgrade",
                "head",
            ],
            cwd=str(domain_path),
        )
    else:
        # Run migrations for all domains
        for dom in INSTALLED_DOMAINS:
            domain_path = _get_domain_path(dom)
            print(f"\nRunning migrations for domain: {dom}")
            subprocess.run(
                [
                    "alembic",
                    "upgrade",
                    "head",
                ],
                cwd=str(domain_path),
            )


@cli.command()
def seed():
    """Seed the database."""
    print("Seeding DB...")


if __name__ == "__main__":
    cli()
