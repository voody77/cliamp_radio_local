# Тестирование cliamp_radio_local

## 1. Слои

| Слой | Что проверяет | Где |
|---|---|---|
| Синтаксис | Python-компиляция | `make compile` |
| CLI smoke | `--help` всех скриптов | GitHub Actions |
| TOML | валидность собранных плейлистов | refresh workflow |
| Потоки | доступность станций | `verify_playlists.py` |

## 2. Правила

- тесты проверяют поведение через публичные CLI-флаги;
- ожидаемые значения — из формата cliamp и TOML;
- перед изменениями сначала воспроизводите сбой;
- сетевые проверки не должны быть обязательными для обычного CI.

## 3. Что не покрыто

- unit-тесты парсинга M3U и Radio Browser;
- rate limits и retry;
- реальная доступность всех станций;
- разные версии cliamp.

## 4. Перед изменением

1. `make compile`.
2. `python build_genres.py --help`.
3. `make check` на существующих плейлистах.
4. `python3 scripts/check_docs.py --strict`.
