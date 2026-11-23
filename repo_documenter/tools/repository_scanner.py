from __future__ import annotations

import os
from pathlib import Path
from typing import Any

SUPPORTED_EXTENSIONS = {
    ".py": "Python",
    ".java": "Java",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".mjs": "JavaScript",
    ".cjs": "JavaScript",
}

EXCLUDED_DIRS = {
    ".git", ".hg", ".svn", ".idea", ".vscode",
    ".venv", "venv", "env", "__pycache__",
    "node_modules", "target", "build", "dist",
    ".next", ".nuxt", "coverage", ".pytest_cache",
    ".mypy_cache", ".tox", "vendor",
}

EXCLUDED_FILENAMES = {
    ".env", ".env.local", ".env.production",
    "id_rsa", "id_ed25519",
}

EXCLUDED_SUFFIXES = {
    ".pyc", ".pyo", ".class", ".jar", ".war",
    ".zip", ".gz", ".png", ".jpg", ".jpeg",
    ".gif", ".pdf", ".db", ".sqlite", ".pem",
    ".key", ".p12", ".pfx", ".keystore",
}

MAX_FILES = 5000


def scan_repository(node_input: str) -> dict[str, Any]:
    """Scan a local repository path and return a bounded source-file inventory.

    Pass an absolute or relative local directory path as the workflow input.
    The scanner does not execute repository code and skips symlinks.
    """
    raw_path = (node_input or "").strip().strip('"').strip("'")
    if not raw_path:
        raise ValueError("Please provide a repository folder path.")

    root = Path(raw_path).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise ValueError(f"Repository folder does not exist or is not a directory: {root}")

    file_records: list[dict[str, str]] = []
    language_counts: dict[str, int] = {}
    tree_entries: list[str] = []
    truncated = False

    for current_dir, dirs, filenames in os.walk(root, followlinks=False):
        current = Path(current_dir)

        # Prune ignored and symlink directories in-place.
        dirs[:] = [
            d for d in dirs
            if d not in EXCLUDED_DIRS and not (current / d).is_symlink()
        ]

        rel_dir = current.relative_to(root)
        if str(rel_dir) != ".":
            tree_entries.append(f"{rel_dir.as_posix()}/")

        for filename in sorted(filenames):
            path = current / filename

            if path.is_symlink() or filename in EXCLUDED_FILENAMES:
                continue

            suffix = path.suffix.lower()
            if suffix in EXCLUDED_SUFFIXES:
                continue

            try:
                rel_path = path.relative_to(root).as_posix()
            except ValueError:
                continue

            # Include non-source project manifests in the tree, but only source
            # files are sent to parsers.
            if filename in {
                "pyproject.toml", "requirements.txt", "Pipfile",
                "pom.xml", "build.gradle", "build.gradle.kts",
                "settings.gradle", "package.json", "tsconfig.json",
                "Makefile", "Dockerfile", "docker-compose.yml",
                "docker-compose.yaml",
            }:
                tree_entries.append(rel_path)

            language = SUPPORTED_EXTENSIONS.get(suffix)
            if language:
                try:
                    size = path.stat().st_size
                except OSError:
                    continue

                file_records.append({
                    "path": rel_path,
                    "language": language,
                    "size_bytes": str(size),
                })
                language_counts[language] = language_counts.get(language, 0) + 1

                if len(file_records) >= MAX_FILES:
                    truncated = True
                    break

        if truncated:
            break

    if not file_records:
        raise ValueError(
            "No supported .py, .java, .js, .jsx, .mjs or .cjs files were found."
        )

    primary_language = max(language_counts, key=language_counts.get)

    return {
        "repository_name": root.name,
        "root_path": str(root),
        "file_count": len(file_records),
        "language_counts": language_counts,
        "primary_language": primary_language,
        "source_files": file_records,
        "project_files": sorted(set(tree_entries))[:1500],
        "inventory_truncated": truncated,
    }