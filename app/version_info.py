import os
import subprocess
from datetime import datetime, timezone
from functools import lru_cache
from pathlib import Path

GITHUB_REPO = "https://github.com/mcandiav/expenses"


@lru_cache(maxsize=1)
def get_build_info() -> dict[str, str]:
    sha = (os.environ.get("APP_GIT_SHA") or "").strip()
    build_date = (os.environ.get("APP_BUILD_DATE") or "").strip()

    info_path = Path(__file__).with_name("build_info.py")
    if info_path.exists():
        ns: dict = {}
        exec(info_path.read_text(encoding="utf-8"), ns)  # noqa: S102
        sha = sha or str(ns.get("GIT_SHA", "")).strip()
        build_date = build_date or str(ns.get("BUILD_DATE", "")).strip()

    if not sha:
        sha = _git_short_sha() or "dev"

    if not build_date:
        build_date = _git_commit_date(sha) or datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC")

    return {
        "git_sha": sha,
        "build_date": build_date,
        "github_url": f"{GITHUB_REPO}/commit/{sha}" if sha not in ("dev", "unknown") else GITHUB_REPO,
    }


def format_sidebar_version() -> str:
    info = get_build_info()
    return f"`{info['git_sha']}` · {info['build_date']}"


def _git_short_sha() -> str | None:
    try:
        root = Path(__file__).resolve().parents[1]
        return (
            subprocess.check_output(
                ["git", "rev-parse", "--short", "HEAD"],
                cwd=root,
                stderr=subprocess.DEVNULL,
                text=True,
            )
            .strip()
        )
    except (OSError, subprocess.CalledProcessError):
        return None


def _git_commit_date(sha: str) -> str | None:
    try:
        root = Path(__file__).resolve().parents[1]
        raw = subprocess.check_output(
            ["git", "show", "-s", "--format=%ci", sha],
            cwd=root,
            stderr=subprocess.DEVNULL,
            text=True,
        ).strip()
        if not raw:
            return None
        dt = datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
        return dt.strftime("%Y-%m-%d %H:%M UTC")
    except (OSError, subprocess.CalledProcessError, ValueError):
        return None
