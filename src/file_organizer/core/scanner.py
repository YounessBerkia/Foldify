"""File discovery and scanning."""

from dataclasses import dataclass
from pathlib import Path

from ..config.models import Profile, Source
from ..rules.engine import RuleEngine


@dataclass
class FileInfo:
    """Information about a discovered file."""

    path: Path
    source: Source
    size: int
    modified_time: float


class FileScanner:
    """Scanner for discovering files in source directories."""

    def __init__(self, profile: Profile, rule_engine: RuleEngine):
        self.profile = profile
        self.rule_engine = rule_engine

    def scan_all(self) -> list[FileInfo]:
        """Scan all sources and return list of files to process."""
        files = []
        for source in self.profile.sources:
            files.extend(self._scan_source(source))
        return files

    def _scan_source(self, source: Source) -> list[FileInfo]:
        """Scan a single source directory."""
        files = []

        if not source.path.exists():
            raise FileNotFoundError(f"Source path does not exist: {source.path}")

        paths_to_scan = [source.path]

        while paths_to_scan:
            current_path = paths_to_scan.pop()

            try:
                for item in current_path.iterdir():
                    if item.is_dir():
                        if source.recursive:
                            paths_to_scan.append(item)
                    elif item.is_file():
                        if self.rule_engine.should_process_file(item, source):
                            try:
                                stat = item.stat()
                                files.append(
                                    FileInfo(
                                        path=item,
                                        source=source,
                                        size=stat.st_size,
                                        modified_time=stat.st_mtime,
                                    )
                                )
                            except (OSError, IOError):
                                continue
            except PermissionError:
                continue

        return files

    def scan_with_limit(self, limit: int | None = None) -> list[FileInfo]:
        """Scan sources with optional limit on number of files."""
        files = self.scan_all()
        if limit:
            return files[:limit]
        return files
