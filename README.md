# cliamp_radio_local

Скрипты для сборки тематических радио-плейлистов для
[cliamp](https://github.com/bjarneo/cliamp) из каталога
[Radio Browser](https://www.radio-browser.info/).

Каталог станций cliamp (`external/radio/catalog.go`) сам ничего не хранит —
станции приходят из Radio Browser. Эти скрипты выгружают их заранее,
проверяют доступность с текущей машины и раскладывают в локальные TOML-плейлисты
cliamp.

## Что создаётся

В `~/.config/cliamp/playlists/`:

| Файл | Содержимое |
|------|-----------|
| `Жанр — <Name>.toml` | до 50 станций на каждый из 60 жанров |
| `Россия — <Name>.toml` | до 50 российских станций на жанр |
| `cliamp-radio.toml` | 15 встроенных каналов cliamp |

Формат записи — штатный формат cliamp:

```toml
[[track]]
path = "http://choco.hostingradio.ru:10010/fm"
title = "Радио Шоколад"
genre = "Россия / Pop"
realtime = true
```

`realtime = true` включает переподключение после паузы или обрыва — это важно
для живого радио.

## Требования

- Linux с `iproute2` (`ip`) и `curl`
- Python 3.11+ (используется `tomllib`)
- `requests`

```sh
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
```

Или через Makefile — он сам создаст `.venv` и поставит зависимости:

```sh
make            # список целей
make install    # venv + зависимости
make genres     # мировые жанры
make russia     # российские жанры
make all        # и то, и другое
make check      # проверить потоки во всех плейлистах
make prune      # удалить мёртвые потоки
make compile    # быстрая проверка синтаксиса
make clean
```

Переменные: `OUT_DIR`, `IFACE`, `PER_LIST`, `CANDIDATES`.

```sh
make all OUT_DIR=~/tmp/playlists PER_LIST=80 CANDIDATES=200
make check IFACE=wlp3s0
```

## Проверка без VPN

Каждый поток проверяется реальным GET-запросом с этой машины:

- сокет привязывается к IPv4-адресу сетевого интерфейса (`--iface`, по
  умолчанию — интерфейс маршрута по умолчанию, обычно `wlp3s0`);
- в начале работы печатается внешний IP и провайдер через `ipinfo.io` — так
  видно, что трафик не ушёл в VPN-туннель;
- принимаются только ответы `200/206` с аудио-content-type или аудиомагией в
  первых байтах;
- отбрасываются `.m3u`/`.m3u8`/`.pls`-обёртки, HTML-страницы и мёртвые ссылки.

Если `tun0` поднят, но default route идёт через Wi-Fi, привязка к адресу Wi-Fi
всё равно гарантирует, что проверка не пойдёт через туннель.

## Скрипты

### `build_genres.py` — мировые жанры

```sh
python3 build_genres.py
python3 build_genres.py --per-list 100 --candidates 200
python3 build_genres.py --iface wlp3s0 --out-dir ~/tmp/playlists
```

Создаёт 60 плейлистов `Жанр — …` и обновляет `cliamp-radio.toml`.
К станциям жанра Acoustic добавляются несколько отобранных вручную потоков.

### `build_russia_genres.py` — Россия по жанрам

```sh
python3 build_russia_genres.py
python3 build_russia_genres.py --include-small        # жанры с 1–4 станциями
python3 build_russia_genres.py --min-stations 3
```

Удаляет старый общий `Россия.toml` (если он есть) и создаёт
`Россия — <жанр>.toml`. Жанры, где меньше `--min-stations` живых станций,
по умолчанию пропускаются. В `Россия — Pop` первыми идут Радио Шоколад
(Москва и Нижний Новгород).

### `verify_playlists.py` — проверка готовых плейлистов

```sh
python3 verify_playlists.py                        # проверить всё
python3 verify_playlists.py "Жанр — Rock.toml"     # один файл
python3 verify_playlists.py --prune                # удалить мёртвые ссылки
```

Печатает мёртвые потоки по плейлистам. С `--prune` перезаписывает файлы без
них. Код возврата `1`, если мёртвые ссылки остались (удобно для cron/CI).

## Общие опции

| Опция | По умолчанию | Значение |
|-------|--------------|----------|
| `--out-dir` | `~/.config/cliamp/playlists` | куда писать TOML |
| `--iface` | интерфейс default route | к какому интерфейсу привязываться |
| `--per-list` | `50` | сколько станций оставить в списке |
| `--candidates` | `120` | сколько кандидатов проверить |
| `--workers` | `64` | параллельных проверок |
| `--page` | `10` | размер страницы API |
| `--api` | `https://de1.api.radio-browser.info/json` | зеркало Radio Browser |

`--page` не стоит поднимать сильно: API периодически обрывает большие ответы,
поэтому скрипт ходит страницами по 10 и повторяет запрос при ошибке.

## Использование в cliamp

1. Перезапустить cliamp.
2. `Esc` / `b` → **Local**.
3. `/` → набрать `Жанр` или `Россия`.
4. `Enter` → `>` / `<` — переключение станций, `f` — избранное.

## Структура

```
cliamp_radio_local/
├── build_genres.py          # мировые жанры + cliamp-radio
├── build_russia_genres.py   # российские жанры
├── verify_playlists.py      # проверка/чистка плейлистов
├── radio_playlists/
│   ├── core.py              # API, проверка потоков, запись TOML
│   ├── genres.py            # список жанров и ручные станции
│   └── cliamp_channels.py   # встроенные каналы cliamp
├── .github/workflows/       # CI и еженедельная сборка
├── Makefile
├── requirements.txt
└── README.md
```

Скрипты перезаписывают только те файлы, которые генерируют сами. Если вы
правили плейлист вручную, изменения в нём потеряются при следующем запуске —
держите ручные правки в отдельном файле или в `radios.toml`.

## GitHub Actions

| Workflow | Когда | Что делает |
|----------|-------|-----------|
| `CI` | push в `main`, pull request | `make compile` + `--help` всех скриптов |
| `Refresh playlists` | по понедельникам в 03:00 UTC и вручную | собирает все плейлисты в `build/playlists`, валидирует TOML и выкладывает артефакт `cliamp-playlists` (14 дней) |

Ручной запуск с параметрами:

```sh
gh workflow run refresh.yml -f per_list=50 -f candidates=120
gh run list --workflow=refresh.yml
gh run watch
gh run download --name cliamp-playlists
```

Скачанные `.toml` достаточно положить в `~/.config/cliamp/playlists/`.
В CI проверка идёт через `eth0` (default route раннера) — привязка к
интерфейсу там работает так же, как локально.

