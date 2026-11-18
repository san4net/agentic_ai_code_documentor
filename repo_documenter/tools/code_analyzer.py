from __future__ import annotations

import ast
import json
import re
from pathlib import Path
from typing import Any

MAX_SOURCE_BYTES = 512_000
MAX_SYMBOLS_PER_FILE = 250
MAX_ANALYZED_FILES = 1200


def _read_source(repo_root: Path, relative_path: str) -> str | None:
    """Read a bounded UTF-8 source file without following symlinks."""
    path = (repo_root / relative_path).resolve()
    try:
        path.relative_to(repo_root.resolve())
    except ValueError:
        return None

    if not path.is_file() or path.is_symlink():
        return None

    try:
        if path.stat().st_size > MAX_SOURCE_BYTES:
            return None
        raw = path.read_bytes()
        if b"\x00" in raw:
            return None
        return raw.decode("utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def _python_analysis(source: str) -> dict[str, Any]:
    result = {"classes": [], "functions": [], "imports": [], "parse_error": None}
    try:
        tree = ast.parse(source)
    except SyntaxError as exc:
        result["parse_error"] = f"SyntaxError at line {exc.lineno}: {exc.msg}"
        return result

    for node in ast.walk(tree):
        if isinstance(node, (ast.ClassDef,)):
            result["classes"].append({
                "name": node.name,
                "line": node.lineno,
                "bases": [
                    ast.unparse(base) if hasattr(ast, "unparse") else type(base).__name__
                    for base in node.bases
                ],
                "docstring_present": bool(ast.get_docstring(node)),
                "methods": [
                    child.name for child in node.body
                    if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef))
                ],
            })
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            result["functions"].append({
                "name": node.name,
                "line": node.lineno,
                "async": isinstance(node, ast.AsyncFunctionDef),
                "parameters": [arg.arg for arg in node.args.args],
                "docstring_present": bool(ast.get_docstring(node)),
            })
        elif isinstance(node, ast.Import):
            result["imports"].extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            result["imports"].append(node.module or ".")

    result["classes"] = result["classes"][:MAX_SYMBOLS_PER_FILE]
    result["functions"] = result["functions"][:MAX_SYMBOLS_PER_FILE]
    result["imports"] = sorted(set(result["imports"]))[:100]
    return result


def _walk_tree(node):
    yield node
    for child in node.children:
        yield from _walk_tree(child)


def _node_text(node, source_bytes: bytes) -> str:
    if node is None:
        return ""
    return source_bytes[node.start_byte:node.end_byte].decode("utf-8", errors="replace")


def _tree_sitter_analysis(source: str, language: str) -> dict[str, Any]:
    """Parse Java/JavaScript using tree-sitter-language-pack."""
    from tree_sitter_language_pack import get_parser

    source_bytes = source.encode("utf-8")
    parser_language = "java" if language == "Java" else "javascript"
    parser = get_parser(parser_language)
    tree = parser.parse(source_bytes)

    result = {"classes": [], "functions": [], "imports": [], "parse_error": None}
    class_types = {
        "class_declaration", "interface_declaration", "enum_declaration",
        "record_declaration",
    }
    function_types = {
        "method_declaration", "constructor_declaration",
        "function_declaration", "method_definition",
    }

    for node in _walk_tree(tree.root_node):
        if node.type in {"import_declaration", "package_declaration", "import_statement"}:
            result["imports"].append(_node_text(node, source_bytes).strip())

        if node.type in class_types:
            name_node = node.child_by_field_name("name")
            name = _node_text(name_node, source_bytes) or "<anonymous>"
            methods = []
            for child in _walk_tree(node):
                if child is not node and child.type in function_types:
                    method_name_node = child.child_by_field_name("name")
                    method_name = _node_text(method_name_node, source_bytes)
                    if method_name:
                        methods.append(method_name)
            result["classes"].append({
                "name": name,
                "line": node.start_point.row + 1,
                "methods": sorted(set(methods))[:100],
            })

        elif node.type in function_types:
            name_node = node.child_by_field_name("name")
            name = _node_text(name_node, source_bytes)
            if name:
                result["functions"].append({
                    "name": name,
                    "line": node.start_point.row + 1,
                })

        elif language == "JavaScript" and node.type == "variable_declarator":
            value_node = node.child_by_field_name("value")
            name_node = node.child_by_field_name("name")
            if value_node and value_node.type in {"arrow_function", "function_expression"}:
                name = _node_text(name_node, source_bytes)
                if name:
                    result["functions"].append({
                        "name": name,
                        "line": node.start_point.row + 1,
                        "kind": "function variable",
                    })

    result["classes"] = result["classes"][:MAX_SYMBOLS_PER_FILE]
    result["functions"] = result["functions"][:MAX_SYMBOLS_PER_FILE]
    result["imports"] = sorted(set(result["imports"]))[:100]
    return result


def _read_manifest_dependencies(root: Path) -> dict[str, Any]:
    metadata: dict[str, Any] = {"manifests": [], "dependencies": []}

    package_json = root / "package.json"
    if package_json.is_file() and not package_json.is_symlink():
        try:
            data = json.loads(package_json.read_text(encoding="utf-8"))
            metadata["manifests"].append("package.json")
            deps = {}
            deps.update(data.get("dependencies", {}))
            deps.update(data.get("devDependencies", {}))
            metadata["dependencies"].extend(sorted(deps.keys())[:150])
            metadata["package_name"] = data.get("name")
            metadata["package_scripts"] = list(data.get("scripts", {}).keys())[:50]
        except (OSError, json.JSONDecodeError):
            metadata["manifest_warnings"] = ["Could not parse package.json"]

    pyproject = root / "pyproject.toml"
    if pyproject.is_file() and not pyproject.is_symlink():
        try:
            import tomllib
            data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
            metadata["manifests"].append("pyproject.toml")
            project = data.get("project", {})
            metadata["dependencies"].extend(
                str(dep).split("[")[0].split(">")[0].split("=")[0]
                for dep in project.get("dependencies", [])
            )
            metadata["package_name"] = metadata.get("package_name") or project.get("name")
        except Exception:
            metadata.setdefault("manifest_warnings", []).append(
                "Could not parse pyproject.toml"
            )

    requirements = root / "requirements.txt"
    if requirements.is_file() and not requirements.is_symlink():
        try:
            metadata["manifests"].append("requirements.txt")
            for line in requirements.read_text(encoding="utf-8").splitlines():
                line = line.strip()
                if line and not line.startswith(("#", "-")):
                    metadata["dependencies"].append(
                        re.split(r"[<>=!~;\[]", line, maxsplit=1)[0].strip()
                    )
        except OSError:
            pass

    for manifest in ("pom.xml", "build.gradle", "build.gradle.kts"):
        path = root / manifest
        if path.is_file() and not path.is_symlink():
            metadata["manifests"].append(manifest)

    metadata["dependencies"] = sorted({
        dep for dep in metadata["dependencies"] if dep
    })[:200]
    return metadata


def analyze_repository(node_input: dict[str, Any]) -> dict[str, Any]:
    """Detect repository languages and parse supported source files.

    Receives the scanner's inventory dictionary from the previous workflow node.
    """
    print(f"Analyzing repository on basis of below \n {node_input}")
    inventory = node_input
    root = Path(inventory["root_path"]).resolve()
    language_counts = inventory.get("language_counts", {})
    primary_language = inventory.get("primary_language", "Unknown")

    file_analyses = []
    parser_errors = []

    for record in inventory.get("source_files", [])[:MAX_ANALYZED_FILES]:
        relative_path = record["path"]
        language = record["language"]
        source = _read_source(root, relative_path)

        if source is None:
            parser_errors.append({
                "file": relative_path,
                "error": "Skipped: unreadable, binary, oversized or unsafe path",
            })
            continue

        try:
            if language == "Python":
                parsed = _python_analysis(source)
            else:
                parsed = _tree_sitter_analysis(source, language)

            file_analyses.append({
                "file": relative_path,
                "language": language,
                **parsed,
            })
            if parsed.get("parse_error"):
                parser_errors.append({
                    "file": relative_path,
                    "error": parsed["parse_error"],
                })
        except Exception as exc:
            parser_errors.append({
                "file": relative_path,
                "error": f"Parser unavailable or failed: {type(exc).__name__}: {exc}",
            })

    metadata = _read_manifest_dependencies(root)

    # Lightweight framework indicators from declared dependency names.
    deps_lower = {d.lower() for d in metadata.get("dependencies", [])}
    indicators = {
        "Python": ["fastapi", "django", "flask", "starlette", "pytest"],
        "Java": ["spring-boot", "springframework", "quarkus", "micronaut"],
        "JavaScript": ["react", "next", "express", "vue", "angular", "nestjs"],
    }
    framework_indicators = sorted({
        marker for marker in indicators.get(primary_language, [])
        if any(marker in dep for dep in deps_lower)
    })

    return {
        "repository_name": inventory["repository_name"],
        "root_path": inventory["root_path"],
        "primary_language": primary_language,
        "language_counts": language_counts,
        "file_count": inventory["file_count"],
        "inventory_truncated": inventory.get("inventory_truncated", False),
        "project_files": inventory.get("project_files", []),
        "manifest_metadata": metadata,
        "framework_indicators": framework_indicators,
        "analyzed_file_count": len(file_analyses),
        "file_analyses": file_analyses,
        "parser_errors": parser_errors[:100],
    }
