"""Integration bridge and adapter for core clipping engines.

Provides seamless compatibility with installed clipping skills (such as beyondgtaclips)
while delivering standalone execution using the SaimGTA6Clipping pipeline.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

KNOWN_SKILL_PATHS = [
    Path.home() / ".gemini" / "config" / "skills" / "beyondgtaclips",
    Path.home() / ".beyondgtaclips",
    Path.home() / "beyondgtaclips",
]


def find_beyondgtaclips_root() -> Path | None:
    """Locates an installed beyondgtaclips repository if present on the local machine."""
    for p in KNOWN_SKILL_PATHS:
        if p.exists() and (p / "scripts" / "beyondgtaclips.py").exists():
            return p
    return None


def is_beyondgtaclips_available() -> bool:
    return find_beyondgtaclips_root() is not None


def run_beyondgtaclips_cmd(args: list[str]) -> subprocess.CompletedProcess:
    """Executes a command against the local beyondgtaclips CLI if installed."""
    root = find_beyondgtaclips_root()
    if not root:
        raise FileNotFoundError(
            "beyondgtaclips is not installed locally. Run 'python scripts/bootstrap.py' to configure tools."
        )
    cli_script = root / "scripts" / "beyondgtaclips.py"
    cmd = [sys.executable, str(cli_script)] + args
    return subprocess.run(cmd, capture_output=True, text=True)
