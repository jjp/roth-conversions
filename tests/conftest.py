from __future__ import annotations

import sys
from pathlib import Path

# Ensure the repo root is importable under pytest.
# Some runners/import modes don't include CWD on sys.path, which breaks `import roth_conversions`.
_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))
