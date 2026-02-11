# roth-conversions

## Setup Instructions

Follow these steps to set up your environment and install the required packages using `uv`.

### Prerequisites

- Python 3.12+ installed and added to your PATH
- Visual Studio Code installed with the Python and Jupyter extensions

- `uv` installed globally

    ```bash
    # from your default terminal window (typically bash)
    powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
    ```
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

### 2. Sync Packages Using `pyproject.toml`

Ensure that your `pyproject.toml` file specifies the required dependencies. Then, install them into your virtual environment:

```pwsh
uv sync
```

### Notebooks

The primary supported interface is the CLI described below.

Legacy notebooks are kept for exploration and historical context under `notebooks_archive/` (not maintained for interactive use).

## Library + CLI (non-notebook)

This repo now includes a refactored, library-style package in `roth_conversions/` (no `exec`, no notebook parsing).

The primary CLI is now `retirement-toolkit` (namespaced to make room for additional use-cases).

Additional notebook-derived config templates (for migration) live at:

- `configs/retirement_story_config.template.toml`
- `configs/archive/retirement_visual_config.template.toml`
- `configs/archive/roth_conversion_optimizer_config.template.toml`

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

Compatibility entrypoint (old CLI name; still works):

```pwsh
roth-conversions --config configs/retirement_config.template.toml three-paths
```

### Run all scenarios

This repo includes a set of ready-to-run scenario configs under `configs/` (see `configs/README.md`).

Run all _scenario_ configs (recommended):

```pwsh
New-Item -ItemType Directory -Force outputs/scenarios | Out-Null

Get-ChildItem configs -Filter "retirement_config.scenario_*.toml" | Sort-Object Name | ForEach-Object {
  $cfg = $_.FullName
  $base = $_.BaseName
  Write-Host "Running $($_.Name)"

  uv run retirement-toolkit roth --config $cfg three-paths | Out-Null
  uv run retirement-toolkit roth --config $cfg report --format md --out ("outputs/scenarios/$base.md")
}
```

Run _all_ ready-to-run configs (includes `minimal_roth` and `example`, excludes the canonical template):

```pwsh
New-Item -ItemType Directory -Force outputs/scenarios | Out-Null

Get-ChildItem configs -Filter "retirement_config*.toml" |
  Where-Object { $_.Name -ne "retirement_config.template.toml" } |
  Sort-Object Name |
  ForEach-Object {
    $cfg = $_.FullName
    $base = $_.BaseName
    Write-Host "Running $($_.Name)"

    uv run retirement-toolkit roth --config $cfg three-paths | Out-Null
    uv run retirement-toolkit roth --config $cfg report --format md --out ("outputs/scenarios/$base.md")
  }
```

### Run unit tests

```pwsh
python -m unittest discover -s tests -p "test_*.py" -q
```
