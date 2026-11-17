# Архитектура cliamp_radio_local

## 1. Назначение

Скрипты заранее собирают локальные TOML-плейлисты для cliamp из каталога
Radio Browser. Сам cliamp не хранит станции: каталог приходит извне.

## 2. Компоненты

| Компонент | Ответственность |
|---|---|
| `build_genres.py` | мировые жанровые плейлисты |
| `build_russia_genres.py` | российские жанровые плейлисты |
| `verify_playlists.py` | проверка и очистка мёртвых станций |
| `radio_playlists/` | Radio Browser client, жанры, TOML writer |
| `Makefile` | venv, install, build, check, prune, compile |
| GitHub Actions | проверка синтаксиса и недельное обновление |

## 3. Поток

```text
Radio Browser API → фильтр жанра/страны → проверка потока с локального IP
                  → до N станций → TOML в ~/.config/cliamp/playlists/
```

## 4. Хранилища

- TOML-плейлисты в `~/.config/cliamp/playlists/` (или `--out-dir`);
- `.venv` с зависимостями;
- `build/playlists` в CI как временный артефакт.

## 5. Интерфейсы

- Radio Browser API (`--api`);
- cliamp M3U для встроенных каналов;
- `curl` и `ip` для проверки потока и выбора интерфейса;
- Makefile как основной вход.

## 6. Отказы

- нет сети или Radio Browser — плейлисты не обновляются;
- мёртвые станции отсеиваются проверкой;
- `--prune` удаляет мёртвые записи;
- секретов нет; проект работает без авторизации.
