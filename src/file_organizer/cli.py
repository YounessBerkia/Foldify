"""CLI entry point for file-organizer."""

import sys
import warnings
from collections import Counter
from pathlib import Path
from typing import Optional

import click

from . import __version__
from .config import (
    ValidationError,
    ensure_config_dirs,
    get_profiles_dir,
    list_profiles,
    load_profile_by_name,
    validate_profile,
)
from .core import FileInfo, OrganizationResult, Organizer
from .utils import confirm_prompt, setup_logging, truncate_string

# Template definitions
TEMPLATES = {
    "school": {
        "description": (
            "Organize school files by subject " "(Math, Physics, History, etc.)"
        ),
        "file": "school.yaml.example",
    },
    "work": {
        "description": "Organize work documents (Reports, Invoices, Contracts)",
        "file": "work.yaml.example",
    },
    "desktop-cleanup": {
        "description": "Clean up Downloads/Desktop (old files, screenshots, archives)",
        "file": "desktop-cleanup.yaml.example",
    },
    "ai-smart": {
        "description": "AI-powered classification using Ollama",
        "file": "ai-smart.yaml.example",
    },
}


def get_examples_dir() -> Path:
    """Get the examples directory."""
    # When installed, examples are in package data
    # When developing, they're in the repo
    cli_file = Path(__file__).resolve()
    package_root = cli_file.parent.parent.parent
    examples_dir = package_root / "examples"

    # Fallback to looking in common locations
    if not examples_dir.exists():
        # Try relative to installed package
        import importlib.util

        spec = importlib.util.find_spec("file_organizer")
        if spec and spec.origin:
            package_root = Path(spec.origin).parent.parent
            examples_dir = package_root / "examples"

    return examples_dir


@click.group()
@click.version_option(version=__version__, prog_name="file-organizer")
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    help="Enable verbose output",
)
def cli(verbose: bool) -> None:
    """File Organizer - Intelligent file organization with AI-powered classification."""
    ensure_config_dirs()
    log_level = "DEBUG" if verbose else "WARNING"
    setup_logging(log_level)


@cli.command()
@click.option(
    "--profile",
    "-p",
    required=True,
    help="Profile name to use",
)
@click.option(
    "--dry-run",
    "-d",
    is_flag=True,
    help="Preview changes without executing",
)
@click.option(
    "--limit",
    "-l",
    type=int,
    help="Limit number of files to process",
)
def run(profile: str, dry_run: bool, limit: int | None) -> None:
    """Run file organization with a profile."""
    try:
        config = load_profile_by_name(profile)
    except FileNotFoundError as e:
        click.echo(f"Error: {e}", err=True)
        click.echo(
            f"\nCreate a profile at: {get_profiles_dir() / f'{profile}.yaml'}",
            err=True,
        )
        sys.exit(1)

    # Validate profile
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            validation_warnings = validate_profile(config)
    except ValidationError as e:
        click.echo(f"Validation error: {e}", err=True)
        sys.exit(1)

    _print_validation_warnings(validation_warnings)

    # Override dry_run from CLI
    if dry_run:
        config.options.dry_run = True

    if config.ai.enabled:
        click.secho("Checking Ollama connection...", fg="cyan")

    organizer = Organizer(config, status_callback=_status_update)

    if config.ai.enabled:
        if organizer.rule_engine.ai_client:
            click.secho("Connected to Ollama.", fg="green")
        else:
            click.secho(
                "Ollama is not available. AI matching will be skipped.",
                fg="yellow",
            )

    # Preview mode
    if config.options.dry_run:
        click.secho("\n=== Dry Run Preview ===", bold=True)
        click.echo("No files will be moved.")
        click.secho("Scanning files and preparing suggestions...\n", fg="cyan")

        preview = organizer.preview(
            limit=limit or 20,
            progress_callback=_preview_update,
        )
        if not preview:
            click.secho("No files would be moved.", fg="yellow")
            return

        click.secho(f"\nPlanned moves: {len(preview)}\n", fg="green", bold=True)
        for index, (src, dest, match) in enumerate(preview, start=1):
            click.secho(
                f"{index}. {truncate_string(src.name, 60)}",
                bold=True,
            )
            click.echo(f"   Destination: {dest.parent.name}")
            click.echo(f"   Final name: {dest.name}")
            click.echo(f"   Reason: {match.reason}\n")

        if limit is None or len(preview) == limit:
            click.echo(f"Showing {len(preview)} planned result(s).\n")

        if confirm_prompt("Execute these moves?", default=False):
            # Re-run without dry_run
            config.options.dry_run = False
            organizer = Organizer(config, status_callback=_status_update)
            result = organizer.organize(dry_run=False)
            _print_result(result)
    else:
        # Normal execution
        if not confirm_prompt(
            f"This will organize files using profile '{profile}'. Continue?",
            default=False,
        ):
            click.echo("Aborted.")
            sys.exit(0)

        click.secho("Running organizer...\n", fg="cyan")
        result = organizer.organize(dry_run=False, limit=limit)
        _print_result(result)


def _print_result(result: OrganizationResult) -> None:
    """Print organization result."""
    click.secho("\n=== Organization Complete ===", bold=True)
    click.echo(f"Files scanned: {result.files_scanned}")
    click.echo(f"Files matched: {result.files_matched}")
    click.echo(f"Files moved: {result.files_moved}")
    click.echo(f"Files failed: {result.files_failed}")

    if result.files_failed > 0:
        sys.exit(1)


def _print_validation_warnings(warnings_list: list[str]) -> None:
    """Print validation warnings in a compact, user-friendly way."""
    if not warnings_list:
        return

    inside_source_count = sum(
        "is inside source" in warning for warning in warnings_list
    )
    other_warnings = [
        warning for warning in warnings_list if "is inside source" not in warning
    ]

    click.secho("Profile warnings:", fg="yellow", bold=True)
    if inside_source_count:
        click.echo(
            "  - Some destinations are inside a source directory. "
            "Those files could be picked up again in later runs."
        )

    for warning, count in Counter(other_warnings).items():
        prefix = f"  - ({count}x) " if count > 1 else "  - "
        click.echo(f"{prefix}{warning}")

    click.echo("")


def _status_update(status: str, file_path: Path) -> None:
    """Render AI status updates for the terminal UI."""
    if status == "ai_started":
        click.secho(
            f"Consulting Ollama for: {truncate_string(file_path.name, 60)}",
            fg="cyan",
        )


def _preview_update(file_info: FileInfo, status: str) -> None:
    """Render lightweight preview progress updates."""
    if status == "matching":
        click.echo(f"Reviewing {truncate_string(file_info.path.name, 60)}...")


def copy_template(template_name: str, profile_name: str) -> Optional[Path]:
    """Copy a template to the profiles directory."""
    examples_dir = get_examples_dir()
    template_info = TEMPLATES.get(template_name)

    if not template_info:
        return None

    source_file = examples_dir / template_info["file"]
    if not source_file.exists():
        return None

    profiles_dir = get_profiles_dir()
    profiles_dir.mkdir(parents=True, exist_ok=True)

    dest_file = profiles_dir / f"{profile_name}.yaml"

    # Don't overwrite existing profiles
    if dest_file.exists():
        raise FileExistsError(f"Profile already exists: {dest_file}")

    # Read template and update name
    content = source_file.read_text()
    # Replace the name field
    lines = content.split("\n")
    for i, line in enumerate(lines):
        if line.startswith("name:"):
            lines[i] = f"name: {profile_name}"
            break
    content = "\n".join(lines)

    dest_file.write_text(content)
    return dest_file


@cli.command()
@click.option(
    "--profile",
    "-p",
    help="Profile name to create",
)
@click.option(
    "--template",
    "-t",
    type=click.Choice(list(TEMPLATES.keys())),
    help="Template to use",
)
@click.option(
    "--list-templates",
    is_flag=True,
    help="List available templates",
)
def init(profile: Optional[str], template: Optional[str], list_templates: bool) -> None:
    """Initialize configuration directories and create profiles from templates."""
    ensure_config_dirs()

    if list_templates:
        click.echo("Available templates:")
        for name, info in TEMPLATES.items():
            click.echo(f"  {name:15} - {info['description']}")
        click.echo("\nUse: file-organizer init --template <name> --profile <name>")
        return

    if template and profile:
        # Copy template to profile
        try:
            dest = copy_template(template, profile)
            if dest:
                click.echo(f"Created profile '{profile}' from template '{template}'")
                click.echo(f"Profile location: {dest}")
                click.echo("\nEdit the profile to customize paths, then run:")
                click.echo(f"  file-organizer run --profile {profile} --dry-run")
            else:
                click.echo(f"Error: Template file not found for '{template}'", err=True)
                sys.exit(1)
        except FileExistsError as e:
            click.echo(f"Error: {e}", err=True)
            click.echo("Choose a different profile name or delete the existing one.")
            sys.exit(1)
    elif template or profile:
        click.echo("Error: Both --template and --profile are required.", err=True)
        click.echo("\nExamples:")
        click.echo("  file-organizer init --template school --profile school")
        click.echo("  file-organizer init --template work --profile mywork")
        click.echo("  file-organizer init --list-templates")
        sys.exit(1)
    else:
        # Just initialize directories
        click.echo("Configuration directories created.")
        click.echo(f"Profiles directory: {get_profiles_dir()}")
        click.echo("\nTo create a profile from a template:")
        click.echo("  file-organizer init --list-templates")
        click.echo("  file-organizer init --template school --profile school")


@cli.command(name="list")
def list_cmd() -> None:
    """List available profiles."""
    profiles = list_profiles()
    if not profiles:
        click.echo("No profiles found.")
        click.echo(f"Create profiles in: {get_profiles_dir()}")
        return

    click.echo("Available profiles:")
    for profile in profiles:
        click.echo(f"  - {profile}")


@cli.command()
@click.argument("profile_name")
def validate(profile_name: str) -> None:
    """Validate a profile configuration."""
    try:
        config = load_profile_by_name(profile_name)
        warnings = validate_profile(config)
        click.echo(f"Profile '{profile_name}' is valid.")
        if warnings:
            click.echo(f"Warnings: {len(warnings)}")
    except (FileNotFoundError, ValidationError) as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


@cli.group()
def ai() -> None:
    """AI-related commands."""
    pass


@ai.command(name="status")
def ai_status() -> None:
    """Check AI (Ollama) status."""
    from .ai import check_ollama_status

    status = check_ollama_status()
    models = status.get("models")

    click.echo("AI Status:")
    click.echo(f"  Installed: {'Yes' if status['installed'] else 'No'}")
    click.echo(f"  Running: {'Yes' if status['running'] else 'No'}")

    if isinstance(models, list):
        click.echo(f"  Available models: {', '.join(str(model) for model in models)}")
    elif status["running"]:
        click.echo("  Available models: (none)")

    if "error" in status:
        click.echo(f"  Error: {status['error']}", err=True)


@ai.command(name="setup")
def ai_setup() -> None:
    """Setup AI configuration."""
    click.echo("AI Setup")
    click.echo("========")
    click.echo("\n1. Install Ollama from: https://ollama.ai")
    click.echo("2. Pull a recommended model:")
    click.echo("   ollama pull qwen3:8b    # Recommended (~5.5GB)")
    click.echo("   ollama pull phi4:mini   # Fast option (~4GB)")
    click.echo("\n3. Test with: file-organizer ai status")


def main() -> None:
    """Main entry point."""
    cli()


if __name__ == "__main__":
    main()
