# Tests

## Structure

- `unit/` - Unit tests for individual modules
- `integration/` - Integration tests for full workflows
- `fixtures/` - Sample files for testing

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=foldify

# Run specific test file
pytest tests/unit/test_config.py

# Run with verbose output
pytest -v
```