"""Tests for rule matching engine."""

from pathlib import Path

import pytest

from file_organizer.config.models import (
    AIConfig,
    Destination,
    Options,
    Profile,
    Rule,
    Source,
)
from file_organizer.rules.engine import RuleEngine


class FakeAIResult:
    """Simple AI result stub for tests."""

    def __init__(self, category: str, confidence: float, reasoning: str = "stub"):
        self.category = category
        self.confidence = confidence
        self.reasoning = reasoning


class FakeAIClient:
    """Minimal AI client stub."""

    def __init__(self, result: FakeAIResult | None, threshold: float = 0.7):
        self.result = result
        self.calls: list[tuple[str, list[str] | None]] = []
        self.config = AIConfig(enabled=True, confidence_threshold=threshold)

    def classify(
        self, file_path: Path, content: str, categories: list[str] | None = None
    ) -> FakeAIResult | None:
        self.calls.append((file_path.name, categories))
        return self.result


class TestRuleEngine:
    """Tests for RuleEngine class."""

    @pytest.fixture
    def sample_profile(self, temp_dir):
        """Create a sample profile for testing."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        math_dest = Destination(
            path=temp_dir / "Math",
            rules=[
                Rule(type="filename_contains", keywords=["math", "algebra"]),
                Rule(type="extension", extensions=[".py"]),
            ],
        )

        pdf_dest = Destination(
            path=temp_dir / "PDFs",
            rules=[Rule(type="extension", extensions=[".pdf"])],
        )

        return Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[math_dest, pdf_dest],
            ai=AIConfig(enabled=False),
            options=Options(),
        )

    @pytest.fixture
    def engine(self, sample_profile):
        """Create a RuleEngine instance."""
        return RuleEngine(sample_profile)

    def test_match_filename_contains(self, temp_dir, engine):
        """Test filename_contains rule matching."""
        file_path = temp_dir / "math_homework.txt"
        file_path.write_text("content")

        result = engine.match_file(file_path)
        assert result.matched is True
        assert "math" in result.reason.lower()

    def test_match_extension(self, temp_dir, engine):
        """Test extension rule matching."""
        file_path = temp_dir / "document.pdf"
        file_path.write_text("content")

        result = engine.match_file(file_path)
        assert result.matched is True
        assert result.destination.path.name == "PDFs"

    def test_no_match(self, temp_dir, engine):
        """Test file with no matching rules."""
        file_path = temp_dir / "unknown.xyz"
        file_path.write_text("content")

        result = engine.match_file(file_path)
        assert result.matched is False

    def test_should_process_file_include_patterns(
        self, temp_dir, engine, sample_profile
    ):
        """Test include pattern filtering."""
        sample_profile.sources[0].include_patterns = ["*.pdf"]
        sample_profile.sources[0].exclude_patterns = []

        pdf_file = temp_dir / "source" / "test.pdf"
        pdf_file.parent.mkdir(exist_ok=True)
        pdf_file.write_text("content")

        txt_file = temp_dir / "source" / "test.txt"
        txt_file.write_text("content")

        assert engine.should_process_file(pdf_file, sample_profile.sources[0]) is True
        assert engine.should_process_file(txt_file, sample_profile.sources[0]) is False

    def test_should_process_file_exclude_patterns(
        self, temp_dir, engine, sample_profile
    ):
        """Test exclude pattern filtering."""
        sample_profile.sources[0].include_patterns = ["*"]
        sample_profile.sources[0].exclude_patterns = ["*.tmp", ".DS_Store"]

        temp_file = temp_dir / "source" / "test.tmp"
        temp_file.parent.mkdir(exist_ok=True)
        temp_file.write_text("content")

        normal_file = temp_dir / "source" / "test.txt"
        normal_file.write_text("content")

        assert engine.should_process_file(temp_file, sample_profile.sources[0]) is False
        assert (
            engine.should_process_file(normal_file, sample_profile.sources[0]) is True
        )


class TestRuleTypes:
    """Tests for individual rule types."""

    @pytest.fixture
    def engine(self, temp_dir):
        """Create a basic engine."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[],
            ai=AIConfig(enabled=False),
            options=Options(),
        )
        return RuleEngine(profile)

    def test_regex_rule_matching(self, temp_dir, engine):
        """Test regex rule matching."""
        rule = Rule(type="regex", pattern=r"report_\d{4}")
        dest = Destination(path=temp_dir / "Reports")

        matching_file = temp_dir / "report_2024.pdf"
        matching_file.write_text("content")

        non_matching_file = temp_dir / "document.txt"
        non_matching_file.write_text("content")

        result = engine._evaluate_rule(matching_file, rule, dest)
        assert result.matched is True

        result = engine._evaluate_rule(non_matching_file, rule, dest)
        assert result.matched is False

    def test_size_range_rule(self, temp_dir, engine):
        """Test size_range rule matching."""
        rule = Rule(type="size_range", min_size=100, max_size=1000)
        dest = Destination(path=temp_dir / "Sized")

        # Create files with specific sizes
        small_file = temp_dir / "small.txt"
        small_file.write_text("x" * 50)  # 50 bytes

        medium_file = temp_dir / "medium.txt"
        medium_file.write_text("x" * 500)  # 500 bytes

        large_file = temp_dir / "large.txt"
        large_file.write_text("x" * 2000)  # 2000 bytes

        assert engine._evaluate_rule(small_file, rule, dest).matched is False
        assert engine._evaluate_rule(medium_file, rule, dest).matched is True
        assert engine._evaluate_rule(large_file, rule, dest).matched is False

    def test_content_contains_rule(self, temp_dir, engine):
        """Test content_contains rule matching."""
        rule = Rule(type="content_contains", keywords=["IMPORTANT", "urgent"])
        dest = Destination(path=temp_dir / "Priority")

        important_file = temp_dir / "important.txt"
        important_file.write_text("This is an IMPORTANT document")

        normal_file = temp_dir / "normal.txt"
        normal_file.write_text("This is a regular document")

        result = engine._evaluate_rule(important_file, rule, dest)
        assert result.matched is True
        assert "IMPORTANT" in result.reason

        result = engine._evaluate_rule(normal_file, rule, dest)
        assert result.matched is False

    def test_unknown_rule_type(self, temp_dir, engine):
        """Test unknown rule type handling."""
        rule = Rule(type="unknown_type")
        dest = Destination(path=temp_dir / "Dest")

        test_file = temp_dir / "test.txt"
        test_file.write_text("content")

        result = engine._evaluate_rule(test_file, rule, dest)
        assert result.matched is False
        assert "Unknown" in result.reason

    def test_ai_match_returns_destination_from_ai_category(self, temp_dir):
        """AI match should resolve to the matching configured destination."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[
                Destination(
                    path=temp_dir / "Bewerbungen", rules=[Rule(type="ai_match")]
                ),
                Destination(path=temp_dir / "Lebenslaeufe", rules=[]),
            ],
            ai=AIConfig(enabled=True),
            options=Options(),
        )
        ai_client = FakeAIClient(FakeAIResult("Lebenslaeufe", 0.91, "resume"))
        engine = RuleEngine(profile, ai_client=ai_client)

        file_path = source_dir / "Lebenslauf_Youness.docx"
        file_path.write_text("resume")

        result = engine.match_file(file_path)

        assert result.matched is True
        assert result.destination.path.name == "Lebenslaeufe"
        assert "AI matched" in result.reason
        assert ai_client.calls[0][1] == ["Bewerbungen", "Lebenslaeufe"]

    def test_ai_fallback_runs_when_no_normal_rule_matches(self, temp_dir):
        """AI should act as fallback even without an explicit ai_match rule."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[
                Destination(
                    path=temp_dir / "Bewerbungen",
                    rules=[Rule(type="filename_contains", keywords=["anschreiben"])],
                ),
                Destination(path=temp_dir / "Lohnsteuerbescheinigungen 2025", rules=[]),
            ],
            ai=AIConfig(enabled=True),
            options=Options(),
        )
        ai_client = FakeAIClient(
            FakeAIResult("Lohnsteuerbescheinigungen 2025", 0.88, "tax document")
        )
        engine = RuleEngine(profile, ai_client=ai_client)

        file_path = source_dir / "Lohnsteuerbescheinigung 2025 07 Juli.pdf"
        file_path.write_text("steuer")

        result = engine.match_file(file_path)

        assert result.matched is True
        assert result.destination.path.name == "Lohnsteuerbescheinigungen 2025"

    def test_ai_match_respects_confidence_threshold(self, temp_dir):
        """Low-confidence AI responses should not match."""
        source_dir = temp_dir / "source"
        source_dir.mkdir()

        profile = Profile(
            name="test",
            version="1.0",
            sources=[Source(path=source_dir)],
            destinations=[
                Destination(
                    path=temp_dir / "Bewerbungen", rules=[Rule(type="ai_match")]
                )
            ],
            ai=AIConfig(enabled=True, confidence_threshold=0.8),
            options=Options(),
        )
        ai_client = FakeAIClient(
            FakeAIResult("Bewerbungen", 0.51, "uncertain"), threshold=0.8
        )
        engine = RuleEngine(profile, ai_client=ai_client)

        file_path = source_dir / "document.pdf"
        file_path.write_text("content")

        result = engine.match_file(file_path)

        assert result.matched is False
        assert "below threshold" in result.reason
