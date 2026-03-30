"""Integration tests for organizer workflow."""

import pytest

from foldify.config.models import (
    AIConfig,
    Destination,
    Options,
    Profile,
    Rule,
    Source,
)
from foldify.core.organizer import Organizer


class TestOrganizerWorkflow:
    """End-to-end tests for the organizer."""

    @pytest.fixture
    def setup(self, temp_dir):
        """Setup test environment."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        math_dir = temp_dir / "Math"
        pdf_dir = temp_dir / "PDFs"

        # Create test files
        (source_dir / "algebra_notes.txt").write_text("Algebra content")
        (source_dir / "calculus.pdf").write_text("PDF content")
        (source_dir / "history.docx").write_text("History content")

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir, recursive=False)],
            destinations=[
                Destination(
                    path=math_dir,
                    rules=[
                        Rule(
                            type="filename_contains",
                            keywords=["algebra", "calculus"],
                        ),
                    ],
                ),
                Destination(
                    path=pdf_dir,
                    rules=[Rule(type="extension", extensions=[".pdf"])],
                ),
            ],
            ai=AIConfig(enabled=False),
            options=Options(dry_run=False),
        )

        organizer = Organizer(profile)
        return organizer, source_dir, math_dir, pdf_dir

    def test_organize_dry_run(self, setup):
        """Test dry run doesn't move files."""
        organizer, source_dir, math_dir, pdf_dir = setup

        result = organizer.organize(dry_run=True)

        # Files should still be in source
        assert (source_dir / "algebra_notes.txt").exists()
        assert (source_dir / "calculus.pdf").exists()

        # Nothing in destinations
        assert not math_dir.exists() or not any(math_dir.iterdir())
        assert not pdf_dir.exists() or not any(pdf_dir.iterdir())

        # Result should show what would happen
        assert result.files_scanned > 0
        assert result.dry_run is True

    def test_organize_real_run(self, setup):
        """Test actual file organization."""
        organizer, source_dir, math_dir, pdf_dir = setup

        result = organizer.organize(dry_run=False)

        # Should have moved files
        assert result.files_moved > 0
        assert result.files_failed == 0

    def test_preview_mode(self, setup):
        """Test preview functionality."""
        organizer, source_dir, math_dir, pdf_dir = setup

        preview = organizer.preview(limit=10)

        # Should show planned moves
        assert len(preview) > 0

        # Source files should still exist
        assert (source_dir / "algebra_notes.txt").exists()

    def test_unmatched_files_ignored(self, setup):
        """Test files not matching any rule are ignored."""
        organizer, source_dir, math_dir, pdf_dir = setup

        # Add a file that won't match any rule
        (source_dir / "random.xyz").write_text("random content")

        result = organizer.organize(dry_run=True)

        # history.docx and random.xyz shouldn't match
        assert result.files_matched == 2  # Only algebra and calculus


class TestOrganizerWithOptions:
    """Test organizer with various options."""

    def test_organize_with_limit(self, temp_dir):
        """Test organizing with file limit."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        # Create many files
        for i in range(10):
            (source_dir / f"file{i}.txt").write_text(f"content {i}")

        dest_dir = temp_dir / "dest"

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[
                Destination(
                    path=dest_dir,
                    rules=[Rule(type="extension", extensions=[".txt"])],
                )
            ],
            ai=AIConfig(enabled=False),
            options=Options(dry_run=False),
        )

        organizer = Organizer(profile)
        result = organizer.organize(limit=3, dry_run=False)

        # Should only process 3 files
        assert result.files_moved <= 3
