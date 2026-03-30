"""Tests for configuration loading."""

from pathlib import Path

import pytest
import yaml

from foldify.config.loader import (
    expand_path,
    load_ai_config,
    load_destination,
    load_options,
    load_profile,
    load_rule,
    load_source,
)
from foldify.config.models import AIConfig, Destination, Options, Source


class TestPathExpansion:
    """Tests for path expansion functions."""

    def test_expand_home(self):
        """Test expanding ~ to home directory."""
        result = expand_path("~/Documents")
        assert result == Path.home() / "Documents"

    def test_expand_env_var(self, monkeypatch):
        """Test expanding environment variables."""
        monkeypatch.setenv("TEST_DIR", "/tmp/test")
        result = expand_path("$TEST_DIR/files")
        assert result == Path("/tmp/test/files").resolve()

    def test_expand_absolute(self):
        """Test absolute path is preserved."""
        result = expand_path("/usr/local/bin")
        assert result == Path("/usr/local/bin").resolve()


class TestLoadRule:
    """Tests for load_rule function."""

    def test_load_filename_contains_rule(self):
        """Load filename_contains rule."""
        data = {"type": "filename_contains", "keywords": ["math", "algebra"]}
        rule = load_rule(data)
        assert rule.type == "filename_contains"
        assert rule.keywords == ["math", "algebra"]

    def test_load_extension_rule(self):
        """Load extension rule."""
        data = {"type": "extension", "extensions": [".pdf", ".docx"]}
        rule = load_rule(data)
        assert rule.type == "extension"
        assert rule.extensions == [".pdf", ".docx"]

    def test_load_rule_defaults(self):
        """Load rule with defaults."""
        data = {}
        rule = load_rule(data)
        assert rule.type == "filename_contains"

    def test_load_rule_threshold(self):
        """Load rule threshold."""
        data = {"type": "ai_match", "threshold": 0.85}
        rule = load_rule(data)
        assert rule.type == "ai_match"
        assert rule.threshold == 0.85


class TestLoadSource:
    """Tests for load_source function."""

    def test_load_source_defaults(self, temp_dir):
        """Load source with defaults."""
        data = {"path": str(temp_dir)}
        source = load_source(data)
        assert isinstance(source, Source)
        assert source.path == temp_dir.resolve()
        assert source.recursive is True
        assert source.include_patterns == ["*"]

    def test_load_source_custom(self, temp_dir):
        """Load source with custom values."""
        data = {
            "path": str(temp_dir),
            "recursive": False,
            "include_patterns": ["*.pdf"],
            "exclude_patterns": [".DS_Store"],
        }
        source = load_source(data)
        assert source.recursive is False
        assert source.include_patterns == ["*.pdf"]
        assert source.exclude_patterns == [".DS_Store"]


class TestLoadDestination:
    """Tests for load_destination function."""

    def test_load_destination_no_rules(self, temp_dir):
        """Load destination without rules."""
        data = {"path": str(temp_dir)}
        dest = load_destination("test", data)
        assert isinstance(dest, Destination)
        assert dest.path == temp_dir.resolve()
        assert dest.rules == []

    def test_load_destination_with_rules(self, temp_dir):
        """Load destination with rules."""
        data = {
            "path": str(temp_dir),
            "rules": [{"type": "extension", "extensions": [".pdf"]}],
        }
        dest = load_destination("pdf_files", data)
        assert len(dest.rules) == 1
        assert dest.rules[0].type == "extension"


class TestLoadAIConfig:
    """Tests for load_ai_config function."""

    def test_load_ai_config_none(self):
        """Load AI config with None (defaults)."""
        config = load_ai_config(None)
        assert isinstance(config, AIConfig)
        assert config.enabled is True
        assert config.model == "qwen3:8b"

    def test_load_ai_config_custom(self):
        """Load custom AI config."""
        data = {
            "enabled": False,
            "model": "phi4:mini",
            "categories": ["A", "B"],
            "confidence_threshold": 0.8,
        }
        config = load_ai_config(data)
        assert config.enabled is False
        assert config.model == "phi4:mini"
        assert config.categories == ["A", "B"]
        assert config.confidence_threshold == 0.8


class TestLoadOptions:
    """Tests for load_options function."""

    def test_load_options_none(self):
        """Load options with None (defaults)."""
        opts = load_options(None)
        assert isinstance(opts, Options)
        assert opts.dry_run is False
        assert opts.max_workers == 4

    def test_load_options_custom(self):
        """Load custom options."""
        data = {"dry_run": True, "max_workers": 8}
        opts = load_options(data)
        assert opts.dry_run is True
        assert opts.max_workers == 8


class TestLoadProfile:
    """Tests for load_profile function."""

    def test_load_valid_profile(self, temp_dir):
        """Load a valid profile YAML."""
        profile_data = {
            "name": "test",
            "version": "1.0",
            "sources": [{"path": str(temp_dir / "source")}],
            "destinations": {"dest1": {"path": str(temp_dir / "dest")}},
        }

        # Create source directory (required for validation)
        (temp_dir / "source").mkdir()

        profile_file = temp_dir / "test.yaml"
        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        profile = load_profile(profile_file)
        assert profile.name == "test"
        assert len(profile.sources) == 1
        assert len(profile.destinations) == 1

    def test_load_profile_not_found(self, temp_dir):
        """Load non-existent profile raises error."""
        with pytest.raises(FileNotFoundError):
            load_profile(temp_dir / "nonexistent.yaml")

    def test_load_profile_missing_sources(self, temp_dir):
        """Profile without sources raises error."""
        profile_data = {
            "name": "test",
            "destinations": {"dest1": {"path": str(temp_dir)}},
        }

        profile_file = temp_dir / "test.yaml"
        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        with pytest.raises(ValueError, match="must have at least one source"):
            load_profile(profile_file)

    def test_load_profile_missing_destinations(self, temp_dir):
        """Profile without destinations raises error."""
        (temp_dir / "source").mkdir()

        profile_data = {
            "name": "test",
            "sources": [{"path": str(temp_dir / "source")}],
        }

        profile_file = temp_dir / "test.yaml"
        with open(profile_file, "w") as f:
            yaml.dump(profile_data, f)

        with pytest.raises(ValueError, match="must have at least one destination"):
            load_profile(profile_file)
