from __future__ import annotations

import os
from pathlib import Path
from typing import Any


def write_readme(node_input: dict[str, Any]) -> str:
    """Write the generated README.md to the repository root.

    Input is the structured output from documentation_generator_agent.
    An existing README.md is backed up to README.md.bak before replacement.
    """
    print(f'readme input is {node_input}\n')
    repo_path = Path(node_input["repository_path"]).expanduser().resolve()
    markdown = node_input["markdown"]

    if not repo_path.is_dir():
        raise ValueError("The repository path no longer exists.")

    if not isinstance(markdown, str) or not markdown.strip():
        raise ValueError("The documentation agent returned empty Markdown.")

    if len(markdown.encode("utf-8")) > 200_000:
        raise ValueError("Generated README is larger than the 200 KB safety limit.")

    # Guard against accidental path traversal: the only output is repo_root/README.md.
    target = repo_path / "README.md"
    backup = repo_path / "README.md.bak"
    temp = repo_path / ".README.md.tmp"

    if target.exists() and not target.is_file():
        raise ValueError("README.md exists but is not a regular file.")

    if target.exists():
        if backup.exists():
            backup.unlink()
        target.replace(backup)

    try:
        temp.write_text(markdown.rstrip() + "\n", encoding="utf-8")
        temp.replace(target)
    except Exception:
        if temp.exists():
            temp.unlink()
        if backup.exists() and not target.exists():
            backup.replace(target)
        raise

    return (
        f"README generated successfully: {target}\n"
        + (f"Previous README backed up to: {backup}" if backup.exists()
           else "No previous README was present.")
    )
