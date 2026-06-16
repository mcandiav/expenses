"""Genera app/build_info.py con SHA y fecha para despliegues Docker."""

import subprocess
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "app" / "build_info.py"


def main() -> None:
    try:
        sha = subprocess.check_output(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=ROOT,
            text=True,
        ).strip()
    except (OSError, subprocess.CalledProcessError):
        sha = "unknown"

    build_date = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    OUT.write_text(
        f'GIT_SHA = "{sha}"\nBUILD_DATE = "{build_date}"\n',
        encoding="utf-8",
    )
    print(f"build_info -> {sha} @ {build_date}")


if __name__ == "__main__":
    main()
