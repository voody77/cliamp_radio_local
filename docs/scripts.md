# Скрипты и режимы

| Скрипт | Вход | Выход | Ошибки |
|---|---|---|---|
| `build_genres.py` | `--out-dir`, `--api`, `--iface`, `--per-list`, `--candidates` | `Жанр — *.toml`, `cliamp-radio.toml` | код 1 при сбое сети |
| `build_russia_genres.py` | те же + `--min-stations`, `--include-small` | `Россия — *.toml` | код 1 при сбое |
| `verify_playlists.py` | файлы или `--dir`, `--prune` | отчёт и очистка | код 1, если остались мёртвые |

## Makefile

| Цель | Действие |
|---|---|
| `make install` | venv и зависимости |
| `make genres` | мировые жанры |
| `make russia` | российские жанры |
| `make all` | оба набора |
| `make check` | проверка потоков |
| `make prune` | удаление мёртвых станций |
| `make compile` | `py_compile` |

## Правила

- скрипты идемпотентны: повторная сборка перезаписывает плейлист;
- секретов нет;
- exit code 1 при ошибке проверки или сети.
