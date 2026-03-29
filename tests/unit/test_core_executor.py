"""Tests for core executor."""

from file_organizer.core.executor import OperationExecutor


class TestOperationExecutor:
    """Tests for OperationExecutor."""

    def test_dry_run_no_changes(self, temp_dir):
        """Dry run should not modify files."""
        source = temp_dir / "source.txt"
        source.write_text("test content")

        dest = temp_dir / "dest.txt"

        executor = OperationExecutor(dry_run=True)
        result = executor.execute(source, dest, action="move")

        assert result is True
        assert source.exists()  # Source should still exist
        assert not dest.exists()  # Dest should not exist

    def test_move_file(self, temp_dir):
        """Test moving a file."""
        source = temp_dir / "source.txt"
        source.write_text("test content")

        dest_dir = temp_dir / "destination"
        dest = dest_dir / "moved.txt"

        executor = OperationExecutor(dry_run=False)
        result = executor.execute(source, dest, action="move")

        assert result is True
        assert not source.exists()  # Source should be gone
        assert dest.exists()  # Dest should exist
        assert dest.read_text() == "test content"

    def test_copy_file(self, temp_dir):
        """Test copying a file."""
        source = temp_dir / "source.txt"
        source.write_text("test content")

        dest_dir = temp_dir / "destination"
        dest = dest_dir / "copied.txt"

        executor = OperationExecutor(dry_run=False)
        result = executor.execute(source, dest, action="copy")

        assert result is True
        assert source.exists()  # Source should still exist
        assert dest.exists()  # Dest should exist
        assert source.read_text() == dest.read_text()

    def test_backup_on_conflict(self, temp_dir):
        """Test backup creation when destination exists."""
        source = temp_dir / "source.txt"
        source.write_text("new content")

        dest_dir = temp_dir / "destination"
        dest = dest_dir / "file.txt"
        dest_dir.mkdir()
        dest.write_text("existing content")

        executor = OperationExecutor(dry_run=False, backup_conflicts=True)
        result = executor.execute(source, dest, action="move")

        assert result is True
        assert dest.exists()
        assert dest.read_text() == "new content"

        # Check backup was created
        backup_dir = dest_dir / ".file_organizer_backups"
        assert backup_dir.exists()
        backups = list(backup_dir.glob("*"))
        assert len(backups) == 1

    def test_rollback(self, temp_dir):
        """Test rollback functionality."""
        source = temp_dir / "source.txt"
        source.write_text("original content")

        dest_dir = temp_dir / "destination"
        dest = dest_dir / "moved.txt"

        executor = OperationExecutor(dry_run=False)
        executor.execute(source, dest, action="move")

        # Verify move happened
        assert not source.exists()
        assert dest.exists()

        # Rollback
        results = executor.rollback()

        assert len(results) == 1
        assert results[0][1] is True  # Success

        # After rollback
        assert source.exists()
        assert not dest.exists()

    def test_get_summary(self, temp_dir):
        """Test operation summary."""
        source = temp_dir / "source.txt"
        source.write_text("content")

        dest = temp_dir / "dest.txt"

        executor = OperationExecutor(dry_run=False)
        executor.execute(source, dest, action="move")

        summary = executor.get_summary()
        assert summary["total"] == 1
        assert summary["completed"] == 1
        assert summary["failed"] == 0
        assert summary["dry_run"] is False

    def test_failed_operation(self, temp_dir):
        """Test handling of failed operations."""
        source = temp_dir / "source.txt"
        # Don't create the file - should fail

        dest = temp_dir / "dest.txt"

        executor = OperationExecutor(dry_run=False)
        result = executor.execute(source, dest, action="move")

        assert result is False
        assert len(executor.failed) == 1
