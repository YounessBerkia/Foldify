# Configuration Guide

Learn how to create and customize Foldify profiles.

## Table of Contents

- [Profile Structure](#profile-structure)
- [Sources](#sources)
- [Destinations](#destinations)
- [Rules](#rules)
- [AI Configuration](#ai-configuration)
- [Options](#options)
- [Examples](#examples)

## Profile Structure

A profile is a YAML file that defines:

```yaml
name: my_profile              # Profile identifier
version: "1.0"                # Profile version
description: "Description"    # Optional description

sources:                      # Where to scan for files
  - ...

destinations:                 # Where to organize files
  ...

ai:                           # AI configuration (optional)
  ...

options:                      # Global options
  ...
```

## Sources

Define directories to scan:

```yaml
sources:
  - path: ~/Downloads
    recursive: true
    include_patterns: ["*.pdf", "*.docx"]
    exclude_patterns: [".DS_Store", "*.tmp"]
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | required | Directory to scan (supports `~` for home) |
| `recursive` | boolean | `true` | Scan subdirectories |
| `include_patterns` | list | `["*"]` | File patterns to include |
| `exclude_patterns` | list | `[]` | File patterns to exclude |

### Pattern Syntax

- `*` - Match any characters except `/`
- `?` - Match single character
- `**` - Match any directories (if supported)
- `*.pdf` - All PDF files
- `report_*` - Files starting with "report_"

## Destinations

Define where matched files go:

```yaml
destinations:
  Math:
    path: ~/Documents/School/Math
    create_if_missing: true
    rules:
      - type: filename_contains
        keywords: ["math", "algebra", "calculus"]
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `path` | string | required | Destination directory |
| `create_if_missing` | boolean | `true` | Create directory if it doesn't exist |
| `rules` | list | `[]` | Rules for matching files |

## Rules

Rules are evaluated in order. The first match wins.

### filename_contains

Match files with specific keywords in their names:

```yaml
rules:
  - type: filename_contains
    keywords: ["invoice", "bill", "receipt"]
```

### extension

Match files by extension:

```yaml
rules:
  - type: extension
    extensions: [".pdf", ".docx", ".txt"]
```

Note: Extensions can be specified with or without the leading dot.

### content_contains

Match files containing specific text (scans file content):

```yaml
rules:
  - type: content_contains
    keywords: ["confidential", "private"]
```

**Note:** This reads file contents. Supported formats:
- Plain text (.txt, .md, .csv, etc.)
- PDF (.pdf) - requires pypdf
- Word (.docx) - requires python-docx

### size_range

Match files by size:

```yaml
rules:
  - type: size_range
    min_size: 1048576      # 1 MB in bytes
    max_size: 104857600    # 100 MB in bytes
```

| Field | Type | Description |
|-------|------|-------------|
| `min_size` | integer | Minimum file size in bytes |
| `max_size` | integer | Maximum file size in bytes |

### date_range

Match files by modification date:

```yaml
rules:
  - type: date_range
    older_than_days: 30     # Files older than 30 days
    newer_than_days: 365    # Files newer than 1 year
```

Useful for archiving old files or processing recent downloads.

### regex

Match filenames using regular expressions:

```yaml
rules:
  - type: regex
    pattern: "report_\d{4}-\d{2}-\d{2}"
```

### ai_match

Let Ollama choose the best destination from the configured categories:

```yaml
rules:
  - type: ai_match
    threshold: 0.75
```

Use this when the destination cannot be described well with simple filename or content rules. The optional `threshold` overrides the global AI confidence threshold for that rule.

## AI Configuration

Enable AI-powered classification with Ollama:

```yaml
ai:
  enabled: true
  model: qwen3:8b
  categories:
    - Academic
    - Business
    - Technical
    - Personal
  confidence_threshold: 0.7
  max_content_length: 2000
  cache_results: true
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `enabled` | boolean | `true` | Enable AI classification |
| `model` | string | `qwen3:8b` | Ollama model to use |
| `categories` | list | `[]` | Optional category hints for the AI |
| `confidence_threshold` | float | `0.7` | Minimum confidence (0.0-1.0) |
| `max_content_length` | integer | `2000` | Max characters to analyze |
| `cache_results` | boolean | `true` | Cache AI responses |

### How AI Classification Works

1. Normal rules are checked first
2. If no normal rule matches and AI is enabled, file content is sent to Ollama
3. Ollama chooses from the configured destinations and/or category hints
4. If an `ai_match` rule is present, its threshold can further control acceptance
5. Results are cached to avoid re-processing

If `categories` is empty, Foldify can still derive categories from the destination folder names.

### Recommended Models

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| `qwen3:8b` | ~5.5GB | Medium | Best |
| `phi4:mini` | ~4GB | Fast | Good |

## Options

Global settings for the organizer:

```yaml
options:
  dry_run: false
  backup_conflicts: true
  log_level: INFO
  log_file: ~/.local/share/foldify/organizer.log
  max_workers: 4
```

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| `dry_run` | boolean | `false` | Preview changes without executing |
| `backup_conflicts` | boolean | `true` | Backup existing files at destination |
| `log_level` | string | `INFO` | Logging level (DEBUG, INFO, WARNING, ERROR) |
| `log_file` | string | `null` | Path to log file (optional) |
| `max_workers` | integer | `4` | Parallel processing workers |

## Examples

### School Organization

```yaml
name: school
sources:
  - path: ~/Downloads
    include_patterns: ["*.pdf", "*.docx"]

destinations:
  Math:
    path: ~/Documents/School/Math
    rules:
      - type: filename_contains
        keywords: ["math", "algebra", "calculus"]

  Physics:
    path: ~/Documents/School/Physics
    rules:
      - type: filename_contains
        keywords: ["physics", "mechanics"]
      - type: extension
        extensions: [.py, .ipynb]
```

### Work Documents

```yaml
name: work
sources:
  - path: ~/Downloads

destinations:
  Invoices:
    path: ~/Documents/Work/Invoices
    rules:
      - type: filename_contains
        keywords: ["invoice", "rechnung", "INV-"]
      - type: content_contains
        keywords: ["invoice number", "total amount"]

  Reports:
    path: ~/Documents/Work/Reports
    rules:
      - type: date_range
        newer_than_days: 90
      - type: filename_contains
        keywords: ["report", "weekly", "monthly"]
```

### Desktop Cleanup

```yaml
name: cleanup
options:
  dry_run: true  # Always preview first!

sources:
  - path: ~/Desktop
    recursive: false
  - path: ~/Downloads
    recursive: true

destinations:
  OldDownloads:
    path: ~/Documents/Archive/Downloads
    rules:
      - type: date_range
        older_than_days: 30
      - type: extension
        extensions: [.zip, .dmg, .pkg]

  Screenshots:
    path: ~/Pictures/Screenshots
    rules:
      - type: filename_contains
        keywords: ["Screenshot", "Screen Shot"]
```

## Tips

1. **Start with dry_run**: Always test with `dry_run: true` first
2. **Order matters**: Rules are evaluated top-to-bottom
3. **Be specific**: More specific rules should come first
4. **Use backups**: Keep `backup_conflicts: true` until you're confident
5. **Check logs**: Enable `log_file` to track what happened
6. **AI as fallback**: Use rules for common cases, AI for ambiguous files
