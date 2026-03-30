"""Data models for configuration."""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional


@dataclass
class Source:
    """A source directory to scan for files."""

    path: Path
    recursive: bool = True
    include_patterns: list[str] = field(default_factory=list)
    exclude_patterns: list[str] = field(default_factory=list)

    def __post_init__(self) -> None:
        if not self.include_patterns:
            self.include_patterns = ["*"]


@dataclass
class Rule:
    """A rule for matching files."""

    type: str
    keywords: Optional[list[str]] = None
    extensions: Optional[list[str]] = None
    pattern: Optional[str] = None
    min_size: Optional[int] = None
    max_size: Optional[int] = None
    older_than_days: Optional[int] = None
    newer_than_days: Optional[int] = None
    # 0.6 default - lower threshold = more matches but less confidence
    threshold: Optional[float] = 0.6


@dataclass
class Destination:
    """A destination directory for organized files."""

    path: Path
    rules: list[Rule] = field(default_factory=list)
    create_if_missing: bool = True


@dataclass
class AIConfig:
    """AI-powered classification configuration.

    default model is qwen3:8b - good balance of speed and accuracy.
    """

    enabled: bool = True
    model: str = "qwen3:8b"
    categories: list[str] = field(default_factory=list)
    confidence_threshold: float = 0.7
    max_content_length: int = 2000
    cache_results: bool = True


@dataclass
class Options:
    """Global options for the organizer."""

    dry_run: bool = False
    backup_conflicts: bool = True
    log_level: str = "INFO"
    log_file: Optional[Path] = None
    # default max_workers=4 is good for most systems
    max_workers: int = 4


@dataclass
class Profile:
    """A complete organization profile."""

    name: str
    version: str
    sources: list[Source]
    destinations: list[Destination]
    ai: AIConfig
    options: Options
    description: Optional[str] = None

    def get_destination_for_category(self, category: str) -> Optional[Destination]:
        """Find destination by category name."""
        for dest in self.destinations:
            if dest.path.name.lower() == category.lower():
                return dest
        return None
