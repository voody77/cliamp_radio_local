#!/usr/bin/env python3
"""Build Russian per-genre playlists for cliamp.

Creates one playlist per genre: "Россия — <Name>.toml", using only stations
located in Russia. Every stream is verified from this host.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

from radio_playlists import (
    DEFAULT_API,
    DEFAULT_OUT_DIR,
    GENRES,
    RadioClient,
    station_name,
    station_url,
    write_playlist,
)
from radio_playlists.genres import RUSSIA_POP_EXTRAS


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out-dir", default=DEFAULT_OUT_DIR, help="playlist directory")
    parser.add_argument("--api", default=DEFAULT_API, help="Radio Browser API base")
    parser.add_argument("--iface", default=None, help="interface to bind to (default: default route)")
    parser.add_argument("--per-list", type=int, default=50, help="stations kept per genre")
    parser.add_argument("--candidates", type=int, default=120, help="stations checked per genre")
    parser.add_argument("--min-stations", type=int, default=5, help="skip genres below this count")
    parser.add_argument("--include-small", action="store_true", help="keep lists below --min-stations")
    parser.add_argument("--workers", type=int, default=64, help="parallel stream checks")
    parser.add_argument("--page", type=int, default=10, help="catalog page size")
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

    for path in glob.glob(os.path.join(args.out_dir, "Россия.toml")):
        os.remove(path)
        print("Removed the single Россия.toml playlist")

    candidates: dict[str, list[dict]] = {}
    print(f"Collecting Russian candidates for {len(GENRES)} genres...")
    for index, (display, tag) in enumerate(GENRES, 1):
        stations = client.candidates(
            {"countrycode": "RU", "tag": tag, "tagExact": "true"}, args.candidates
        )
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
            if done % 300 == 0:
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

        if display == "Pop" and chosen and not args.no_extras:
            existing = {url.lower().rstrip("/") for _, url in chosen}
            extras = [
                (title, url) for title, url in RUSSIA_POP_EXTRAS
                if url.lower().rstrip("/") not in existing and client.stream_ok(url)
            ]
            chosen = extras + chosen

        if len(chosen) < args.min_stations and not args.include_small:
            skipped.append((display, len(chosen)))
            continue
        if not chosen:
            skipped.append((display, 0))
            continue
        write_playlist(args.out_dir, f"Россия — {display}", f"Россия / {display}", chosen)
        total += len(chosen)
        print(f"  Россия — {display}: {len(chosen)}")

    print()
    print(f"Stations written: {total}")
    print(f"Skipped genres (< {args.min_stations} live): {len(skipped)}")
    for display, count in skipped:
        print(f"  {count:3d}  {display}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
