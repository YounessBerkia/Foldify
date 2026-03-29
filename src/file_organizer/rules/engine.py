"""Rule matching engine for file classification."""

import fnmatch
import re
import unicodedata
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Callable, Optional

from ..config.models import Destination, Profile, Rule, Source

if TYPE_CHECKING:
    from ..ai.client import AIClient


class RuleMatchResult:
    """Result of a rule match."""

    def __init__(
        self,
        matched: bool,
        destination: Optional[Destination] = None,
        rule: Optional[Rule] = None,
        confidence: float = 1.0,
        reason: str = "",
    ):
        self.matched = matched
        self.destination = destination
        self.rule = rule
        self.confidence = confidence
        self.reason = reason


class RuleEngine:
    """Engine for matching files against rules."""

    def __init__(
        self,
        profile: Profile,
        ai_client: Optional["AIClient"] = None,
        status_callback: Callable[[str, Path], None] | None = None,
    ):
        self.profile = profile
        self.ai_client = ai_client
        self.status_callback = status_callback
        self._content_cache: dict[Path, str] = {}

    def should_process_file(self, file_path: Path, source: Source) -> bool:
        """Check if a file should be processed based on source filters."""
        for pattern in source.exclude_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return False
            if file_path.match(pattern):
                return False

        if not source.include_patterns:
            return True

        for pattern in source.include_patterns:
            if fnmatch.fnmatch(file_path.name, pattern):
                return True
            if file_path.match(pattern):
                return True

        return False

    def match_file(self, file_path: Path) -> RuleMatchResult:
        """
        Match a file against all destinations and their rules.

        Non-AI rules are evaluated first. If nothing matches and AI is enabled,
        AI classification acts as a fallback across all configured destinations.
        """
        ai_rule: tuple[Rule, Destination] | None = None

        for destination in self.profile.destinations:
            for rule in destination.rules:
                if rule.type == "ai_match":
                    if ai_rule is None:
                        ai_rule = (rule, destination)
                    continue

                result = self._evaluate_rule(file_path, rule, destination)
                if result.matched:
                    return result

        if self.ai_client and self.ai_client.config.enabled:
            fallback_rule = ai_rule[0] if ai_rule else Rule(type="ai_match")
            fallback_destination = (
                ai_rule[1] if ai_rule else self.profile.destinations[0]
            )
            return self._match_ai(file_path, fallback_rule, fallback_destination)

        return RuleMatchResult(matched=False, reason="No matching rule found")

    def _evaluate_rule(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Evaluate a single rule against a file."""
        match rule.type:
            case "filename_contains":
                return self._match_filename_contains(file_path, rule, destination)
            case "extension":
                return self._match_extension(file_path, rule, destination)
            case "content_contains":
                return self._match_content_contains(file_path, rule, destination)
            case "size_range":
                return self._match_size_range(file_path, rule, destination)
            case "date_range":
                return self._match_date_range(file_path, rule, destination)
            case "regex":
                return self._match_regex(file_path, rule, destination)
            case "ai_match":
                return self._match_ai(file_path, rule, destination)
            case _:
                return RuleMatchResult(
                    matched=False, reason=f"Unknown rule type: {rule.type}"
                )

    def _match_filename_contains(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match if filename contains any of the keywords."""
        if not rule.keywords:
            return RuleMatchResult(matched=False, reason="No keywords specified")

        filename_normalized = self._normalize_text(file_path.name)
        for keyword in rule.keywords:
            if self._normalize_text(keyword) in filename_normalized:
                return RuleMatchResult(
                    matched=True,
                    destination=destination,
                    rule=rule,
                    reason=f"Filename contains '{keyword}'",
                )

        return RuleMatchResult(matched=False, reason="No keyword match in filename")

    def _match_extension(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match if file extension is in the list."""
        if not rule.extensions:
            return RuleMatchResult(matched=False, reason="No extensions specified")

        file_ext = file_path.suffix.lower()
        for ext in rule.extensions:
            ext_clean = ext.lower()
            if not ext_clean.startswith("."):
                ext_clean = f".{ext_clean}"
            if file_ext == ext_clean:
                return RuleMatchResult(
                    matched=True,
                    destination=destination,
                    rule=rule,
                    reason=f"Extension matches '{ext}'",
                )

        return RuleMatchResult(matched=False, reason="Extension not in list")

    def _match_content_contains(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match if file content contains any of the keywords."""
        if not rule.keywords:
            return RuleMatchResult(matched=False, reason="No keywords specified")

        content = self._get_file_content(file_path)
        if content is None:
            return RuleMatchResult(matched=False, reason="Could not read file content")

        content_normalized = self._normalize_text(content)
        for keyword in rule.keywords:
            if self._normalize_text(keyword) in content_normalized:
                return RuleMatchResult(
                    matched=True,
                    destination=destination,
                    rule=rule,
                    reason=f"Content contains '{keyword}'",
                )

        return RuleMatchResult(matched=False, reason="No keyword match in content")

    def _match_size_range(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match if file size is within range."""
        try:
            size = file_path.stat().st_size
        except (OSError, IOError):
            return RuleMatchResult(matched=False, reason="Could not get file size")

        if rule.min_size is not None and size < rule.min_size:
            return RuleMatchResult(
                matched=False, reason=f"Size {size} < min {rule.min_size}"
            )

        if rule.max_size is not None and size > rule.max_size:
            return RuleMatchResult(
                matched=False, reason=f"Size {size} > max {rule.max_size}"
            )

        return RuleMatchResult(
            matched=True,
            destination=destination,
            rule=rule,
            reason=f"Size {size} within range",
        )

    def _match_date_range(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match if file modification time is within range."""
        try:
            mtime = datetime.fromtimestamp(file_path.stat().st_mtime)
        except (OSError, IOError):
            return RuleMatchResult(
                matched=False, reason="Could not get file modification time"
            )

        now = datetime.now()

        if rule.older_than_days is not None:
            cutoff = now - timedelta(days=rule.older_than_days)
            if mtime > cutoff:
                return RuleMatchResult(
                    matched=False,
                    reason=f"File is newer than {rule.older_than_days} days",
                )

        if rule.newer_than_days is not None:
            cutoff = now - timedelta(days=rule.newer_than_days)
            if mtime < cutoff:
                return RuleMatchResult(
                    matched=False,
                    reason=f"File is older than {rule.newer_than_days} days",
                )

        return RuleMatchResult(
            matched=True,
            destination=destination,
            rule=rule,
            reason="File age within range",
        )

    def _match_regex(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match filename against regex pattern."""
        if not rule.pattern:
            return RuleMatchResult(matched=False, reason="No pattern specified")

        try:
            pattern = re.compile(rule.pattern, re.IGNORECASE)
        except re.error as exc:
            return RuleMatchResult(
                matched=False, reason=f"Invalid regex pattern: {exc}"
            )

        if pattern.search(file_path.name):
            return RuleMatchResult(
                matched=True,
                destination=destination,
                rule=rule,
                reason=f"Filename matches pattern '{rule.pattern}'",
            )

        return RuleMatchResult(matched=False, reason="Pattern not matched")

    def _match_ai(
        self, file_path: Path, rule: Rule, destination: Destination
    ) -> RuleMatchResult:
        """Match file using AI classification across all destinations."""
        if not self.ai_client or not self.ai_client.config.enabled:
            return RuleMatchResult(
                matched=False, reason="AI client not available or disabled"
            )

        content = self._get_file_content(file_path) or file_path.name
        categories = self._build_ai_categories(rule)
        if self.status_callback:
            self.status_callback("ai_started", file_path)
        result = self.ai_client.classify(file_path, content, categories=categories)
        if self.status_callback:
            self.status_callback("ai_finished", file_path)

        if result is None:
            return RuleMatchResult(matched=False, reason="AI classification failed")

        threshold = (
            rule.threshold
            if rule.threshold is not None
            else self.ai_client.config.confidence_threshold
        )
        if result.confidence < threshold:
            return RuleMatchResult(
                matched=False,
                reason=(
                    f"AI confidence {result.confidence:.2%} below threshold "
                    f"{threshold:.2%}"
                ),
            )

        matched_destination = self._find_destination_for_category(result.category)
        if not matched_destination:
            return RuleMatchResult(
                matched=False,
                reason=(
                    f"AI suggested '{result.category}' "
                    "but no matching destination found"
                ),
            )

        return RuleMatchResult(
            matched=True,
            destination=matched_destination,
            rule=rule,
            confidence=result.confidence,
            reason=(
                f"AI matched to '{matched_destination.path.name}': "
                f"{result.reasoning}"
            ),
        )

    def _build_ai_categories(self, rule: Rule) -> list[str]:
        """Build the list of categories to offer to the AI."""
        categories = [
            destination.path.name for destination in self.profile.destinations
        ]
        if rule.keywords:
            categories.extend(rule.keywords)

        unique_categories: list[str] = []
        seen: set[str] = set()
        for category in categories:
            normalized = self._normalize_text(category)
            if normalized not in seen:
                seen.add(normalized)
                unique_categories.append(category)
        return unique_categories

    def _find_destination_for_category(self, category: str) -> Optional[Destination]:
        """Resolve an AI category back to a configured destination."""
        normalized_category = self._normalize_text(category)

        for destination in self.profile.destinations:
            if self._normalize_text(destination.path.name) == normalized_category:
                return destination

        return None

    def _get_file_content(self, file_path: Path) -> Optional[str]:
        """Get text content of a file, with caching."""
        if file_path in self._content_cache:
            return self._content_cache[file_path]

        content = self._extract_text(file_path)
        if content is not None:
            self._content_cache[file_path] = content

        return content

    def _extract_text(self, file_path: Path) -> Optional[str]:
        """Extract text content from various file types."""
        suffix = file_path.suffix.lower()

        if suffix in {
            ".txt",
            ".md",
            ".json",
            ".yaml",
            ".yml",
            ".py",
            ".js",
            ".html",
            ".css",
            ".csv",
        }:
            try:
                return file_path.read_text(encoding="utf-8", errors="ignore")
            except (OSError, IOError):
                return None

        if suffix == ".pdf":
            return self._extract_pdf_text(file_path)

        if suffix in {".docx", ".doc"}:
            return self._extract_docx_text(file_path)

        return None

    def _extract_pdf_text(self, file_path: Path) -> Optional[str]:
        """Extract text from PDF file."""
        try:
            from pypdf import PdfReader

            reader = PdfReader(str(file_path))
            text_parts = []
            for page in reader.pages[:5]:
                text_parts.append(page.extract_text() or "")
            return "\n".join(text_parts)
        except Exception:
            return None

    def _extract_docx_text(self, file_path: Path) -> Optional[str]:
        """Extract text from Word document."""
        try:
            from docx import Document

            doc = Document(str(file_path))
            text_parts = []
            for para in doc.paragraphs[:50]:
                text_parts.append(para.text)
            return "\n".join(text_parts)
        except Exception:
            return None

    @staticmethod
    def _normalize_text(value: str) -> str:
        """Normalize text for accent-insensitive comparisons."""
        normalized = unicodedata.normalize("NFKD", value)
        return "".join(
            ch for ch in normalized if not unicodedata.combining(ch)
        ).casefold()
