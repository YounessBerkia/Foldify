# File Organizer

An intelligent file organization tool with AI-powered classification. Organize your files using rules, patterns, or local AI models via Ollama.

## Status

File Organizer is currently in **alpha**. The core workflow, tests, linting, and strict type checks are in place, but the project is still early and the CLI/API may evolve.

## Features

- **Profile-based configuration** - Multiple use cases, one tool
- **Hierarchical rule engine** - Filename → Content → AI classification
- **Safe operations** - Dry-run mode, conflict resolution, undo support
- **Local AI integration** - Optional Ollama support for smart categorization
- **Multiple file types** - PDF, DOCX, TXT, and more
- **Strict quality checks** - `pytest`, `ruff`, and `mypy` all pass locally

## Installation

```bash
# Clone the repository
git clone https://github.com/YounesBerkia/Local-AI-Folder-Organizer.git
cd Local-AI-Folder-Organizer

# Install with pip
pip install -e .

# Or install development dependencies
pip install -e ".[dev]"
```

## Quick Start

```bash
# Create config folders
file-organizer init

# See available templates
file-organizer init --list-templates

# Create your first profile from a template
file-organizer init --template school --profile school

# Preview changes (dry run)
file-organizer run --profile school --dry-run

# If you want the preview colors optimized for your terminal background:
file-organizer run --profile school --dry-run --theme dark
file-organizer run --profile school --dry-run --theme light

# Execute organization
file-organizer run --profile school
```

## Configuration

Profiles are stored in `~/.config/file-organizer/profiles/`.

Use `file-organizer list` to see installed profiles.

See [examples/](examples/) for sample configurations and [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full profile format.

## AI Integration

File Organizer can use local AI models via Ollama for intelligent classification:

```bash
# Check AI status
file-organizer ai status

# Setup recommended model
file-organizer ai setup

# Create an AI-oriented profile from a template
file-organizer init --template ai-smart --profile ai-smart

# Preview AI-based decisions
file-organizer run --profile ai-smart --dry-run
```

AI is used as a fallback after normal rules. In practice that means obvious matches can be handled by fast filename/content rules, while ambiguous files can still be classified by Ollama. You can also add an explicit `ai_match` rule to a destination when you want AI-backed routing in the profile itself.

### Supported Models

- `qwen3:8b` (recommended, ~5.5GB)
- `phi4:mini` (fast, ~4GB)
- Custom Ollama models

## Limitations

- Ollama must be installed and running locally for AI-based matching
- AI classifications depend on the quality of the selected local model
- The project is currently optimized for local CLI usage, not long-running background services

## Documentation

- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting Guide](docs/TROUBLESHOOTING.md)
- [Example Profiles](examples/README.md)
- [Contributing Guide](CONTRIBUTING.md)

## Project Structure

```
file-organizer/
├── src/file_organizer/     # Main package
├── examples/               # Sample configurations
├── tests/                  # Test suite
└── docs/                   # Documentation
```

## Development

```bash
# Run tests
pytest

# Format code
black src/ tests/
ruff check --fix src/ tests/

# Type check
mypy src/
```

## License

MIT License - see [LICENSE](LICENSE) file.
