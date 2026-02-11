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

### 3. (Optional): PowerShell profile helper for activating the venv

This is a PowerShell function you can add to your personal `$PROFILE` so you can activate a repo's venv with a single command. 

1. Add the function below to your profile file (create it if it does not exist & then restart PowerShell),
2. Ensure the BasePath reflects your local Git repository location

```pwsh
function venv {
  param(
    [Parameter(Mandatory = $true)]
    [string]$RepoName,

    [string]$BasePath = "$HOME\GitLocal"
  )

  $repoPath = Join-Path $BasePath $RepoName
  $activate = Join-Path $repoPath ".venv\Scripts\Activate.ps1"

  if (-not (Test-Path $activate)) {
    throw "No venv found at $repoPath"
  }

  Push-Location $repoPath
  & $activate
}
```

Usage:

```pwsh
venv roth-conversions
```

### 4. Run unit tests

```pwsh
python -m unittest discover -s tests -p "test_*.py" -q
```

## Library + CLI (non-notebook primary interface)

This repo now includes a refactored, library-style package in `roth_conversions/` (no `exec`, no notebook parsing).

The primary CLI is now `retirement-toolkit` (namespaced to make room for additional use-cases).

Additional notebook-derived config templates (for migration) live at:

- `configs/retirement_story_config.template.toml`
- `configs/archive/retirement_visual_config.template.toml`
- `configs/archive/roth_conversion_optimizer_config.template.toml`

### Run the CLI

Using `uv` (recommended). Ordered from quickest/simplest to most complex, with each explanation as a code comment:

```pwsh
# 1) List available report sections (fastest). Discovery step before targeted reports.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --list-sections

# 2) Run the baseline three-paths analysis. Quick end-to-end sanity check.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml three-paths

# 3) Run the 32% bracket conversion path. Compact stress check of tax logic.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml 32pct

# 4) Run the home purchase scenario. Exercises optional scenario logic.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml home --down-payment 200000 --purchase-year 2027

# 5) Generate a full Markdown report. Shareable review artifact.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format md --out outputs/report.md

# 6) Generate a Markdown report with included sections only. Trims output.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format md --include executive-summary --include three-paths-a-b-c --out outputs/report.md

# 7) Generate a Markdown report excluding a section. Mostly full report, minus a topic.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format md --exclude home-purchase-scenario --out outputs/report.md

# 8) Generate a full PDF report (most work). Slowest output for finalized deliverable.
uv run retirement-toolkit roth --config configs/retirement_config.template.toml report --format pdf --out outputs/report.pdf
```

If `uv run retirement-toolkit ...` fails on your machine, you can always run the CLI via module execution:

```pwsh
python -m retirement_toolkit.cli roth --config configs/retirement_config.template.toml report --format md --out outputs/report.md
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

### Archive of devops repo features

- Legacy notebooks are kept for exploration and historical context under `notebooks_archive/` (not maintained for interactive use).

- Compatibility entrypoint (old CLI name; no longer works as uv sync doesn't "package" it):

    ```pwsh
    # for reference - this is how the cli used to be called (in the devops repo)
    roth-conversions --config configs/retirement_config.template.toml three-paths
    ```
