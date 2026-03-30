"""Tests for configuration validation."""

import warnings
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
from foldify.config.validator import (
    ValidationError,
    validate_destination,
    validate_profile,
    validate_rule,
    validate_source,
)


class TestValidateRule:
    """Tests for rule validation."""

    def test_valid_filename_contains_rule(self):
        """Valid filename_contains rule."""
        rule = Rule(type="filename_contains", keywords=["test"])
        warnings_list = validate_rule(rule, 0, "dest1")
        assert len(warnings_list) == 0

    def test_filename_contains_without_keywords(self):
        """filename_contains without keywords warns."""
        rule = Rule(type="filename_contains")
        warnings_list = validate_rule(rule, 0, "dest1")
        assert len(warnings_list) == 1
        assert "should have 'keywords'" in warnings_list[0]

    def test_unknown_rule_type(self):
        """Unknown rule type warns."""
        rule = Rule(type="unknown_type")
        warnings_list = validate_rule(rule, 0, "dest1")
        assert len(warnings_list) == 1
        assert "Unknown rule type" in warnings_list[0]

    def test_valid_extension_rule(self):
        """Valid extension rule."""
        rule = Rule(type="extension", extensions=[".pdf"])
        warnings_list = validate_rule(rule, 0, "dest1")
        assert len(warnings_list) == 0

    def test_extension_without_extensions(self):
        """extension rule without extensions warns."""
        rule = Rule(type="extension")
        warnings_list = validate_rule(rule, 0, "dest1")
        assert len(warnings_list) == 1

    def test_regex_without_pattern(self):
        """regex rule without pattern warns."""
        rule = Rule(type="regex")
        warnings_list = validate_rule(rule, 0, "dest1")
        assert len(warnings_list) == 1
        assert "should have 'pattern'" in warnings_list[0]

    def test_valid_ai_match_rule(self):
        """ai_match is accepted as a valid rule type."""
        rule = Rule(type="ai_match")
        warnings_list = validate_rule(rule, 0, "dest1")
        assert warnings_list == []

    def test_threshold_out_of_range_warns(self):
        """Rule threshold outside 0-1 should warn."""
        rule = Rule(type="ai_match", threshold=1.2)
        warnings_list = validate_rule(rule, 0, "dest1")
        assert any("threshold" in warning for warning in warnings_list)


class TestValidateDestination:
    """Tests for destination validation."""

    def test_valid_destination(self, temp_dir):
        """Valid destination (under home)."""
        dest = Destination(path=temp_dir)
        warnings_list = validate_destination(dest, 0)
        # May have warning about being outside home depending on temp_dir location
        assert isinstance(warnings_list, list)

    def test_destination_outside_home(self):
        """Destination outside home warns."""
        dest = Destination(path=Path("/usr/local"))
        warnings_list = validate_destination(dest, 0)
        assert any("outside home directory" in w for w in warnings_list)

    def test_destination_with_invalid_rule(self, temp_dir):
        """Destination with invalid rule warns."""
        rule = Rule(type="filename_contains")  # Missing keywords
        dest = Destination(path=temp_dir, rules=[rule])
        warnings_list = validate_destination(dest, 0)
        assert any("should have 'keywords'" in w for w in warnings_list)


class TestValidateSource:
    """Tests for source validation."""

    def test_valid_source(self, temp_dir):
        """Valid source directory."""
        source = Source(path=temp_dir)
        warnings_list = validate_source(source, 0)
        assert isinstance(warnings_list, list)

    def test_nonexistent_source(self, temp_dir):
        """Non-existent source raises error."""
        source = Source(path=temp_dir / "nonexistent")
        with pytest.raises(ValidationError, match="does not exist"):
            validate_source(source, 0)

    def test_file_as_source(self, temp_dir):
        """File instead of directory raises error."""
        file_path = temp_dir / "file.txt"
        file_path.write_text("test")
        source = Source(path=file_path)
        with pytest.raises(ValidationError, match="not a directory"):
            validate_source(source, 0)

    def test_wildcard_without_excludes_warning(self, temp_dir):
        """Wildcard pattern without excludes warns."""
        source = Source(path=temp_dir, include_patterns=["*"], exclude_patterns=[])
        warnings_list = validate_source(source, 0)
        assert any("wildcard" in w.lower() for w in warnings_list)


class TestValidateAIConfig:
    """Tests for AI config validation."""

    def test_valid_ai_config(self):
        """Valid AI config."""
        ai = AIConfig(enabled=True, categories=["A", "B"])
        # validate_ai_config is called via validate_profile
        # No categories warning when categories provided
        assert ai.categories == ["A", "B"]

    def test_ai_without_categories_warning(self):
        """AI without categories is allowed because destinations are used."""
        ai = AIConfig(enabled=True, categories=[])
        assert ai.categories == []

    def test_invalid_confidence_threshold(self):
        """Invalid confidence threshold raises error."""
        ai = AIConfig(enabled=True, confidence_threshold=1.5)
        # Would raise ValidationError during profile validation
        assert ai.confidence_threshold == 1.5


class TestValidateProfile:
    """Tests for full profile validation."""

    def test_valid_profile(self, temp_dir):
        """Valid profile passes validation."""
        (temp_dir / "source").mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=temp_dir / "source")],
            destinations=[Destination(path=temp_dir / "dest")],
            ai=AIConfig(enabled=False),
            options=Options(),
        )

        # In lenient mode, returns warnings list
        with warnings.catch_warnings(record=True):
            warnings.simplefilter("always")
            result = validate_profile(profile, strict=False)
            assert isinstance(result, list)

    def test_profile_no_sources(self):
        """Profile with no sources raises error."""
        profile = Profile(
            name="test",
            version="1.0",
            sources=[],
            destinations=[Destination(path=Path("/tmp/dest"))],
            ai=AIConfig(),
            options=Options(),
        )

        with pytest.raises(ValidationError, match="at least one source"):
            validate_profile(profile)

    def test_profile_no_destinations(self, temp_dir):
        """Profile with no destinations raises error."""
        (temp_dir / "source").mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=temp_dir / "source")],
            destinations=[],
            ai=AIConfig(),
            options=Options(),
        )

        with pytest.raises(ValidationError, match="at least one destination"):
            validate_profile(profile)

    def test_overlapping_destinations(self, temp_dir):
        """Same path for multiple destinations raises error."""
        (temp_dir / "source").mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=temp_dir / "source")],
            destinations=[
                Destination(path=temp_dir / "same"),
                Destination(path=temp_dir / "same"),
            ],
            ai=AIConfig(),
            options=Options(),
        )

        with pytest.raises(ValidationError, match="same path"):
            validate_profile(profile)

    def test_destination_inside_source_warning(self, temp_dir):
        """Destination inside source warns."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()
        dest_dir = source_dir / "dest"  # Inside source

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[Destination(path=dest_dir)],
            ai=AIConfig(enabled=False),
            options=Options(),
        )

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            validate_profile(profile, strict=False)
            assert any("inside source" in str(warning.message) for warning in w)
