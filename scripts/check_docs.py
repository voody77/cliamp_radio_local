#!/usr/bin/env python3
"""Check the project documentation set.

The checker is dependency-free and runs both locally and in CI:

    python3 scripts/check_docs.py
    python3 scripts/check_docs.py --strict

It reads ``agent-context.json``, verifies required documents, resolves
relative Markdown links in managed documents (``required_docs`` and
``local_guides``), and checks the ``Обновлено: YYYY-MM-DD`` marker in
``docs/status.md``. ``--strict`` additionally fails on unfilled ``TODO``
markers and a stale status file; use it as a release gate.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path
from urllib.parse import unquote

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / "agent-context.json"
STATUS = ROOT / "docs" / "status.md"
STALE_DAYS = 180

LINK = re.compile(
    r"\[[^\]]*\]\(\s*(?:<([^>]+)>|((?:[^()\s]|\([^()]*\))+))"
    r"(?:\s+(?:\"[^\"]*\"|'[^']*'|\([^)]*\)))?\s*\)"
)
DATE = re.compile(r"Обновлено:\s*\**\s*(\d{4}-\d{2}-\d{2})")
TODO = re.compile(r"\bTODO\b")
SKIP_PREFIXES = ("http://", "https://", "mailto:", "#", "/")


def strip_code(text: str) -> str:
    """Remove fenced and inline code while keeping line numbers stable."""
    text = re.sub(
        r"```.*?```",
        lambda match: "\n" * match.group(0).count("\n"),
        text,
        flags=re.DOTALL,
    )
    return re.sub(r"`[^`\n]*`", "", text)


def safe_path(name: str) -> Path | None:
    """Return a path inside the project or ``None`` for an unsafe name."""
    if not name or any(ord(character) < 32 for character in name):
        return None
    relative = Path(name)
    if relative.is_absolute() or ".." in relative.parts:
        return None
    try:
        candidate = (ROOT / relative).resolve()
    except (OSError, ValueError):
        return None
    try:
        candidate.relative_to(ROOT)
    except ValueError:
        return None
    return candidate


def load_manifest() -> dict:
    if not MANIFEST.is_file():
        raise ValueError("agent-context.json is missing")
    try:
        data = json.loads(MANIFEST.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValueError(f"agent-context.json is invalid: {exc}") from exc
    if not isinstance(data, dict):
        raise TypeError("agent-context.json must contain an object")
    return data


def required_docs(manifest: dict) -> list[str]:
    docs = manifest.get("required_docs")
    if not isinstance(docs, list) or not docs:
        raise ValueError("agent-context.json has no required_docs")
    return [str(item) for item in docs]


def managed_docs(manifest: dict) -> list[str]:
    names = list(required_docs(manifest))
    guides = manifest.get("local_guides", [])
    if isinstance(guides, list):
        names.extend(str(item) for item in guides)
    result: list[str] = []
    for name in names:
        if name and name not in result:
            result.append(name)
    return result


def label(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:
        return str(path)


def markdown_files(names: list[str]) -> list[Path]:
    files: list[Path] = []
    for name in names:
        path = safe_path(name)
        if path is not None and path.is_file():
            files.append(path)
    return files


def read_markdown(path: Path) -> str | None:
    """Return text or ``None`` when the file is unreadable or not UTF-8."""
    try:
        return path.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None


def check_links(files: list[Path]) -> list[str]:
    failures: list[str] = []
    for path in files:
        text = read_markdown(path)
        if text is None:
            failures.append(f"{label(path)}: not UTF-8 or unreadable")
            continue
        for number, line in enumerate(strip_code(text).splitlines(), 1):
            for match in LINK.finditer(line):
                target = (match.group(1) or match.group(2) or "").strip()
                if not target or target.startswith(SKIP_PREFIXES):
                    continue
                target = unquote(
                    target.split("#", 1)[0].split("?", 1)[0].strip()
                )
                if not target:
                    continue
                if any(ord(character) < 32 for character in target):
                    failures.append(
                        f"{label(path)}:{number}: invalid link target"
                    )
                    continue
                try:
                    resolved = (path.parent / target).resolve()
                except (OSError, ValueError):
                    failures.append(
                        f"{label(path)}:{number}: invalid link target"
                    )
                    continue
                try:
                    resolved.relative_to(ROOT)
                except ValueError:
                    failures.append(
                        f"{label(path)}:{number}: {target} escapes the project"
                    )
                    continue
                if not resolved.exists():
                    failures.append(f"{label(path)}:{number}: {target}")
    return failures


def check_status(*, strict: bool) -> list[str]:
    failures: list[str] = []
    if not STATUS.is_file():
        return ["docs/status.md is missing"]
    text = read_markdown(STATUS)
    if text is None:
        return ["docs/status.md is not UTF-8 or unreadable"]
    match = DATE.search(text)
    if not match:
        return ["docs/status.md has no 'Обновлено: YYYY-MM-DD' marker"]
    try:
        updated = datetime.strptime(match.group(1), "%Y-%m-%d").date()
    except ValueError:
        return [f"docs/status.md has an invalid date: {match.group(1)}"]
    age = (date.today() - updated).days
    message = (
        f"docs/status.md was updated {age} days ago ({updated}); "
        "refresh it before a release"
    )
    if age < 0:
        return [f"docs/status.md has a future date: {updated}"]
    if age > STALE_DAYS:
        if strict:
            failures.append(message)
        else:
            print(f"WARN {message}")
    return failures


def check_todos(docs: list[str], *, strict: bool) -> list[str]:
    if not strict:
        return []
    failures: list[str] = []
    for name in docs:
        path = safe_path(name)
        if path is None or not path.is_file():
            continue
        text = read_markdown(path)
        if text is None:
            continue
        text = strip_code(text)
        count = len(TODO.findall(text))
        if count:
            failures.append(f"{name}: {count} TODO marker(s) left")
    return failures


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Check the documentation set")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="fail on TODO markers and a stale status file",
    )
    args = parser.parse_args(argv)

    try:
        manifest = load_manifest()
        docs = required_docs(manifest)
        managed = managed_docs(manifest)
    except (ValueError, TypeError) as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1

    unsafe = sorted({name for name in managed if safe_path(name) is None})
    failures = [f"unsafe managed path: {name}" for name in unsafe]
    for name in docs:
        path = safe_path(name)
        if path is not None and not path.is_file():
            failures.append(f"missing required file: {name}")
    failures.extend(check_links(markdown_files(managed)))
    failures.extend(check_status(strict=args.strict))
    failures.extend(check_todos(docs, strict=args.strict))

    if failures:
        for failure in failures:
            print(f"FAIL {failure}", file=sys.stderr)
        return 1
    print(f"docs check: {len(docs)} required files, links OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
