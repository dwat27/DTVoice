# Tests

## OVERVIEW
pytest test suite with fixtures for temp workspace and config patching.

## STRUCTURE
```
tests/
├── __init__.py
├── conftest.py              # Fixtures
├── test_config.py           # 9 tests - config module
├── test_history.py          # 14 tests - TranscriptionHistory
└── test_model_loader.py     # 8 tests - ModelLoader
```

## CONVENTIONS
- **Class-based**: `TestClassName` with `test_*` methods
- **Fixtures**: Session-scoped `temp_workspace`, auto-used `clean_env` (patches `config.CONFIG_DIR`)
- **Import errors**: Use `pytest.skip()` for graceful degradation
- **Markers**: `slow`, `integration` defined in pytest.ini

## RUN TESTS
```bash
pytest tests/ -v
```

## KEY FIXTURES
- `temp_workspace`: Session-scoped temp directory
- `clean_env`: Auto-patches `config.CONFIG_DIR` to temp for each test