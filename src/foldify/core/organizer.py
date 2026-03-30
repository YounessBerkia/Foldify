"""Main organizer orchestration."""

import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from ..ai.client import AIClient
from ..config.loader import get_cache_dir
from ..config.models import Destination, Profile
from ..rules.engine import RuleEngine, RuleMatchResult
from .executor import FileOperation, OperationExecutor
from .scanner import FileInfo, FileScanner

logger = logging.getLogger(__name__)


@dataclass
class OrganizationResult:
    """Result of an organization run."""

    files_scanned: int
    files_matched: int
    files_moved: int
    files_failed: int
    dry_run: bool
    operations: list[FileOperation] = field(default_factory=list)


class Organizer:
    """Main orchestrator that coordinates scanning, matching, and file operations."""

    def __init__(
        self,
        profile: Profile,
        use_ai: bool = True,
        status_callback: Callable[[str, Path], None] | None = None,
    ):
        self.profile = profile
        self.status_callback = status_callback

        # Initialize AI client if enabled
        ai_client = None
        if use_ai and profile.ai.enabled:
            cache_dir = get_cache_dir() if profile.ai.cache_results else None
            ai_client = AIClient(profile.ai, cache_dir=cache_dir)
            if not ai_client.is_available():
                logger.warning(
                    "AI is enabled but Ollama is not available. "
                    "AI matching disabled."
                )
                ai_client = None

        self.rule_engine = RuleEngine(
            profile,
            ai_client=ai_client,
            status_callback=status_callback,
        )
        self.scanner = FileScanner(profile, self.rule_engine)

    def organize(
        self,
        dry_run: bool = False,
        limit: int | None = None,
        progress_callback: Callable[[FileInfo, str], None] | None = None,
    ) -> OrganizationResult:
        """
        Run the organization process.

        Args:
            dry_run: If True, only simulate operations
            limit: Optional limit on number of files to process
            progress_callback: Optional callback(file_info, status)

        Returns:
            OrganizationResult with statistics
        """
        # Use profile options if not overridden
        if dry_run is None:
            dry_run = self.profile.options.dry_run

        executor = OperationExecutor(
            dry_run=dry_run,
            backup_conflicts=self.profile.options.backup_conflicts,
        )

        # Scan for files - this is where we discover what to organize
        logger.info("Scanning source directories...")
        files = self.scanner.scan_with_limit(limit)
        logger.info(f"Found {len(files)} files to process")

        result = OrganizationResult(
            files_scanned=len(files),
            files_matched=0,
            files_moved=0,
            files_failed=0,
            dry_run=dry_run,
        )

        # Process each file
        for file_info in files:
            match_result = self.rule_engine.match_file(file_info.path)

            if match_result.matched and match_result.destination:
                result.files_matched += 1

                # Determine destination path
                dest_path = self._compute_destination_path(
                    file_info.path, match_result.destination
                )

                # Execute operation
                success = executor.execute(
                    source=file_info.path,
                    destination=dest_path,
                    action="move",
                    progress_callback=None,
                )

                if success:
                    result.files_moved += 1
                else:
                    result.files_failed += 1

                if progress_callback:
                    progress_callback(file_info, "processed" if success else "failed")
            else:
                logger.debug(f"No match for {file_info.path}")
                if progress_callback:
                    progress_callback(file_info, "skipped")

        result.operations = executor.completed
        return result

    def _compute_destination_path(
        self, source_path: Path, destination: Destination
    ) -> Path:
        """Compute the final destination path for a file.

        TODO: add support for renaming files during organization
        """
        return destination.path / source_path.name

    def preview(
        self,
        limit: int = 10,
        progress_callback: Callable[[FileInfo, str], None] | None = None,
    ) -> list[tuple[Path, Path, RuleMatchResult]]:
        """
        Preview what would happen without executing.

        Returns:
            List of (source_path, destination_path, match_result) tuples
        """
        files = self.scanner.scan_with_limit(limit)
        preview_list = []

        for file_info in files:
            if progress_callback:
                progress_callback(file_info, "matching")
            match_result = self.rule_engine.match_file(file_info.path)
            if match_result.matched and match_result.destination:
                dest_path = self._compute_destination_path(
                    file_info.path, match_result.destination
                )
                preview_list.append((file_info.path, dest_path, match_result))
                if progress_callback:
                    progress_callback(file_info, "matched")
            elif progress_callback:
                progress_callback(file_info, "skipped")

        return preview_list
