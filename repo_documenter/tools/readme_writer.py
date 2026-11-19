from __future__ import annotations

import hashlib
import json
import os
import shutil
import tempfile
from datetime import datetime, timezone
from difflib import unified_diff
from pathlib import Path
from typing import Any

MAX_README_BYTES = 200_000


def _safe_repository_path(value: str) -> Path:
    repo_path = Path(value).expanduser().resolve()
    if not repo_path.is_dir():
        raise ValueError(f"Repository directory does not exist: {repo_path}")
    return repo_path


def _read_current_readme(target: Path) -> str:
    if target.is_symlink():
        raise ValueError("README.md is a symbolic link; refusing to follow it.")
    if target.exists() and not target.is_file():
        raise ValueError("README.md exists but is not a regular file.")
    return target.read_text(encoding="utf-8") if target.exists() else ""


def prepare_readme_review(node_input: dict[str, Any]) -> dict[str, Any]:
    """Build a review bundle without modifying the repository."""
    repo_path = _safe_repository_path(node_input["repository_path"])
    markdown = node_input["markdown"]
    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("The documentation agent returned empty Markdown.")

    proposed = markdown.rstrip() + "\n"
    if len(proposed.encode("utf-8")) > MAX_README_BYTES:
        raise ValueError("Generated README is larger than the 200 KB safety limit.")

    target = repo_path / "README.md"
    current = _read_current_readme(target)
    diff = "".join(
        unified_diff(
            current.splitlines(keepends=True),
            proposed.splitlines(keepends=True),
            fromfile="README.md (current)",
            tofile="README.md (proposed)",
        )
    )

    return {
        "repository_path": str(repo_path),
        "readme_path": str(target),
        "old_content": current,
        "proposed_content": proposed,
        "diff": diff,
        "readme_existed": target.exists(),
        "old_sha256": hashlib.sha256(current.encode("utf-8")).hexdigest(),
        "proposed_sha256": hashlib.sha256(proposed.encode("utf-8")).hexdigest(),
    }


def commit_readme(node_input: str) -> dict[str, str]:
    """ADK commit node. It writes only when an explicit approval is present."""
    request = json.loads(node_input)
    if request.get("approved") is not True:
        return {"status": "rejected", "message": "README was not changed."}

    review = request["review"]
    repo_path = _safe_repository_path(review["repository_path"])
    target = repo_path / "README.md"
    if target.is_symlink():
        raise ValueError("README.md became a symbolic link after review; refusing to write.")
    current = _read_current_readme(target)
    current_hash = hashlib.sha256(current.encode("utf-8")).hexdigest()
    if current_hash != review["old_sha256"]:
        raise RuntimeError(
            "README.md changed after the review was generated. Generate a new review before accepting."
        )

    proposed = review["proposed_content"]
    if not isinstance(proposed, str) or not proposed.strip():
        raise ValueError("The proposed README is empty.")
    if len(proposed.encode("utf-8")) > MAX_README_BYTES:
        raise ValueError("Generated README is larger than the 200 KB safety limit.")

    backup_path: Path | None = None
    if target.exists():
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        candidate = repo_path / f"README.md.bak.{stamp}"
        suffix = 1
        while candidate.exists():
            candidate = repo_path / f"README.md.bak.{stamp}.{suffix}"
            suffix += 1
        shutil.copy2(target, candidate)
        backup_path = candidate

    fd, temp_name = tempfile.mkstemp(prefix=".README.md.", suffix=".tmp", dir=repo_path)
    temp_path = Path(temp_name)
    try:
        with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(proposed)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temp_path, target)
    except Exception:
        temp_path.unlink(missing_ok=True)
        raise

    return {
        "status": "success",
        "message": "README.md was updated after approval.",
        "readme_path": str(target),
        "backup_path": str(backup_path) if backup_path else "",
    }
