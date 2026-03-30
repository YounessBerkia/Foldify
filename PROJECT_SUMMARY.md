# Foldify - Project Summary

## Project Overview

An intelligent file organization tool with AI-powered classification using Ollama.

## Project Structure

```
foldify/
├── src/foldify/          # Main source code
│   ├── __init__.py              # Package init with version
│   ├── cli.py                   # CLI entry point (Click-based)
│   ├── py.typed                 # PEP 561 marker
│   ├── ai/                      # AI integration
│   │   ├── __init__.py
│   │   └── client.py            # Ollama client
│   ├── config/                  # Configuration handling
│   │   ├── __init__.py
│   │   ├── loader.py            # YAML loading
│   │   ├── models.py            # Dataclasses
│   │   └── validator.py         # Validation
│   ├── core/                    # Core logic
│   │   ├── __init__.py
│   │   ├── executor.py          # File operations with rollback
│   │   ├── organizer.py         # Main orchestration
│   │   └── scanner.py           # File discovery
│   ├── rules/                   # Rule engine
│   │   ├── __init__.py
│   │   └── engine.py            # Rule matching
│   └── utils/                   # Utilities
│       ├── __init__.py
│       └── helpers.py           # Helper functions
├── tests/                       # Test suite
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/                    # Unit tests
│   │   ├── test_config_models.py
│   │   ├── test_config_loader.py
│   │   ├── test_config_validator.py
│   │   ├── test_rules_engine.py
│   │   ├── test_core_executor.py
│   │   └── test_core_scanner.py
│   ├── integration/             # Integration tests
│   │   ├── test_organize_workflow.py
│   │   └── test_cli_commands.py
│   └── fixtures/                # Test fixtures
├── examples/                    # Example profiles
│   ├── README.md
│   ├── school.yaml.example
│   ├── work.yaml.example
│   ├── desktop-cleanup.yaml.example
│   └── ai-smart.yaml.example
├── docs/                        # Documentation
│   ├── README.md
│   ├── CONFIGURATION.md         # Configuration guide
│   └── TROUBLESHOOTING.md       # Troubleshooting guide
├── .github/workflows/           # CI/CD
│   └── ci.yml
├── pyproject.toml               # Package configuration
├── MANIFEST.in                  # Package manifest
├── .pre-commit-config.yaml      # Pre-commit hooks
├── .gitignore                   # Git ignore
├── CHANGELOG.md                 # Changelog
├── CONTRIBUTING.md              # Contribution guidelines
├── LICENSE                      # MIT License
└── README.md                    # Main README
```

## Features Implemented

### Core Features
- ✅ Profile-based configuration (YAML)
- ✅ Hierarchical rule engine (7 rule types)
- ✅ AI-powered classification (Ollama integration)
- ✅ Safe operations (dry-run, backups, rollback)
- ✅ Multi-source/multi-destination support

### Rule Types
1. filename_contains - Match keywords in filename
2. extension - Match file extensions
3. content_contains - Match text in file content
4. size_range - Match file size range
5. date_range - Match file modification date
6. regex - Match filename with regex pattern
7. ai_match - Let Ollama choose the best destination

### AI Features
- Local AI classification via Ollama
- Support for qwen3:8b, phi4:mini models
- Configurable confidence threshold
- Result caching
- AI fallback after normal rules

### CLI Commands
- `foldify init` - Initialize/create profiles
- `foldify list` - List profiles
- `foldify validate <profile>` - Validate profile
- `foldify run -p <profile>` - Execute organization
- `foldify ai status` - Check AI status
- `foldify ai setup` - AI setup guide

### Safety Features
- Dry-run mode for preview
- Automatic conflict backups
- Rollback capability
- Profile validation
- Path expansion (~ and env vars)

## Installation

```bash
# Development install
pip install -e "."

# With dev dependencies
pip install -e ".[dev]"
```

## Usage

```bash
# Create profile from template
foldify init --template school --profile myschool

# Preview changes
foldify run --profile myschool --dry-run

# Execute
foldify run --profile myschool
```

## Testing

```bash
# Run all tests
pytest

# With coverage
pytest --cov=foldify

# Specific test
pytest tests/unit/test_config_models.py
```

## Quality Tools

- black - Code formatting
- ruff - Linting
- mypy - Type checking
- pytest - Testing
- pre-commit - Git hooks

## Next Steps

1. Install dependencies: `pip install -e "."`
2. Run tests: `pytest`
3. Install pre-commit hooks: `pre-commit install`
4. Try example profiles
5. Create your own profiles

## License

MIT License - See LICENSE file
