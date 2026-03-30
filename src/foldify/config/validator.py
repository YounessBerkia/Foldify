"""Configuration validation with lenient mode."""

import warnings
from pathlib import Path

from .models import AIConfig, Destination, Profile, Rule, Source


class ValidationError(Exception):
    """Raised when configuration validation fails."""

    pass


class ValidationWarning(UserWarning):
    """Warning for non-critical validation issues."""

    pass


def validate_path(
    path: Path, must_exist: bool = True, field_name: str = "path"
) -> None:
    """Validate a path exists and is accessible."""
    # TODO: add option to validate paths outside home directory
    if must_exist and not path.exists():
        raise ValidationError(f"{field_name} does not exist: {path}")
    if must_exist and not path.is_dir():
        raise ValidationError(f"{field_name} is not a directory: {path}")


def validate_rule(rule: Rule, index: int, destination_name: str) -> list[str]:
    """Validate a single rule. Returns list of warnings."""
    warnings_list = []

    valid_types = {
        "filename_contains",
        "extension",
        "content_contains",
        "size_range",
        "date_range",
        "regex",
        "ai_match",
    }

    if rule.type not in valid_types:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"Unknown rule type '{rule.type}'. Known types: {', '.join(valid_types)}"
        )

    # Type-specific validation
    if rule.type == "filename_contains" and not rule.keywords:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"'filename_contains' rule should have 'keywords'"
        )

    if rule.type == "extension" and not rule.extensions:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"'extension' rule should have 'extensions'"
        )

    if rule.type == "content_contains" and not rule.keywords:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"'content_contains' rule should have 'keywords'"
        )

    if rule.type == "size_range" and rule.min_size is None and rule.max_size is None:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"'size_range' rule should have 'min_size' or 'max_size'"
        )

    if rule.type == "regex" and not rule.pattern:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"'regex' rule should have 'pattern'"
        )

    if rule.threshold is not None and not 0.0 <= rule.threshold <= 1.0:
        warnings_list.append(
            f"Destination '{destination_name}', rule {index}: "
            f"'threshold' should be between 0.0 and 1.0"
        )

    return warnings_list


def validate_destination(destination: Destination, index: int) -> list[str]:
    """Validate a destination configuration. Returns list of warnings."""
    warnings_list = []
    dest_name = destination.path.name or f"destination_{index}"

    # Check if path is under home directory (security check)
    try:
        destination.path.relative_to(Path.home())
    except ValueError:
        warnings_list.append(
            f"Destination '{dest_name}': Path {destination.path} "
            "is outside home directory. "
            "This is allowed but may affect portability."
        )

    # Validate rules
    for i, rule in enumerate(destination.rules):
        rule_warnings = validate_rule(rule, i, dest_name)
        warnings_list.extend(rule_warnings)

    return warnings_list


def validate_source(source: Source, index: int) -> list[str]:
    """Validate a source configuration. Returns list of warnings."""
    warnings_list = []

    if not source.path.exists():
        raise ValidationError(f"Source {index}: Path does not exist: {source.path}")

    if not source.path.is_dir():
        raise ValidationError(f"Source {index}: Path is not a directory: {source.path}")

    # warn if include_patterns might be too broad without excludes
    if "*" in source.include_patterns and len(source.include_patterns) == 1:
        if not source.exclude_patterns:
            warnings_list.append(
                f"Source {index} ({source.path}): Using wildcard pattern '*' "
                "without exclude_patterns may process unexpected files."
            )

    return warnings_list


def validate_ai_config(ai_config: AIConfig) -> list[str]:
    """Validate AI configuration. Returns list of warnings."""
    warnings_list = []

    if ai_config.enabled:
        # Check if model name looks valid
        if not ai_config.model or "/" in ai_config.model or "\\" in ai_config.model:
            warnings_list.append(
                f"AI model name '{ai_config.model}' may be invalid. "
                "Expected format: 'modelname:size' (e.g., 'qwen3:8b')"
            )

        # Check confidence threshold
        if not 0.0 <= ai_config.confidence_threshold <= 1.0:
            raise ValidationError(
                f"AI confidence_threshold must be between 0.0 and 1.0, "
                f"got {ai_config.confidence_threshold}"
            )

    return warnings_list


def validate_profile(profile: Profile, strict: bool = False) -> list[str]:
    """
    Validate a complete profile.

    Args:
        profile: The profile to validate
        strict: If True, raise ValidationError for warnings.
            If False, return warnings list.

    Returns:
        List of warning messages (empty if no warnings)

    Raises:
        ValidationError: If critical validation fails or strict=True and warnings exist
    """
    all_warnings = []

    # TODO: consider making strict mode the default in v2.0

    # Validate sources
    if not profile.sources:
        raise ValidationError("Profile must have at least one source")

    for i, source in enumerate(profile.sources):
        source_warnings = validate_source(source, i)
        all_warnings.extend(source_warnings)

    # Validate destinations
    if not profile.destinations:
        raise ValidationError("Profile must have at least one destination")

    for i, dest in enumerate(profile.destinations):
        dest_warnings = validate_destination(dest, i)
        all_warnings.extend(dest_warnings)

    # Check for overlapping destinations (same path)
    dest_paths = [str(d.path.resolve()) for d in profile.destinations]
    if len(dest_paths) != len(set(dest_paths)):
        raise ValidationError("Multiple destinations point to the same path")

    # check if any destination is inside a source (risky - files could be re-processed)
    for dest in profile.destinations:
        for source in profile.sources:
            try:
                dest.path.relative_to(source.path)
                all_warnings.append(
                    f"Destination {dest.path} is inside source {source.path}. "
                    "This may cause files to be re-processed."
                )
            except ValueError:
                pass

    # Validate AI config
    ai_warnings = validate_ai_config(profile.ai)
    all_warnings.extend(ai_warnings)

    # In lenient mode, emit warnings instead of raising
    if not strict:
        for warning_msg in all_warnings:
            warnings.warn(warning_msg, ValidationWarning, stacklevel=2)
        return all_warnings

    # In strict mode, convert warnings to errors
    if all_warnings:
        raise ValidationError(
            f"Profile validation failed with {len(all_warnings)} issues:\n"
            + "\n".join(f"  - {w}" for w in all_warnings)
        )

    return []
