# Статус cliamp_radio_local

- **Обновлено:** 2026-11-17
- **Версия:** из `README.md`/Makefile; отдельный semver не ведётся
- **Ветка:** main

## 1. Что работает

- мировые жанровые плейлисты (`make genres`);
- российские жанровые плейлисты (`make russia`);
- встроенные каналы cliamp;
- проверка потоков и `--prune` (`make check`, `make prune`);
- синтаксическая проверка `make compile`;
- CI: compile и CLI smoke;
- недельное обновление через GitHub Actions.

## 2. Окружения

| Окружение | Назначение | Состояние |
|---|---|---|
| Локальное | сборка плейлистов | `.venv`, `make` |
| CI | compile и smoke | GitHub Actions |
| Промышленное | не применимо | локальные файлы пользователя |

## 3. Проверки на дату

```text
make compile
python build_genres.py --help
python build_russia_genres.py --help
python verify_playlists.py --help
python3 scripts/check_docs.py
```

## 4. Открытые блокеры

| Блокер | Влияние | Владелец |
|---|---|---|
| Зависимость от Radio Browser и сети | нет сети — нет обновления | владелец проекта |
| Станции часто умирают | нужен `make prune` | владелец проекта |
| Нет unit-тестов | проверяется синтаксис и smoke | владелец проекта |

## 5. Что дальше

1. Добавить unit-тесты для парсинга и TOML.
2. Проверить лимиты Radio Browser и retry.
3. Обновлять статус при изменении формата cliamp.
