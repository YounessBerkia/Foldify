# Documentation

Additional documentation for File Organizer.

## Available Guides

- [Configuration Guide](CONFIGURATION.md) - Learn how to write profiles
- [Troubleshooting Guide](TROUBLESHOOTING.md) - Common issues and solutions

## Profile Examples

See the [`examples/`](../examples/) directory for complete profile examples:

- `school.yaml.example` - Organize school files
- `work.yaml.example` - Organize work documents
- `desktop-cleanup.yaml.example` - Clean up old downloads
- `ai-smart.yaml.example` - AI-powered classification

## Quick Reference

### Command Line

```bash
# Initialize configuration
file-organizer init

# Create profile from template
file-organizer init --template school --profile myschool

# List profiles
file-organizer list

# Validate profile
file-organizer validate myschool

# Preview changes (dry run)
file-organizer run --profile myschool --dry-run

# Theme the preview output for your terminal background:
file-organizer run --profile myschool --dry-run --theme dark
file-organizer run --profile myschool --dry-run --theme light

# Execute organization
file-organizer run --profile myschool

# Check AI status
file-organizer ai status
```

Notes:
- In dry-run mode, the CLI prints a decision-time summary (how long it took to scan + match + (optionally) consult AI) before asking to execute.

### Rule Types

| Type | Purpose | Example |
|------|---------|---------|
| `filename_contains` | Match keywords in filename | `keywords: ["invoice"]` |
| `extension` | Match file extensions | `extensions: [".pdf"]` |
| `content_contains` | Match text in file content | `keywords: ["confidential"]` |
| `size_range` | Match file size | `min_size: 1048576` |
| `date_range` | Match file age | `older_than_days: 30` |
| `regex` | Match filename pattern | `pattern: "report_\d{4}"` |
| `ai_match` | Let Ollama choose the best destination | `type: ai_match` |

### AI Configuration

```yaml
ai:
  enabled: true
  model: qwen3:8b
  categories: ["Work", "Personal", "Academic"]
  confidence_threshold: 0.7
  max_content_length: 2000
  cache_results: true
```

AI runs after normal rules unless you explicitly add `ai_match` to a destination. This makes it useful as a fallback for ambiguous files while keeping obvious matches fast.

### Options

```yaml
options:
  dry_run: false
  backup_conflicts: true
  log_level: INFO
  log_file: ~/.local/share/file-organizer/app.log
  max_workers: 4
```
