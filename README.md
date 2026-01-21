# roth_conversions

## Setup Instructions

Follow these steps to set up your environment, install the required packages using `uv`, and use the `.ipynb` files in VS Code.

### Prerequisites

- Python 3.9+ installed and added to your PATH
- Visual Studio Code installed with the Python and Jupyter extensions

- `uv` installed globally
  - powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
  - outside of VS Code, from a terminal run "where.exe uv" to confirm the installation
  - fully exit VS Code and restart (or the uv command will be unfindable)

### 1. Create and Activate a Virtual Environment Using `uv`

```pwsh
# Create a virtual environment named .venv using uv
uv venv .venv

# Activate the virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# If activation is blocked, run this command first:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1
```

### 2. Install Required Packages

You can install `uv` and other dependencies using either `pip` or `curl`. Choose the method based on your system setup:

### 3. Sync Packages Using `pyproject.toml`

Ensure that your `pyproject.toml` file specifies the required dependencies. Then, sync the packages into your virtual environment:

```pwsh
# Sync packages defined in pyproject.toml
uv sync
```

### 4. Open and Run "retirement_story" `.ipynb` Files in VS Code

1. Open Visual Studio Code.
2. Install the Python and Jupyter extensions if not already installed.
3. Open the `.ipynb` file you want to work with.
4. Select the Python interpreter associated with your virtual environment:
   - Press `Ctrl+Shift+P` to open the Command Palette.
   - Search for and select `Python: Select Interpreter`.
   - Choose the interpreter located in `.venv`.
5. Run the notebook cells using the `Run` button or `Shift+Enter`.

### Notebooks

- Started with roth_conversion_optimizer.ibynb
- Improved with retirement_story.ipynb
- Currently working on retirement_visual.ipynb

## Library + CLI (non-notebook)

This repo now includes a refactored, library-style package in `roth_conversions/` (no `exec`, no notebook parsing).

The primary CLI is now `retirement-toolkit` (namespaced to make room for additional use-cases).

Additional notebook-derived config templates (for migration) live at:

- `configs/retirement_story_config.template.toml`
- `configs/retirement_visual_config.template.toml`
- `configs/roth_conversion_optimizer_config.template.toml`

### Run the CLI

Using `uv` (recommended):

```pwsh
uv run retirement-toolkit roth --config configs/retirement_config.template.toml three-paths
uv run retirement-toolkit roth --config configs/retirement_config.template.toml 32pct
uv run retirement-toolkit roth --config configs/retirement_config.template.toml home --down-payment 200000 --purchase-year 2027
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format md --out outputs/report.md
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format pdf --out outputs/report.pdf

# List available report sections
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --list-sections

# Include only specific sections (keys are shown by --list-sections)
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format md --include executive-summary --include three-paths-a-b-c --out outputs/report.md

# Exclude a section
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format md --exclude home-purchase-scenario --out outputs/report.md
```

If `uv run retirement-toolkit ...` fails on your machine, you can always run the CLI via module execution:

```pwsh
python -m retirement_toolkit.cli roth --config configs/retirement_config.template.toml report --format md --out outputs/report.md
```

Compatibility entrypoint (old name; still works):

```pwsh
roth-conversions --config configs/retirement_config.template.toml three-paths
python -m roth_conversions.cli --config configs/retirement_config.template.toml three-paths
```

### Run unit tests

```pwsh
python -m unittest discover -s tests -p "test_*.py" -q
```
