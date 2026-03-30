"""Tests for configuration data models."""

from foldify.config.models import (
    AIConfig,
    Destination,
    Options,
    Profile,
    Rule,
    Source,
)


class TestSource:
    """Tests for Source model."""

    def test_source_defaults(self, temp_dir):
        """Test Source with default values."""
        source = Source(path=temp_dir)
        assert source.path == temp_dir
        assert source.recursive is True
        assert source.include_patterns == ["*"]
        assert source.exclude_patterns == []

    def test_source_custom_values(self, temp_dir):
        """Test Source with custom values."""
        source = Source(
            path=temp_dir,
            recursive=False,
            include_patterns=["*.pdf"],
            exclude_patterns=[".DS_Store"],
        )
        assert source.recursive is False
        assert source.include_patterns == ["*.pdf"]
        assert source.exclude_patterns == [".DS_Store"]


class TestRule:
    """Tests for Rule model."""

    def test_rule_defaults(self):
        """Test Rule with defaults."""
        rule = Rule(type="filename_contains")
        assert rule.type == "filename_contains"
        assert rule.keywords is None
        assert rule.extensions is None

    def test_rule_with_keywords(self):
        """Test Rule with keywords."""
        rule = Rule(type="filename_contains", keywords=["math", "physics"])
        assert rule.keywords == ["math", "physics"]

    def test_rule_with_extensions(self):
        """Test Rule with extensions."""
        rule = Rule(type="extension", extensions=[".pdf", ".docx"])
        assert rule.extensions == [".pdf", ".docx"]


class TestDestination:
    """Tests for Destination model."""

    def test_destination_defaults(self, temp_dir):
        """Test Destination defaults."""
        dest = Destination(path=temp_dir)
        assert dest.path == temp_dir
        assert dest.rules == []
        assert dest.create_if_missing is True

    def test_destination_with_rules(self, temp_dir):
        """Test Destination with rules."""
        rule = Rule(type="extension", extensions=[".pdf"])
        dest = Destination(path=temp_dir, rules=[rule])
        assert len(dest.rules) == 1
        assert dest.rules[0].type == "extension"


class TestAIConfig:
    """Tests for AIConfig model."""

    def test_ai_config_defaults(self):
        """Test AIConfig defaults."""
        config = AIConfig()
        assert config.enabled is True
        assert config.model == "qwen3:8b"
        assert config.categories == []
        assert config.confidence_threshold == 0.7
        assert config.max_content_length == 2000
        assert config.cache_results is True

    def test_ai_config_disabled(self):
        """Test disabled AI config."""
        config = AIConfig(enabled=False)
        assert config.enabled is False


class TestOptions:
    """Tests for Options model."""

    def test_options_defaults(self):
        """Test Options defaults."""
        opts = Options()
        assert opts.dry_run is False
        assert opts.backup_conflicts is True
        assert opts.log_level == "INFO"
        assert opts.log_file is None
        assert opts.max_workers == 4

    def test_options_dry_run(self):
        """Test Options with dry_run."""
        opts = Options(dry_run=True)
        assert opts.dry_run is True


class TestProfile:
    """Tests for Profile model."""

    def test_profile_creation(self, temp_dir):
        """Test Profile creation."""
        source = Source(path=temp_dir / "source")
        dest = Destination(path=temp_dir / "dest")
        ai = AIConfig(enabled=False)
        opts = Options()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[source],
            destinations=[dest],
            ai=ai,
            options=opts,
        )

        assert profile.name == "test"
        assert profile.version == "1.0"

    def test_get_destination_for_category(self, temp_dir):
        """Test finding destination by category name."""
        math_dest = Destination(path=temp_dir / "Math")
        physics_dest = Destination(path=temp_dir / "Physics")

        profile = Profile(
            name="test",
            version="1.0",
            sources=[],
            destinations=[math_dest, physics_dest],
            ai=AIConfig(),
            options=Options(),
        )

        found = profile.get_destination_for_category("math")
        assert found == math_dest

        found = profile.get_destination_for_category("Physics")
        assert found == physics_dest

        not_found = profile.get_destination_for_category("Chemistry")
        assert not_found is None
