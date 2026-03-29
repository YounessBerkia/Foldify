# Contributing to File Organizer

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/YounesBerkia/Local-AI-Folder-Organizer.git
   cd Local-AI-Folder-Organizer
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or
   venv\Scripts\activate  # Windows
   ```

3. **Install development dependencies:**
   ```bash
   pip install -e ".[dev]"
   ```

4. **Verify setup:**
   ```bash
   pytest
   ```

## Project Structure

```
file-organizer/
├── src/file_organizer/    # Main source code
│   ├── config/            # Configuration handling
│   ├── core/              # Core organizer logic
│   ├── rules/             # Rule engine
│   ├── ai/                # AI integration
│   └── utils/             # Utilities
├── tests/                 # Test suite
│   ├── unit/              # Unit tests
│   └── integration/       # Integration tests
├── examples/              # Example profiles
└── docs/                  # Documentation
```

## Code Style

We use:
- **black** for code formatting
- **ruff** for linting
- **mypy** for type checking

Run checks before committing:
```bash
# Format code
black src/ tests/

# Lint
ruff check --fix src/ tests/

# Type check
mypy src/

# Run tests
pytest -q
```

## Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=file_organizer

# Run specific test file
pytest tests/unit/test_config_models.py

# Run with verbose output
pytest -v
```

### Writing Tests

- Place unit tests in `tests/unit/`
- Place integration tests in `tests/integration/`
- Use fixtures from `tests/conftest.py`
- Aim for >80% code coverage

Example test:
```python
def test_feature(temp_dir):
    """Test description."""
    # Arrange
    source = temp_dir / "source.txt"
    source.write_text("content")

    # Act
    result = process_file(source)

    # Assert
    assert result is True
```

## Pull Request Process

1. **Create a branch:**
   ```bash
   git checkout -b feature/your-feature-name
   ```

2. **Make your changes:**
   - Write code
   - Add tests
   - Update documentation

3. **Run quality checks:**
   ```bash
   black src/ tests/
   ruff check src/ tests/
   mypy src/
   pytest -q
   ```

4. **Commit your changes:**
   ```bash
   git add .
   git commit -m "feat: add new feature"
   ```

   Follow [Conventional Commits](https://www.conventionalcommits.org/):
   - `feat:` New feature
   - `fix:` Bug fix
   - `docs:` Documentation
   - `test:` Tests
   - `refactor:` Code refactoring
   - `style:` Formatting
   - `chore:` Maintenance

5. **Push and create PR:**
   ```bash
   git push origin feature/your-feature-name
   ```

6. **PR Requirements:**
   - Clear description
   - Tests included
   - Documentation updated
   - Checks passing

## Adding New Rule Types

To add a new rule type:

1. **Add to `Rule` model** (`src/file_organizer/config/models.py`):
   ```python
   @dataclass
   class Rule:
       # ... existing fields
       new_field: Optional[str] = None
   ```

2. **Implement in engine** (`src/file_organizer/rules/engine.py`):
   ```python
   def _match_new_type(self, file_path, rule, destination):
       """Match new rule type."""
       # Implementation
       if matches:
           return RuleMatchResult(
               matched=True,
               destination=destination,
               rule=rule,
               reason="Matched new type",
           )
       return RuleMatchResult(matched=False)
   ```

3. **Add validation** (`src/file_organizer/config/validator.py`):
   ```python
   def validate_rule(rule, index, dest_name):
       # ...
       if rule.type == "new_type" and not rule.new_field:
           warnings_list.append("new_type requires new_field")
   ```

4. **Add tests** (`tests/unit/test_rules_engine.py`):
   ```python
   def test_new_rule_type(temp_dir, engine):
       """Test new rule type."""
       rule = Rule(type="new_type", new_field="value")
       # Test implementation
   ```

5. **Update documentation** (`docs/CONFIGURATION.md`)

## Adding New AI Features

1. **Extend AI client** (`src/file_organizer/ai/client.py`)
2. **Update configuration** (`src/file_organizer/config/models.py`)
3. **Add CLI commands** (`src/file_organizer/cli.py`)
4. **Write tests**
5. **Document in TROUBLESHOOTING.md**

## Documentation

- Keep README.md updated
- Update CONFIGURATION.md for new features
- Update TROUBLESHOOTING.md for common issues
- Add docstrings to public APIs

## Reporting Issues

When reporting bugs:

1. **Search existing issues first**
2. **Use issue templates**
3. **Include:**
   - Python version: `python --version`
   - OS: `uname -a`
   - Package version: `pip show file-organizer`
   - Minimal reproducible example
   - Error message / stack trace
   - Profile configuration (sanitized)

## Code of Conduct

- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive feedback
- Respect differing viewpoints

## Questions?

- Open an issue for questions
- Join discussions
- Check existing documentation

Thank you for contributing!
