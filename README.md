<p align="center">
  <img src="assets/banner.png" alt="Foldify Banner" width="100%">
</p>

<p align="center">
  <img src="assets/Icon.png" alt="Foldify Icon" width="80">
</p>

<h1 align="center">Foldify</h1>

<p align="center">
  <strong>AI-powered local file organizer — sort your files with rules, patterns, and local LLMs.</strong>
</p>

<p align="center">
  <a href="https://github.com/YounessBerkia/foldify/actions/workflows/ci.yml">
    <img src="https://github.com/YounessBerkia/foldify/actions/workflows/ci.yml/badge.svg" alt="CI">
  </a>
  <a href="https://www.python.org/downloads/">
    <img src="https://img.shields.io/badge/python-3.10%20|%203.11%20|%203.12-blue" alt="Python">
  </a>
  <a href="LICENSE">
    <img src="https://img.shields.io/badge/license-MIT-green" alt="License">
  </a>
  <img src="https://img.shields.io/badge/code%20style-black-000000" alt="Code style: black">
  <img src="https://img.shields.io/badge/linting-ruff-orange" alt="Linting: ruff">
  <img src="https://img.shields.io/badge/AI-Ollama%20(local)-purple" alt="AI: Ollama">
</p>

---

![Foldify Demo](assets/demo.gif)

## What is Foldify?

Foldify organizes your files automatically using a layered approach: fast rule-based matching first (filename, extension, content, size, date, regex), with a local AI model as a fallback for anything ambiguous. Everything runs **100% locally** — no cloud, no subscriptions, no privacy trade-offs.

## Features

| | |
|---|---|
| **Profile-based config** | Define multiple organization schemes in YAML — one for school, one for work, one for your desktop. |
| **Hierarchical rules** | Seven rule types evaluated in order: `filename_contains`, `extension`, `content_contains`, `size_range`, `date_range`, `regex`, `ai_match`. |
| **Local AI fallback** | Uses [Ollama](https://ollama.ai) models (`qwen3:8b`, `phi4:mini`, or any custom model) for smart classification when rules don't match. |
| **Safe by default** | Dry-run preview, automatic conflict backups, and full rollback support. |
| **Multi-source** | Scan multiple directories at once with include/exclude glob patterns. |
| **Privacy-first** | All AI inference runs on your machine. Nothing leaves your device. |

## Demo

> Coming soon — see `assets/demo.gif` once the recording is added.

## Installation

```bash
git clone https://github.com/YounessBerkia/foldify.git
cd foldify
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
```

## Quick Start

```bash
# Set up config directories
foldify init

# See available profile templates
foldify init --list-templates

# Create a profile from a template
foldify init --template school --profile school

# Preview what would happen (no files moved)
foldify run --profile school --dry-run

# Adjust preview colors to your terminal background
foldify run --profile school --dry-run --theme dark
foldify run --profile school --dry-run --theme light

# Execute
foldify run --profile school
```

## Configuration

Profiles live in `~/.config/foldify/profiles/` as YAML files.

```yaml
name: school
sources:
  - path: ~/Downloads
    recursive: false

destinations:
  Math:
    path: ~/Documents/School/Math
    rules:
      - type: filename_contains
        keywords: [math, calculus, algebra]
      - type: extension
        extensions: [.pdf, .docx]

  Other:
    path: ~/Documents/School/Other
    rules:
      - type: ai_match
```

See [docs/CONFIGURATION.md](docs/CONFIGURATION.md) for the full profile reference and [examples/](examples/) for ready-to-use templates.

## AI Integration

Foldify uses [Ollama](https://ollama.ai) for optional local AI classification:

```bash
# Check Ollama status
foldify ai status

# Get setup instructions
foldify ai setup

# Use an AI-powered profile template
foldify init --template ai-smart --profile ai-smart
foldify run --profile ai-smart --dry-run
```

AI runs as a **fallback** — fast rule-based matching handles obvious cases first, and AI only kicks in for ambiguous files. You can also add explicit `ai_match` rules to force AI routing for specific destinations.

**Supported models:**

| Model | Size | Notes |
|---|---|---|
| `qwen3:8b` | ~5.5 GB | Recommended |
| `phi4:mini` | ~4 GB | Faster, lighter |
| Any Ollama model | — | Fully configurable |

## Requirements

- Python 3.10+
- [Ollama](https://ollama.ai) *(optional, for AI features)*

## Documentation

- [Configuration Guide](docs/CONFIGURATION.md)
- [Troubleshooting](docs/TROUBLESHOOTING.md)
- [Example Profiles](examples/README.md)
- [Contributing](CONTRIBUTING.md)

## Development

```bash
# Run tests
pytest

# Format
black src/ tests/

# Lint
ruff check --fix src/ tests/

# Type check
mypy src/
```

## Project Structure

```
foldify/
├── src/foldify/        # Main package
│   ├── config/         # YAML loading & validation
│   ├── core/           # Organizer, scanner, executor
│   ├── rules/          # Rule engine
│   ├── ai/             # Ollama client
│   └── utils/          # Helpers
├── examples/           # Sample profiles
├── tests/              # Test suite
└── docs/               # Documentation
```

## License

MIT — see [LICENSE](LICENSE).
