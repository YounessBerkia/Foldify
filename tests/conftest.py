"""Shared fixtures for tests."""

import tempfile
from pathlib import Path

import pytest

from foldify.config.models import (
    AIConfig,
    Destination,
    Options,
    Profile,
    Rule,
    Source,
)


@pytest.fixture
def temp_dir():
    """Provide a temporary directory."""
    # cleanup happens automatically when the context exits
    # pretty handy for avoiding test pollution
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def sample_source(temp_dir):
    """Create a sample source configuration."""
    source_dir = temp_dir / "source"
    source_dir.mkdir()
    return Source(path=source_dir, recursive=True)


@pytest.fixture
def sample_destination(temp_dir):
    """Create a sample destination configuration."""
    dest_dir = temp_dir / "destination"
    return Destination(path=dest_dir, rules=[], create_if_missing=True)


@pytest.fixture
def sample_rule():
    """Create a sample rule."""
    return Rule(type="filename_contains", keywords=["test", "example"])


@pytest.fixture
def sample_profile(temp_dir, sample_source, sample_destination):
    """Create a sample profile."""
    return Profile(
        name="test_profile",
        version="1.0",
        description="Test profile",
        sources=[sample_source],
        destinations=[sample_destination],
        ai=AIConfig(enabled=False),
        options=Options(dry_run=True),
    )


@pytest.fixture
def create_test_files(temp_dir):
    """Create test files for rule matching tests."""

    def _create_files(files_dict):
        """Create files from dictionary {path: content}."""
        # helper for setting up test files quickly
        # path_str is relative to temp_dir
        created = []
        for path_str, content in files_dict.items():
            file_path = temp_dir / path_str
            file_path.parent.mkdir(parents=True, exist_ok=True)
            file_path.write_text(content)
            created.append(file_path)
        return created

    return _create_files
