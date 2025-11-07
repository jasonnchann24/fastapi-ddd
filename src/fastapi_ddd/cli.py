# cli.py
import typer
import subprocess
import os
import secrets
import base64
import asyncio
import importlib
import inspect
from pathlib import Path
from dotenv import load_dotenv
from fastapi_ddd.core import database
from rich.console import Console
from sqlmodel.ext.asyncio.session import AsyncSession
from fastapi_ddd.core.database import engine

# Get project root by going up from this file's location
# cli.py is at: /src/fastapi_ddd/cli.py
# Project root is: /
CLI_DIR = Path(
    __file__
).parent.parent.parent  # /src/fastapi_ddd -> /src -> /fastapi_ddd -> /
PROJECT_ROOT = CLI_DIR

load_dotenv(PROJECT_ROOT / ".env")

cli = typer.Typer()

console = Console()


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
def migration_init(
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
def migration_update(
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
        import_line = (
            f"from fastapi_ddd.core.base.base_model import BaseModel\n"
            f"# AUTOGENERATED IMPORT\nfrom fastapi_ddd.domains.{domain}.models import {', '.join(model_classes)}"
        )
        # remove 2 lines above
        if "# AUTOGENERATED IMPORT" in content:
            # remove first two lines
            content_lines = content.splitlines()
            content_lines = content_lines[2:]
            content = "\n".join(content_lines)
        # add new lines at the top
        content = import_line + "\n" + content

        # Replace target_metadata with BaseModel.metadata
        # all domain tables share same MetaData through inheritance
        content_lines = content.splitlines(keepends=True)
        updated_lines = []
        found = False
        for line in content_lines:
            if line.strip().startswith("target_metadata") and not found:
                updated_lines.append("target_metadata = BaseModel.metadata\n")
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
def migration_run(
    domain: str = typer.Option(
        None,
        help="Domain name (e.g., user, profile). If not specified, runs for all domains.",
    ),
):
    """Run migrations for a specific domain or all domains."""
    from fastapi_ddd.core.config import settings

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
        for dom in settings.installed_domains:
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
def migration_drop(
    domain: str = typer.Option(
        None,
        "--domain",
        "-d",
        help="Domain name to drop tables for (e.g., authentication, authorization). If not specified, drops all domains.",
    ),
    confirm: bool = typer.Option(
        False,
        "--yes",
        "-y",
        help="Skip confirmation prompt",
    ),
):
    """Drop tables for a specific domain or all domains.

    Usage:
        fastapi_ddd migration-drop                      # Drop all domains (interactive)
        fastapi_ddd migration-drop --yes                # Drop all domains (no confirmation)
        fastapi_ddd migration-drop -d authentication    # Drop authentication domain only
        fastapi_ddd migration-drop -d authorization -y  # Drop authorization domain (no confirmation)
    """
    from sqlmodel import SQLModel, create_engine, text
    from fastapi_ddd.core.config import settings
    import importlib
    import inspect

    # Determine which domains to drop
    domains_to_drop = [domain] if domain else settings.installed_domains

    # Validate specific domain exists
    if domain and domain not in settings.installed_domains:
        console.print(
            f"[red]Error: Domain '{domain}' not found in installed domains[/red]"
        )
        console.print(f"Available domains: {', '.join(settings.installed_domains)}")
        raise typer.Exit(1)

    # Confirmation prompt
    if not confirm:
        if domain:
            confirmed = typer.confirm(
                f"⚠️  This will DROP ALL TABLES for domain '{domain}'. Continue?",
                abort=True,
            )
        else:
            confirmed = typer.confirm(
                "⚠️  This will DROP ALL TABLES in the database. Continue?", abort=True
            )
        if not confirmed:
            console.print("[yellow]Operation cancelled[/yellow]")
            return

    console.print("[cyan]Loading domain models...[/cyan]")
    domain_models = {}  # Store models per domain

    for dom in domains_to_drop:
        try:
            models_module = importlib.import_module(f"fastapi_ddd.domains.{dom}.models")

            # Get table names for this domain
            from sqlmodel import SQLModel as SM

            tables = []
            for name, obj in inspect.getmembers(models_module):
                if inspect.isclass(obj) and issubclass(obj, SM) and obj is not SM:
                    if hasattr(obj, "__tablename__"):
                        tables.append(obj.__tablename__)

            domain_models[dom] = tables
            console.print(f"  ✓ Loaded {dom} models: {', '.join(tables)}")
        except ImportError:
            console.print(f"  [yellow]⚠ Could not load {dom} models[/yellow]")

    db_url = database.get_db_url()
    engine = create_engine(db_url)

    if domain:
        # Drop specific domain tables
        console.print(f"\n[red]Dropping tables for domain '{domain}'...[/red]")

        with engine.begin() as conn:
            for table_name in domain_models.get(domain, []):
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {table_name} CASCADE"))
                    console.print(f"  ✓ Dropped table '{table_name}'")
                except Exception as e:
                    console.print(
                        f"  [yellow]⚠ Could not drop {table_name}: {e}[/yellow]"
                    )

            # Drop alembic version table for this domain
            version_table = f"alembic_version_{domain}"
            try:
                conn.execute(text(f"DROP TABLE IF EXISTS {version_table}"))
                console.print(f"  ✓ Dropped {version_table}")
            except Exception as e:
                console.print(
                    f"  [yellow]⚠ Could not drop {version_table}: {e}[/yellow]"
                )

        console.print(f"[green]✓ Domain '{domain}' tables dropped successfully[/green]")
        console.print(
            f"[yellow]Run 'fastapi_ddd migration-run -d {domain}' to recreate tables[/yellow]"
        )
    else:
        # Drop all tables
        console.print("\n[red]Dropping all tables...[/red]")

        SQLModel.metadata.drop_all(engine)
        console.print("  ✓ Domain tables dropped")

        # Drop alembic version tables for all domains
        with engine.begin() as conn:
            for dom in settings.installed_domains:
                version_table = f"alembic_version_{dom}"
                try:
                    conn.execute(text(f"DROP TABLE IF EXISTS {version_table}"))
                    console.print(f"  ✓ Dropped {version_table}")
                except Exception as e:
                    console.print(
                        f"  [yellow]⚠ Could not drop {version_table}: {e}[/yellow]"
                    )

        console.print("[green]✓ All tables dropped successfully[/green]")
        console.print(
            "[yellow]Run 'fastapi_ddd migration-run' to recreate tables[/yellow]"
        )


@cli.command()
def auth_jwt_secret():
    """Generate 256-bit JWT Secret for H256 signing"""
    secret_bytes = secrets.token_bytes(32)
    secret = base64.urlsafe_b64encode(secret_bytes).decode("utf-8")
    typer.echo(f"🔑 JWT HS256 Secret: (put this in your .env)\n{secret}")


@cli.command()
def migration_seed(
    domain: str = typer.Option(..., help="Domain name (e.g., authorization)"),
):
    """
    Run all seeder classes defined inside the seeders.py of a given domain.
    Automatically detects any class with a `seed(session)` coroutine method.
    """

    try:
        seeder_module = importlib.import_module(f"fastapi_ddd.domains.{domain}.seeders")
    except ModuleNotFoundError:
        console.print(f"[red]❌ Seeder module not found for domain '{domain}'[/red]")
        raise typer.Exit(1)

    seeders = []
    for _, cls in inspect.getmembers(seeder_module, inspect.isclass):
        if cls.__module__ == seeder_module.__name__:
            seed_method = getattr(cls, "seed", None)
            if seed_method and inspect.iscoroutinefunction(seed_method):
                seeders.append(cls)

    if not seeders:
        console.print(
            f"[yellow]⚠️ No valid seeder classes found in {domain}.seeders[/yellow]"
        )
        raise typer.Exit(1)

    async def _run():
        async with AsyncSession(engine, expire_on_commit=False) as session:
            try:
                async with session.begin():
                    for seeder_cls in seeders:
                        seeder = seeder_cls()
                        console.print(
                            f"[cyan]→ Running {seeder_cls.__name__}...[/cyan]"
                        )
                        await seeder.seed(session)
                console.print(
                    f"[green]✅ Seeding for domain '{domain}' completed[/green]"
                )
            except Exception as e:
                console.print(f"[red]❌ Seeder failed: {e}[/red]")
                raise

    asyncio.run(_run())


if __name__ == "__main__":
    cli()
