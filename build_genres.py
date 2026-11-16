#!/usr/bin/env python3
"""Build worldwide genre playlists for cliamp.

Creates one playlist per genre: "Жанр — <Name>.toml". Every stream is
verified from this host, with sockets bound to the chosen interface.
"""

from __future__ import annotations

import argparse
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from radio_playlists import (
    ACOUSTIC_EXTRAS,
    DEFAULT_API,
    DEFAULT_OUT_DIR,
    GENRES,
    RadioClient,
    fetch_channels,
    station_name,
    station_url,
    write_playlist,
)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="playlist directory")
    parser.add_argument("--api", default=DEFAULT_API, help="Radio Browser API base")
    parser.add_argument("--iface", default=None, help="interface to bind to (default: default route)")
    parser.add_argument("--per-list", type=int, default=50, help="stations kept per genre")
    parser.add_argument("--candidates", type=int, default=120, help="stations checked per genre")
    parser.add_argument("--workers", type=int, default=64, help="parallel stream checks")
    parser.add_argument("--page", type=int, default=10, help="catalog page size")
    parser.add_argument("--skip-cliamp", action="store_true", help="do not refresh cliamp-radio")
    parser.add_argument("--no-extras", action="store_true", help="skip hand-picked stations")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = RadioClient(api=args.api, iface=args.iface, workers=args.workers, page=args.page)
    print(f"Interface: {client.iface} ({client.source_ip})")
    try:
        info = client.egress()
        print(f"Egress: {info.get('ip')} ({info.get('org', '?')}, {info.get('city', '?')}, {info.get('country', '?')})")
    except Exception as exc:  # noqa: BLE001
        print(f"! could not confirm egress: {exc}")

    candidates: dict[str, list[dict]] = {}
    print(f"Collecting candidates for {len(GENRES)} genres...")
    for index, (display, tag) in enumerate(GENRES, 1):
        stations = client.candidates({"tag": tag, "tagExact": "true"}, args.candidates)
        candidates[display] = stations
        print(f"  [{index}/{len(GENRES)}] {display}: {len(stations)} candidates")

    urls: dict[str, bool] = {}
    for stations in candidates.values():
        for station in stations:
            url = station_url(station)
            if url:
                urls.setdefault(url, False)
    print(f"Verifying {len(urls)} unique streams...")

    done = 0
    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(client.stream_ok, url): url for url in urls}
        for future in as_completed(futures):
            url = futures[future]
            try:
                urls[url] = future.result()
            except Exception:  # noqa: BLE001
                urls[url] = False
            done += 1
            if done % 500 == 0:
                print(f"  checked {done}/{len(urls)} (live: {sum(urls.values())})")
    print(f"  live: {sum(urls.values())} / {len(urls)}")

    print("Writing playlists...")
    total = 0
    skipped: list[tuple[str, int]] = []
    for display, _tag in GENRES:
        chosen: list[tuple[str, str]] = []
        seen: set[str] = set()
        for station in candidates[display]:
            url = station_url(station)
            if not url or not urls.get(url):
                continue
            key = url.lower().rstrip("/")
            if key in seen:
                continue
            seen.add(key)
            chosen.append((station_name(station), url))
            if len(chosen) >= args.per_list:
                break

        if display == "Acoustic" and not args.no_extras:
            existing = {url.lower().rstrip("/") for _, url in chosen}
            extras = [
                (title, url) for title, url in ACOUSTIC_EXTRAS
                if url.lower().rstrip("/") not in existing and client.stream_ok(url)
            ]
            chosen = extras + chosen

        if not chosen:
            skipped.append((display, 0))
            continue
        write_playlist(args.out_dir, f"Жанр — {display}", display, chosen)
        total += len(chosen)
        print(f"  Жанр — {display}: {len(chosen)}")

    if not args.skip_cliamp:
        print("Refreshing cliamp-radio...")
        channels = [(name, url) for name, url in fetch_channels(client) if client.stream_ok(url)]
        write_playlist(args.out_dir, "cliamp-radio", "cliamp", channels)
        total += len(channels)
        print(f"  cliamp-radio: {len(channels)} channels")

    print()
    print(f"Stations written: {total}")
    if skipped:
        print(f"Genres with no live stations: {', '.join(name for name, _ in skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
