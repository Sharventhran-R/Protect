# Development & Operations Guide

This guide describes how to configure the local development environment, run tests, enforce code standards, and troubleshoot issues on Windows using PowerShell.

---

## 1. Prerequisites

- **Operating System**: Windows 10/11 (x64)
- **Shell**: PowerShell (v5.1+ or PowerShell 7)
- **Python**: Python 3.12+ (Host environment verified on Python 3.14.6)
- **Hardware**: Standard x86_64 CPU (No GPU required)

---

## 2. Environment Setup (PowerShell)

### Step 1: Create the Local Virtual Environment
From the project root (`d:\PROJECTS\Protect`):

```powershell
python -m venv .venv
```

### Step 2: Configure PowerShell Execution Policy (If restricted)
If script execution is disabled on your system:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned
```

### Step 3: Activate the Virtual Environment
```powershell
.\.venv\Scripts\Activate.ps1
```

Verify the active interpreter:
```powershell
Get-Command python | Select-Object -ExpandProperty Source
```
*Expected: Points to `d:\PROJECTS\Protect\.venv\Scripts\python.exe`.*

### Step 4: Install Dependencies in Editable Mode
Install the core package along with all development and quality tools:
```powershell
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install -e ".[dev]"
```

---

## 3. Code Quality & Verification Commands

All quality gates must pass before submitting any code:

### 3.1 Run Unit Tests (Pytest)
```powershell
.\.venv\Scripts\pytest.exe
```
Verbose output with summary:
```powershell
.\.venv\Scripts\pytest.exe -v
```

### 3.2 Check Code Formatting (Ruff Format)
```powershell
.\.venv\Scripts\ruff.exe format --check .
```
To automatically apply formatting:
```powershell
.\.venv\Scripts\ruff.exe format .
```

### 3.3 Lint Code (Ruff Check)
```powershell
.\.venv\Scripts\ruff.exe check .
```
To automatically fix safe lint issues:
```powershell
.\.venv\Scripts\ruff.exe check --fix .
```

### 3.4 Strict Static Type Analysis (Mypy)
```powershell
.\.venv\Scripts\mypy.exe src tests
```

### 3.5 Verify Package Import
```powershell
.\.venv\Scripts\python.exe -c "import home_guard; print(f'home-guard {home_guard.__version__}: {home_guard.get_health_status().status}')"
```

---

## 4. Git Policy Reminder

- **Human-Owned Git**: AI coding agents are strictly prohibited from running any Git command (`commit`, `add`, `push`, `branch`, etc.) or altering `.git` files.
- All version control operations must be executed manually by the developer.

---

## 5. Troubleshooting Guide

### Issue: `activate.ps1 cannot be loaded because running scripts is disabled`
- **Solution**: Run `Set-ExecutionPolicy -Scope Process -ExecutionPolicy RemoteSigned` in your current PowerShell session. Alternatively, call the executables directly via `.\.venv\Scripts\<tool>.exe`.

### Issue: `ModuleNotFoundError: No module named 'home_guard'`
- **Solution**: Ensure you installed the package in editable mode via `.\.venv\Scripts\python.exe -m pip install -e ".[dev]"`.

### Issue: `Ruff` or `Mypy` command not recognized
- **Solution**: Ensure your virtual environment is activated, or call them directly using `.\.venv\Scripts\ruff.exe` and `.\.venv\Scripts\mypy.exe`.
