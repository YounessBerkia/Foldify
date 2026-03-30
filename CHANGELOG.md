# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Changed
- Documentation and packaging metadata aligned with the real CLI workflow
- Ruff and mypy issues resolved so the default quality checks pass cleanly
- AI fallback and `ai_match` behavior documented more clearly

## [0.1.0] - 2026-03-29

### Added
- Initial release of Foldify
- Profile-based configuration system
- Hierarchical rule engine with 7 rule types:
  - filename_contains
  - extension
  - content_contains
  - size_range
  - date_range
  - regex
  - ai_match
- AI-powered classification via Ollama
- Safe operations with dry-run mode
- Conflict resolution with automatic backups
- Multi-source and multi-destination support
- CLI with profile management commands
- Example profiles for school, work, cleanup, and AI-oriented use cases
- Comprehensive test suite
- Documentation (README, CONFIGURATION, TROUBLESHOOTING, CONTRIBUTING)

[Unreleased]: https://github.com/YounessBerkia/Local-AI-Folder-Organizer/compare/v0.1.0...HEAD
[0.1.0]: https://github.com/YounessBerkia/Local-AI-Folder-Organizer/releases/tag/v0.1.0
