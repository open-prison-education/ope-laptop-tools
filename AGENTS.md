# OPE Laptop Tools - Agent Instructions

## Cursor Cloud specific instructions

### Project overview

This is a **Windows-only** Python 3.12 project that builds tools for managing laptops for incarcerated students. All applications (`credential.exe`, `mgmt.exe`, `OPEService.exe`, `sshot.exe`) depend heavily on Win32 APIs and cannot run on Linux.

### Linux dev environment limitations

- **pywin32**, **winsys**, and **firmware_variables** cannot be installed on Linux. **wmi** and **pyad** install but fail at import time because they depend on pywin32/Windows.
- The applications cannot be executed on Linux since they use `ctypes.windll`, `win32serviceutil`, `win32gui`, `win32api`, Windows Registry, Group Policy, and other Windows-only APIs at module level.
- Static analysis (syntax checks, linting) and cross-platform dependency installation are the main development activities possible on Linux.

### Running checks

- **Virtual environment**: `source venv/bin/activate` (Python 3.12, created at `/workspace/venv`)
- **Syntax check all files**: `python -m py_compile <file.py>` for each `.py` file
- **Lint**: `ruff check .` (236 pre-existing issues; no linter config file exists in the repo)
- **Dependencies**: `pip install -r modules.txt` — expect failures for Windows-only packages; cross-platform packages install fine

### Key files

- `modules.txt` — pip requirements (no version pins); use `pip install -r modules.txt` to install
- `credential/credential_config.json` — main config for the credentialing app
- `build_svc.py` — PyInstaller build script for OPEService
- All `.cmd` files are Windows batch scripts for building/installing

### No automated tests

This codebase has no test suite. There are no unit tests, integration tests, or CI/CD configuration.
