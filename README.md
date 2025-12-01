# roth_conversions

## Setup Instructions

Follow these steps to set up your environment, install the required packages using `uv`, and use the `.ipynb` files in VS Code.

### Prerequisites

- Python 3.9+ installed and added to your PATH
- Visual Studio Code installed with the Python and Jupyter extensions
- `uv` installed globally (if not, install it using `pip install uv` or `curl` as described below)

### 1. Create and Activate a Virtual Environment Using `uv`

```pwsh
# Create a virtual environment named .venv using uv
uv venv create .venv

# Activate the virtual environment (PowerShell)
.\.venv\Scripts\Activate.ps1

# If activation is blocked, run this command first:
Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force
.\.venv\Scripts\Activate.ps1
```

### 2. Install Required Packages

You can install `uv` and other dependencies using either `pip` or `curl`. Choose the method based on your system setup:

#### Option 1: Install Using `pip`

Use this method if `pip` is already installed on your system:

```pwsh
# Upgrade pip
pip install --upgrade pip

# Install required packages
pip install jupyter notebook numpy pandas matplotlib uv
```

#### Option 2: Install Using `curl`

Use this method if `pip` is not installed or you prefer to install it manually:

```pwsh
# Download and install pip
curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
python get-pip.py

# Install required packages
pip install jupyter notebook numpy pandas matplotlib uv
```

### 3. Sync Packages Using `pyproject.toml`

Ensure that your `pyproject.toml` file specifies the required dependencies. Then, sync the packages into your virtual environment:

```pwsh
# Sync packages defined in pyproject.toml
uv sync
```

### 4. Open and Run `.ipynb` Files in VS Code

1. Open Visual Studio Code.
2. Install the Python and Jupyter extensions if not already installed.
3. Open the `.ipynb` file you want to work with.
4. Select the Python interpreter associated with your virtual environment:
   - Press `Ctrl+Shift+P` to open the Command Palette.
   - Search for and select `Python: Select Interpreter`.
   - Choose the interpreter located in `.venv`.
5. Run the notebook cells using the `Run` button or `Shift+Enter`.

### Notes

- If `uv` is not installed globally, install it first using `pip install uv` or the `curl` method described above.
- Ensure the virtual environment is activated whenever you work on this project.
- If notebooks cannot find packages, verify that the kernel matches the activated virtual environment.

### Notebooks

- Started with roth_conversion_optimizer.ibynb
- Improved with retirement_story.ipynb
- Currently working on retirement_visual.ipynb
