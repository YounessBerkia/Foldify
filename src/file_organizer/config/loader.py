"""Configuration loading from YAML files."""

import os
import warnings
from pathlib import Path
from typing import Any

import yaml

from .models import AIConfig, Destination, Options, Profile, Rule, Source

ConfigDict = dict[str, Any]


def get_config_dir() -> Path:
    """Get the configuration directory."""
    config_dir = Path.home() / ".config" / "file-organizer"
    return config_dir


def get_profiles_dir() -> Path:
    """Get the profiles directory."""
    return get_config_dir() / "profiles"


def get_cache_dir() -> Path:
    """Get the cache directory for AI results."""
    cache_dir = Path.home() / ".cache" / "file-organizer"
    cache_dir.mkdir(parents=True, exist_ok=True)
    return cache_dir


def ensure_config_dirs() -> None:
    """Create configuration directories if they don't exist."""
    config_dir = get_config_dir()
    profiles_dir = get_profiles_dir()
    cache_dir = get_cache_dir()

    config_dir.mkdir(parents=True, exist_ok=True)
    profiles_dir.mkdir(parents=True, exist_ok=True)
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Create default logs directory
    log_dir = Path.home() / ".local" / "share" / "file-organizer"
    log_dir.mkdir(parents=True, exist_ok=True)


def expand_path(path: str) -> Path:
    """Expand a path string, handling ~ and environment variables."""
    expanded = os.path.expanduser(os.path.expandvars(path))
    return Path(expanded).resolve()


def load_rule(rule_data: ConfigDict) -> Rule:
    """Load a rule from dictionary data."""
    return Rule(
        type=rule_data.get("type", "filename_contains"),
        keywords=rule_data.get("keywords"),
        extensions=rule_data.get("extensions"),
        pattern=rule_data.get("pattern"),
        min_size=rule_data.get("min_size"),
        max_size=rule_data.get("max_size"),
        older_than_days=rule_data.get("older_than_days"),
        newer_than_days=rule_data.get("newer_than_days"),
        threshold=rule_data.get("threshold"),
    )


def load_source(source_data: ConfigDict) -> Source:
    """Load a source from dictionary data."""
    path = expand_path(source_data.get("path", "~"))
    return Source(
        path=path,
        recursive=source_data.get("recursive", True),
        include_patterns=source_data.get("include_patterns", ["*"]),
        exclude_patterns=source_data.get("exclude_patterns", []),
    )


def load_destination(name: str, dest_data: ConfigDict) -> Destination:
    """Load a destination from dictionary data."""
    path = expand_path(dest_data.get("path", "~"))
    rules = [load_rule(rule) for rule in dest_data.get("rules", [])]

    return Destination(
        path=path,
        rules=rules,
        create_if_missing=dest_data.get("create_if_missing", True),
    )


def load_ai_config(ai_data: ConfigDict | None) -> AIConfig:
    """Load AI configuration from dictionary data."""
    if not ai_data:
        return AIConfig()

    return AIConfig(
        enabled=ai_data.get("enabled", True),
        model=ai_data.get("model", "qwen3:8b"),
        categories=ai_data.get("categories", []),
        confidence_threshold=ai_data.get("confidence_threshold", 0.7),
        max_content_length=ai_data.get("max_content_length", 2000),
        cache_results=ai_data.get("cache_results", True),
    )


def load_options(options_data: ConfigDict | None) -> Options:
    """Load global options from dictionary data."""
    if not options_data:
        return Options()

    log_file = options_data.get("log_file")
    if log_file:
        log_file = expand_path(log_file)

    return Options(
        dry_run=options_data.get("dry_run", False),
        backup_conflicts=options_data.get("backup_conflicts", True),
        log_level=options_data.get("log_level", "INFO"),
        log_file=log_file,
        max_workers=options_data.get("max_workers", 4),
    )


def load_profile(profile_path: Path) -> Profile:
    """Load a profile from a YAML file."""
    if not profile_path.exists():
        raise FileNotFoundError(f"Profile not found: {profile_path}")

    with open(profile_path, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, dict):
        raise ValueError(f"Invalid profile format in {profile_path}")

    typed_data: ConfigDict = data

    # Check for unknown top-level fields (lenient mode - warn only)
    known_fields = {
        "name",
        "version",
        "description",
        "sources",
        "destinations",
        "ai",
        "options",
    }
    unknown_fields = set(typed_data.keys()) - known_fields
    if unknown_fields:
        warnings.warn(
            (
                f"Unknown fields in profile {profile_path.name}: "
                f"{', '.join(unknown_fields)}"
            ),
            UserWarning,
            stacklevel=2,
        )

    # Load sources
    sources_data = typed_data.get("sources", [])
    if not sources_data:
        raise ValueError(f"Profile {profile_path.name} must have at least one source")
    sources = [load_source(src) for src in sources_data]

    # Load destinations
    destinations_data = typed_data.get("destinations", {})
    if not destinations_data:
        raise ValueError(
            f"Profile {profile_path.name} must have at least one destination"
        )

    destinations = []
    for name, dest_data in destinations_data.items():
        if isinstance(dest_data, dict):
            destinations.append(load_destination(name, dest_data))

    if not destinations:
        raise ValueError(f"Profile {profile_path.name} has no valid destinations")

    return Profile(
        name=typed_data.get("name", profile_path.stem),
        version=typed_data.get("version", "1.0"),
        description=typed_data.get("description"),
        sources=sources,
        destinations=destinations,
        ai=load_ai_config(typed_data.get("ai")),
        options=load_options(typed_data.get("options")),
    )


def load_profile_by_name(name: str) -> Profile:
    """Load a profile by name from the profiles directory."""
    profiles_dir = get_profiles_dir()
    profile_path = profiles_dir / f"{name}.yaml"

    if not profile_path.exists():
        # Try with .yml extension
        profile_path = profiles_dir / f"{name}.yml"
        if not profile_path.exists():
            raise FileNotFoundError(
                f"Profile '{name}' not found. "
                f"Create it at: {profiles_dir / name}.yaml"
            )

    return load_profile(profile_path)


def list_profiles() -> list[str]:
    """List all available profiles."""
    profiles_dir = get_profiles_dir()
    if not profiles_dir.exists():
        return []

    profiles = []
    for ext in ["*.yaml", "*.yml"]:
        profiles.extend([p.stem for p in profiles_dir.glob(ext)])

    return sorted(profiles)
