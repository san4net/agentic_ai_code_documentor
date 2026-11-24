from __future__ import annotations

import hashlib
import os
import re
import shutil
import stat
import tempfile
import zipfile
from pathlib import Path, PurePosixPath

MAX_ARCHIVE_ENTRIES = 20_000
MAX_ARCHIVE_UNCOMPRESSED_BYTES = 512 * 1024 * 1024
MAX_ARCHIVE_FILE_BYTES = 50 * 1024 * 1024
MAX_COMPRESSION_RATIO = 200


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def extract_repository_zip(value: str) -> tuple[Path, Path]:
    """Safely extract a ZIP into a temporary directory.

    Returns (temporary extraction root, detected repository root). The caller
    owns the temporary directory and must remove it after review completion.
    """
    raw = (value or "").strip().strip('"').strip("'")
    if not raw:
        raise ValueError("Please provide the fully qualified path to a ZIP file.")

    candidate = Path(raw).expanduser()
    if not candidate.is_absolute():
        raise ValueError("The ZIP file path must be fully qualified (absolute).")
    if candidate.is_symlink():
        raise ValueError("The ZIP file path must not be a symbolic link.")
    archive_path = candidate.resolve(strict=True)
    if not archive_path.is_file() or archive_path.suffix.lower() != ".zip":
        raise ValueError(f"The supplied path must point to an existing .zip file: {archive_path}")

    safe_stem = re.sub(r"[^A-Za-z0-9._-]+", "_", archive_path.stem).strip("._") or "repository"
    temp_parent = Path(tempfile.gettempdir())
    temp_root = temp_parent / safe_stem
    suffix = 1
    while True:
        try:
            temp_root.mkdir(mode=0o700)
            break
        except FileExistsError:
            temp_root = temp_parent / f"{safe_stem}-{suffix}"
            suffix += 1
    try:
        with zipfile.ZipFile(archive_path, "r") as archive:
            entries = archive.infolist()
            if not entries:
                raise ValueError("The ZIP archive is empty.")
            if len(entries) > MAX_ARCHIVE_ENTRIES:
                raise ValueError(f"ZIP contains too many entries (limit: {MAX_ARCHIVE_ENTRIES}).")

            total_size = sum(info.file_size for info in entries if not info.is_dir())
            if total_size > MAX_ARCHIVE_UNCOMPRESSED_BYTES:
                raise ValueError("ZIP expands beyond the 512 MB safety limit.")

            seen: set[str] = set()
            for info in entries:
                raw_name = info.filename.replace("\\", "/")
                member = PurePosixPath(raw_name)
                if (
                    not raw_name
                    or member.is_absolute()
                    or ".." in member.parts
                    or (member.parts and ":" in member.parts[0])
                    or "\x00" in raw_name
                ):
                    raise ValueError(f"Unsafe path found in ZIP archive: {info.filename!r}")
                normalized = member.as_posix().rstrip("/")
                if not normalized or normalized == "__MACOSX" or normalized.startswith("__MACOSX/"):
                    continue
                if member.name == ".DS_Store":
                    continue
                if normalized in seen:
                    raise ValueError(f"Duplicate path found in ZIP archive: {normalized}")
                seen.add(normalized)

                mode = (info.external_attr >> 16) & 0xFFFF
                if stat.S_ISLNK(mode):
                    # Never materialize or silently discard symlinks from an archive.
                    raise ValueError(f"Symbolic links are not supported in ZIP input: {normalized}")
                if info.flag_bits & 0x1:
                    raise ValueError("Encrypted ZIP entries are not supported.")
                if info.file_size > MAX_ARCHIVE_FILE_BYTES:
                    raise ValueError(f"ZIP entry exceeds the 50 MB limit: {normalized}")
                if info.file_size and info.compress_size == 0:
                    raise ValueError(f"Invalid compressed size for ZIP entry: {normalized}")
                if info.compress_size and info.file_size / info.compress_size > MAX_COMPRESSION_RATIO:
                    raise ValueError(f"ZIP entry compression ratio is too high: {normalized}")

                destination = temp_root.joinpath(*member.parts)
                resolved_destination = destination.resolve()
                if not resolved_destination.is_relative_to(temp_root.resolve()):
                    raise ValueError(f"ZIP entry escapes extraction directory: {normalized}")

                if info.is_dir():
                    destination.mkdir(parents=True, exist_ok=True)
                    continue

                destination.parent.mkdir(parents=True, exist_ok=True)
                with archive.open(info, "r") as source, destination.open("xb") as target:
                    shutil.copyfileobj(source, target, length=1024 * 1024)

        top_level = list(temp_root.iterdir())
        if len(top_level) == 1 and top_level[0].is_dir():
            repository_root = top_level[0]
        else:
            repository_root = temp_root

        if not any(path.is_file() for path in repository_root.rglob("*")):
            raise ValueError("The ZIP archive does not contain any files.")

        return temp_root, repository_root
    except Exception:
        shutil.rmtree(temp_root, ignore_errors=True)
        raise
