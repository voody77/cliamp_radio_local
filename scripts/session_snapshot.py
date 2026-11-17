#!/usr/bin/env python3
"""Collect git and context state for a session handoff."""

from __future__ import annotations

import argparse
import subprocess
import sys
from datetime import datetime
from pathlib import Path


def run(command: list[str], cwd: Path) -> str:
    try:
        result = subprocess.run(
            command,
            cwd=cwd,
            text=True,
            capture_output=True,
            check=False,
        )
    except OSError as exc:
        return f"(not available: {exc})"
    output = (result.stdout or result.stderr).strip()
    return output or "(empty)"


def git_state(root: Path) -> list[str]:
    inside = run(["git", "rev-parse", "--is-inside-work-tree"], root)
    if inside != "true":
        return ["Git: не репозиторий"]
    return [
        f"Ветка: `{run(['git', 'branch', '--show-current'], root)}`",
        "",
        "```text",
        run(["git", "status", "--short"], root),
        "```",
        "",
        "Последние коммиты:",
        "",
        "```text",
        run(["git", "log", "--oneline", "-10"], root),
        "```",
        "",
        "Изменённые файлы:",
        "",
        "```text",
        run(["git", "diff", "--stat"], root),
        run(["git", "diff", "--cached", "--stat"], root),
        "```",
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect a session snapshot")
    parser.add_argument("--dir", default=".", help="project directory")
    parser.add_argument(
        "--write",
        help="write the machine snapshot to this file, e.g. docs/handoff.snapshot.md",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="run scripts/check_docs.py and include the result",
    )
    args = parser.parse_args(argv)
    root = Path(args.dir).expanduser().resolve()

    lines = [
        "# Снимок сессии",
        "",
        f"- Дата: {datetime.now().isoformat(timespec='seconds')}",
        f"- Каталог: `{root}`",
        "",
        "## 1. Git",
        "",
        *git_state(root),
        "",
        "## 2. Контекст",
        "",
        "Прочитайте перед продолжением:",
        "",
        "- `AGENTS.md`",
        "- `docs/status.md`",
        "- `docs/progress.md`, если существует",
        "- `docs/known-issues.md`",
        "- `docs/decisions/README.md`",
        "- `docs/handoff.md` и `docs/handoff.snapshot.md`, если существуют",
        "",
        "## 3. Проверки",
        "",
    ]
    if args.check:
        check = root / "scripts" / "check_docs.py"
        if check.is_file():
            lines.extend(
                [
                    "```text",
                    run([sys.executable, "scripts/check_docs.py"], root),
                    "```",
                ]
            )
        else:
            lines.append("`scripts/check_docs.py` не найден.")
    else:
        lines.append("Запустите `python3 scripts/check_docs.py` и тесты проекта.")

    lines.extend(
        [
            "",
            "## 4. Для handoff",
            "",
            "Этот snapshot — вход для `handoff` skill. Итоговый "
            "`docs/handoff.md` содержит",
            "цель, состояние, решения, отброшенное и следующий шаг.",
            "",
        ]
    )
    text = "\n".join(lines)
    if args.write:
        output = Path(args.write).expanduser()
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(text, encoding="utf-8", newline="\n")
        print(output)
    else:
        print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
