#!/usr/bin/env python3
"""Re-check every stream in existing cliamp playlists.

Reports dead links and, with --prune, removes them from the playlist files.
Exit status is 1 when dead links remain.
"""

from __future__ import annotations

import argparse
import glob
import os
import sys
import tomllib
from concurrent.futures import ThreadPoolExecutor, as_completed

from radio_playlists import DEFAULT_OUT_DIR, RadioClient, write_tracks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("playlists", nargs="*", help="TOML files (default: whole --dir)")
    parser.add_argument("--dir", default=DEFAULT_OUT_DIR, help="playlist directory")
    parser.add_argument("--iface", default=None, help="interface to bind to (default: default route)")
    parser.add_argument("--workers", type=int, default=64, help="parallel stream checks")
    parser.add_argument("--prune", action="store_true", help="rewrite files without dead links")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    paths = args.playlists or sorted(glob.glob(os.path.join(args.dir, "*.toml")))
    if not paths:
        print("No playlists found.")
        return 0

    client = RadioClient(iface=args.iface, workers=args.workers)
    print(f"Interface: {client.iface} ({client.source_ip})")

    playlists: dict[str, list[dict]] = {}
    urls: dict[str, bool] = {}
    for path in paths:
        try:
            with open(path, "rb") as handle:
                data = tomllib.load(handle)
        except Exception as exc:  # noqa: BLE001
            print(f"! cannot read {path}: {exc}")
            continue
        tracks = [track for track in data.get("track", []) if track.get("path")]
        playlists[path] = tracks
        for track in tracks:
            urls.setdefault(track["path"], False)

    print(f"Checking {len(urls)} unique streams in {len(playlists)} playlists...")
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
            if done % 250 == 0:
                print(f"  checked {done}/{len(urls)}")

    dead_total = 0
    for path, tracks in playlists.items():
        dead = [track for track in tracks if not urls.get(track["path"])]
        dead_total += len(dead)
        if not dead:
            print(f"  OK   {os.path.basename(path)} ({len(tracks)})")
            continue
        print(f"  DEAD {os.path.basename(path)}: {len(dead)}/{len(tracks)}")
        for track in dead:
            print(f"       {track.get('title', '?')} — {track['path']}")
        if args.prune:
            write_tracks(path, [track for track in tracks if urls.get(track["path"])])
            print(f"       pruned to {len(tracks) - len(dead)} tracks")

    print()
    print(f"Dead streams: {dead_total}")
    return 1 if dead_total and not args.prune else 0


if __name__ == "__main__":
    sys.exit(main())
