"""Ollama client for AI-powered classification."""

import hashlib
import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..config.models import AIConfig

logger = logging.getLogger(__name__)


@dataclass
class ClassificationResult:
    """Result of AI classification."""

    category: str
    confidence: float
    reasoning: str
    cached: bool = False


class AIClient:
    """Client for Ollama AI classification."""

    def __init__(self, config: AIConfig, cache_dir: Path | None = None):
        self.config = config
        self._client: Any | None = None
        self.cache_dir = cache_dir

        if self.config.cache_results and self.cache_dir:
            self.cache_dir.mkdir(parents=True, exist_ok=True)

    def _get_client(self) -> Any:
        """Lazy load Ollama client."""
        if self._client is None:
            try:
                import ollama

                self._client = ollama
            except ImportError:
                raise RuntimeError(
                    "Ollama package not installed. " "Install with: pip install ollama"
                )
        return self._client

    def is_available(self) -> bool:
        """Check if Ollama is available and the model is pulled."""
        try:
            client = self._get_client()
            # Check if model exists
            client.list()
            return True
        except Exception as e:
            logger.debug(f"Ollama not available: {e}")
            return False

    def classify(
        self,
        file_path: Path,
        content: str,
        categories: list[str] | None = None,
    ) -> ClassificationResult | None:
        """
        Classify a file using AI.

        Args:
            file_path: Path to the file
            content: Extracted text content

        Returns:
            ClassificationResult or None if classification failed
        """
        if not self.config.enabled:
            return None

        # Check cache first
        if self.config.cache_results and self.cache_dir:
            cached = self._get_cached(file_path, content)
            if cached:
                return cached

        # Truncate content if too long
        if len(content) > self.config.max_content_length:
            content = content[: self.config.max_content_length] + "..."

        # Build prompt
        prompt = self._build_prompt(file_path, content, categories=categories)

        try:
            client = self._get_client()
            response = client.generate(
                model=self.config.model,
                prompt=prompt,
                stream=False,
            )

            result = self._parse_response(response.response)

            # Cache result
            if result and self.config.cache_results and self.cache_dir:
                self._cache_result(file_path, content, result)

            return result

        except Exception as e:
            logger.error(f"AI classification failed for {file_path}: {e}")
            return None

    def _build_prompt(
        self, file_path: Path, content: str, categories: list[str] | None = None
    ) -> str:
        """Build classification prompt."""
        available_categories = (
            categories if categories is not None else self.config.categories
        )
        categories_str = (
            ", ".join(available_categories)
            if available_categories
            else "any relevant category"
        )

        prompt = (
            "Classify this file into one of the following categories: "
            f"{categories_str}\n\n"
            f"Filename: {file_path.name}\n"
            "Content preview:\n"
            "```\n"
            f"{content}\n"
            "```\n\n"
            "Respond with exactly one category name from the list above, "
            "followed by a confidence score (0.0-1.0), and a brief reasoning.\n\n"
            "Format your response as:\n"
            "Category: [category name]\n"
            "Confidence: [0.0-1.0]\n"
            "Reasoning: [brief explanation]\n"
        )
        return prompt

    def _parse_response(self, response: str) -> ClassificationResult | None:
        """Parse AI response into ClassificationResult."""
        try:
            lines = response.strip().split("\n")
            category = ""
            confidence = 0.5
            reasoning = ""

            for line in lines:
                line = line.strip()
                if line.lower().startswith("category:"):
                    category = line.split(":", 1)[1].strip()
                elif line.lower().startswith("confidence:"):
                    conf_str = line.split(":", 1)[1].strip()
                    try:
                        confidence = float(conf_str)
                    except ValueError:
                        confidence = 0.5
                elif line.lower().startswith("reasoning:"):
                    reasoning = line.split(":", 1)[1].strip()

            if not category:
                # Try to extract just the first line as category
                category = lines[0].strip() if lines else "unknown"

            return ClassificationResult(
                category=category,
                confidence=confidence,
                reasoning=reasoning,
            )

        except Exception as e:
            logger.warning(f"Failed to parse AI response: {e}")
            return ClassificationResult(
                category="unknown",
                confidence=0.0,
                reasoning="Failed to parse response",
            )

    def _get_cache_key(self, file_path: Path, content: str) -> str:
        """Generate cache key for a file."""
        key_data = f"{file_path.name}:{content[:500]}:{self.config.model}"
        return hashlib.sha256(key_data.encode()).hexdigest()

    def _get_cached(self, file_path: Path, content: str) -> ClassificationResult | None:
        """Get cached classification result."""
        if not self.cache_dir:
            return None

        cache_key = self._get_cache_key(file_path, content)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if cache_file.exists():
            try:
                data = json.loads(cache_file.read_text())
                return ClassificationResult(
                    category=data["category"],
                    confidence=data["confidence"],
                    reasoning=data["reasoning"],
                    cached=True,
                )
            except (json.JSONDecodeError, KeyError):
                return None

        return None

    def _cache_result(
        self,
        file_path: Path,
        content: str,
        result: ClassificationResult,
    ) -> None:
        """Cache classification result."""
        if not self.cache_dir:
            return

        cache_key = self._get_cache_key(file_path, content)
        cache_file = self.cache_dir / f"{cache_key}.json"

        data = {
            "category": result.category,
            "confidence": result.confidence,
            "reasoning": result.reasoning,
            "model": self.config.model,
        }

        try:
            cache_file.write_text(json.dumps(data))
        except Exception as e:
            logger.debug(f"Failed to cache result: {e}")


def check_ollama_status() -> dict[str, object]:
    """Check Ollama installation and available models."""
    try:
        import ollama

        client = ollama
        models = client.list()

        return {
            "installed": True,
            "running": True,
            "models": [m.model for m in models.models] if models.models else [],
        }
    except ImportError:
        return {"installed": False, "running": False, "models": []}
    except Exception as e:
        return {
            "installed": True,
            "running": False,
            "models": [],
            "error": str(e),
        }
