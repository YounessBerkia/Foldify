"""Tests for file scanner."""

import pytest

from foldify.config.models import AIConfig, Destination, Options, Profile, Source
from foldify.core.scanner import FileScanner
from foldify.rules.engine import RuleEngine


class TestFileScanner:
    """Tests for FileScanner."""

    @pytest.fixture
    def setup(self, temp_dir):
        """Setup test directories."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        # Create some test files
        (source_dir / "file1.txt").write_text("content1")
        (source_dir / "file2.pdf").write_text("content2")

        subdir = source_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("content3")

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[Destination(path=temp_dir / "dest")],
            ai=AIConfig(enabled=False),
            options=Options(),
        )

        engine = RuleEngine(profile)
        scanner = FileScanner(profile, engine)

        return scanner, source_dir

    def test_scan_all_files(self, setup):
        """Test scanning all files recursively."""
        scanner, source_dir = setup

        files = scanner.scan_all()

        assert len(files) == 3
        filenames = [f.path.name for f in files]
        assert "file1.txt" in filenames
        assert "file2.pdf" in filenames
        assert "file3.txt" in filenames

    def test_scan_non_recursive(self, setup, temp_dir):
        """Test non-recursive scanning."""
        scanner, source_dir = setup

        # Modify source to be non-recursive
        scanner.profile.sources[0].recursive = False

        files = scanner.scan_all()

        assert len(files) == 2  # Only top-level files
        filenames = [f.path.name for f in files]
        assert "file3.txt" not in filenames  # Subdir file excluded

    def test_scan_with_limit(self, setup):
        """Test scanning with limit."""
        scanner, source_dir = setup

        files = scanner.scan_with_limit(limit=2)

        assert len(files) == 2

    def test_scan_source_not_exist(self, temp_dir):
        """Test scanning non-existent source."""
        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=temp_dir / "nonexistent")],
            destinations=[Destination(path=temp_dir / "dest")],
            ai=AIConfig(enabled=False),
            options=Options(),
        )

        engine = RuleEngine(profile)
        scanner = FileScanner(profile, engine)

        with pytest.raises(FileNotFoundError):
            scanner.scan_all()

    def test_file_info_attributes(self, setup):
        """Test FileInfo has correct attributes."""
        scanner, source_dir = setup

        files = scanner.scan_all()
        assert len(files) > 0

        file_info = files[0]
        assert file_info.path.exists()
        assert file_info.size >= 0
        assert file_info.modified_time > 0
        assert file_info.source.path == source_dir
