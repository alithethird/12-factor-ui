# Agent Guidelines for 12-factor-ui Repository

## Build, Lint, Test Commands

This is a Python Flet application with two directories: `flet_app/` and `new_app/` (with identical structure).

**Run the application:**
```bash
cd flet_app
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
flet run main.py
```

**Package for Linux:**
```bash
flet pack main.py --add-data "assets:assets" --name charm-gen
```

### Test Commands

The project uses **pytest** for unit and integration testing. All tests mock external commands (charmcraft, rockcraft) to avoid dependencies.

**Run all tests:**
```bash
cd flet_app
pytest tests -v
```

**Run only unit tests:**
```bash
pytest tests/unit -v
```

**Run only integration tests:**
```bash
pytest tests/integration -v
```

**Run a specific test file:**
```bash
pytest tests/unit/test_rockcraft_generator.py -v
```

**Run a specific test:**
```bash
pytest tests/unit/test_rockcraft_generator.py::test_init_stores_configuration -v
```

**Run tests with coverage report:**
```bash
pytest tests --cov=logic --cov-report=term-missing
```

**Run tests with detailed output (includes print statements):**
```bash
pytest tests -v -s
```

**Run tests with timeout (useful for detecting hangs):**
```bash
pytest tests --timeout=30
```

## Code Style Guidelines

### Imports
- Organize imports into three groups: standard library, third-party, then local (see examples in GenerateFiles.py)
- Use relative imports for local modules: `from .AccordionStep import AccordionStep`
- Use absolute imports for packages: `from logic.bundler import BundleArtifacts`

### Naming Conventions
- **Classes:** PascalCase (e.g., `ApplicationProcessor`, `SelectFramework`)
- **Functions/methods:** snake_case (e.g., `check_project`, `on_framework_select`)
- **Constants:** UPPER_CASE (e.g., `JOB_STORE`, `TEMP_STORAGE_PATH`)
- **Private methods:** prefix with underscore (e.g., `_check_flask`)

### Formatting & Type Hints
- Use Python 3.10+ match/case statements for framework selection patterns
- Add type hints for function parameters: `def _check_requirements(self, package_name: str)`
- Strings should use double quotes consistently
- Use f-strings for string formatting: `f"Framework: {fw_name}"`

### Error Handling
- Raise specific exceptions with descriptive messages: `raise ValueError("Project is missing requirements.txt")`
- Use try-catch blocks for file operations and external commands
- Add helpful error context when catching exceptions

### Architecture & State Management
- Pass `app_state` dictionary through UI components for shared state
- Use `app_state["update_form_data"]()` to update form state and trigger `page.update()`
- Separate UI logic (in `ui/`) from business logic (in `logic/`)
- Store global state in `state.py` (e.g., `JOB_STORE`, `TEMP_STORAGE_PATH`)

### UI Components (Flet)
- Extend `AccordionStep` base class for multi-step UI components
- Define event handlers as nested functions within component methods
- Use type hints for Flet controls: `e.control.data["id"]`
- Organize Flet widgets in logical Column/Row structures

### PR Requirements
- Include "why and what" of changes, not just file lists
- Follow [commit guidelines](https://discourse.canonical.com/t/commit-guidelines/148)
- Include QA steps to verify functionality locally at `http://localhost:8000/` if applicable
