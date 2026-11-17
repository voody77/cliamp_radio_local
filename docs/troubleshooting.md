# Диагностика cliamp_radio_local

| Симптом | Что проверить | Действие |
|---|---|---|
| `make install` падает | Python 3.11+, сеть, pip | пересоздать `.venv`, повторить |
| `requests` не найден | активирован ли `.venv` | `make install`, `. .venv/bin/activate` |
| `curl` или `ip` не найден | системные пакеты | установить `curl`, `iproute2` |
| Нет станций в жанре | Radio Browser и фильтры | проверить `--api`, `--candidates`, `--per-list` |
| Все станции мёртвые | сеть или провайдер | `make check`, `--iface`, `--prune` |
| Плейлист не читается cliamp | TOML и `[[track]]` | проверить `tomllib`, пересобрать |
| Файлы не появились | `--out-dir` | проверить каталог `~/.config/cliamp/playlists/` |
| Обновление CI зависло | Radio Browser/сеть | смотреть лог workflow, повторить вручную |
| `check_docs` падает | обязательные файлы, ссылки, маркеры | `python3 scripts/check_docs.py --strict` |
