---
name: resume
description: Recover a task after a lost or broken session. Use when the chat history is gone, the context window was reset, or a new session must continue existing work.
argument-hint: "What was the task or next step?"
disable-model-invocation: true
---

Восстанови контекст после потери сессии, не выдумывая факты.

1. Прочитай `AGENTS.md`, `docs/status.md`, `docs/progress.md` (если есть),
   `docs/handoff.md` и `docs/handoff.snapshot.md` (если есть).
2. Посмотри `git status`, `git log --oneline -10`, `git diff` и
   `git diff --cached`. Незакоммиченные изменения могут быть чужими — не
   удаляй и не перезаписывай их без подтверждения.
3. Запусти `python3 scripts/check_docs.py` и команды проверки из
   `AGENTS.md`; зафиксируй, что реально работает.
4. Найди задачу в `docs/known-issues.md`, ADR, `CHANGELOG.md` и последних
   коммитах. Не восстанавливай решения по памяти.
5. Сформулируй короткий resume:
   - цель;
   - что уже сделано;
   - что не завершено;
   - следующий шаг;
   - какие проверки пройдены.
6. Если цель или решение не восстанавливаются из репозитория — спроси
   человека. Не начинай опасные изменения (`--force`, миграции, удаление)
   без подтверждения.
7. Перед следующим рискованным шагом обнови `docs/progress.md` или собери
   handoff.

Полезно:

```bash
python3 scripts/session_snapshot.py --dir . --check
python3 scripts/session_snapshot.py --dir . --write docs/handoff.snapshot.md --check
```
