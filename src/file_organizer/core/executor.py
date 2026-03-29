"""File operations with rollback support."""

import logging
import shutil
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

logger = logging.getLogger(__name__)


@dataclass
class FileOperation:
    """A file operation with rollback capability."""

    source: Path
    destination: Path
    action: str  # "move", "copy"
    original_exists: bool = field(default=False, repr=False)
    backup_path: Path | None = field(default=None, repr=False)


class OperationExecutor:
    """Execute file operations with dry-run and rollback support."""

    def __init__(self, dry_run: bool = False, backup_conflicts: bool = True):
        self.dry_run = dry_run
        self.backup_conflicts = backup_conflicts
        self.operations: list[FileOperation] = []
        self.completed: list[FileOperation] = []
        self.failed: list[tuple[FileOperation, Exception]] = []

    def execute(
        self,
        source: Path,
        destination: Path,
        action: str = "move",
        progress_callback: Callable[[str, Path, Path], None] | None = None,
    ) -> bool:
        """
        Execute a file operation.

        Args:
            source: Source file path
            destination: Destination file path
            action: "move" or "copy"
            progress_callback: Optional callback(source, dest, status)

        Returns:
            True if successful
        """
        operation = FileOperation(
            source=source,
            destination=destination,
            action=action,
        )

        self.operations.append(operation)

        if self.dry_run:
            logger.info(f"[DRY RUN] Would {action} {source} -> {destination}")
            if progress_callback:
                progress_callback("dry_run", source, destination)
            return True

        try:
            # Ensure destination directory exists
            dest_dir = destination.parent
            dest_dir.mkdir(parents=True, exist_ok=True)

            # Handle conflicts
            if destination.exists():
                if self.backup_conflicts:
                    backup = self._create_backup(destination)
                    operation.backup_path = backup
                    operation.original_exists = True
                    logger.info(f"Backed up existing file to {backup}")

            # Execute operation
            if action == "move":
                shutil.move(str(source), str(destination))
            elif action == "copy":
                shutil.copy2(str(source), str(destination))
            else:
                raise ValueError(f"Unknown action: {action}")

            self.completed.append(operation)

            if progress_callback:
                progress_callback("completed", source, destination)

            logger.info(f"{action.capitalize()}d {source} -> {destination}")
            return True

        except Exception as e:
            self.failed.append((operation, e))
            logger.error(f"Failed to {action} {source}: {e}")
            if progress_callback:
                progress_callback("failed", source, destination)
            return False

    def _create_backup(self, file_path: Path) -> Path:
        """Create a backup of an existing file."""
        backup_dir = file_path.parent / ".file_organizer_backups"
        backup_dir.mkdir(exist_ok=True)

        timestamp = file_path.stat().st_mtime
        from datetime import datetime

        timestamp_str = datetime.fromtimestamp(timestamp).strftime("%Y%m%d_%H%M%S")
        backup_name = f"{file_path.stem}_{timestamp_str}{file_path.suffix}"
        backup_path = backup_dir / backup_name

        # Handle duplicate backup names
        counter = 1
        original_backup_path = backup_path
        while backup_path.exists():
            backup_path = original_backup_path.with_stem(
                f"{original_backup_path.stem}_{counter}"
            )
            counter += 1

        shutil.copy2(str(file_path), str(backup_path))
        return backup_path

    def rollback(self) -> list[tuple[FileOperation, bool]]:
        """
        Rollback all completed operations.

        Returns:
            List of (operation, success) tuples
        """
        results = []

        for operation in reversed(self.completed):
            success = self._rollback_single(operation)
            results.append((operation, success))

        return results

    def _rollback_single(self, operation: FileOperation) -> bool:
        """Rollback a single operation."""
        try:
            if operation.action == "move":
                # Move file back to source
                if operation.destination.exists():
                    shutil.move(str(operation.destination), str(operation.source))

                # Restore backup if there was a conflict
                if operation.backup_path and operation.backup_path.exists():
                    shutil.move(str(operation.backup_path), str(operation.destination))

            elif operation.action == "copy":
                # Remove copied file
                if operation.destination.exists():
                    operation.destination.unlink()

                # Restore backup
                if operation.backup_path and operation.backup_path.exists():
                    shutil.move(str(operation.backup_path), str(operation.destination))

            logger.info(f"Rolled back {operation.action} of {operation.source}")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback {operation.source}: {e}")
            return False

    def get_summary(self) -> dict[str, int | bool]:
        """Get a summary of operations."""
        return {
            "total": len(self.operations),
            "completed": len(self.completed),
            "failed": len(self.failed),
            "dry_run": self.dry_run,
        }
