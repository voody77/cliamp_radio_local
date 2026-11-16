"""Radio Browser client, stream verification, and TOML playlist writing.

All network checks are bound to the source address of a chosen interface
(Wi-Fi by default), so a VPN tunnel such as tun0 cannot silently carry the
traffic.
"""

from __future__ import annotations

import json
import os
import re
import subprocess
import threading
import time
import urllib.parse
from typing import Iterable, Sequence
from urllib.parse import urlsplit

import requests
from requests.adapters import HTTPAdapter

DEFAULT_API = "https://de1.api.radio-browser.info/json"
DEFAULT_OUT_DIR = os.path.expanduser("~/.config/cliamp/playlists")
DEFAULT_UA = "cliamp-radio-local/1.0"

WRAPPER_EXTS = (
    ".m3u", ".m3u8", ".pls", ".xspf", ".asx", ".ram", ".smil", ".html", ".htm",
)


def run(cmd: Sequence[str], timeout: int = 60) -> subprocess.CompletedProcess:
    return subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)


def default_interface() -> str:
    """Return the interface of the default IPv4 route."""
    out = run(["ip", "route", "show", "default"]).stdout
    match = re.search(r"\bdev\s+(\S+)", out)
    if not match:
        raise RuntimeError("could not determine the default network interface")
    return match.group(1)


def interface_ipv4(iface: str) -> str:
    out = run(["ip", "-4", "-o", "addr", "show", "dev", iface]).stdout
    match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)/", out)
    if not match:
        raise RuntimeError(f"interface {iface} has no IPv4 address")
    return match.group(1)


class _SourceAdapter(HTTPAdapter):
    """HTTP adapter that binds outgoing sockets to a local source address."""

    def __init__(self, source: tuple[str, int], **kwargs):
        self.source = source
        super().__init__(**kwargs)

    def init_poolmanager(self, *args, **kwargs):
        kwargs["source_address"] = self.source
        return super().init_poolmanager(*args, **kwargs)


class RadioClient:
    def __init__(
        self,
        api: str = DEFAULT_API,
        iface: str | None = None,
        workers: int = 64,
        page: int = 10,
        timeout: tuple[float, float] = (6.0, 8.0),
        user_agent: str = DEFAULT_UA,
    ):
        self.api = api.rstrip("/")
        self.iface = iface or default_interface()
        self.source_ip = interface_ipv4(self.iface)
        self.workers = workers
        self.page = page
        self.timeout = timeout
        self.user_agent = user_agent
        self._tls = threading.local()

    # -- sessions ---------------------------------------------------------

    def _session(self) -> requests.Session:
        session = getattr(self._tls, "session", None)
        if session is None:
            session = requests.Session()
            adapter = _SourceAdapter((self.source_ip, 0), pool_connections=4, pool_maxsize=8)
            session.mount("http://", adapter)
            session.mount("https://", adapter)
            session.headers.update({"User-Agent": self.user_agent})
            self._tls.session = session
        return session

    # -- catalog API ------------------------------------------------------

    def curl_text(self, url: str, tries: int = 5) -> str:
        last = None
        for attempt in range(tries):
            try:
                proc = run(
                    [
                        "curl", "-sS", "--http1.1", "--max-time", "45",
                        "--interface", self.iface, "-A", self.user_agent, url,
                    ]
                )
                if proc.returncode == 0 and proc.stdout:
                    return proc.stdout
                last = (proc.stderr or "").strip()[:200]
            except Exception as exc:  # noqa: BLE001
                last = str(exc)[:200]
            time.sleep(0.5 + attempt * 0.5)
        raise RuntimeError(f"curl failed for {url}: {last}")

    def api_json(self, url: str, tries: int = 5):
        last = None
        for attempt in range(tries):
            try:
                return json.loads(self.curl_text(url))
            except Exception as exc:  # noqa: BLE001
                last = str(exc)[:200]
            time.sleep(0.5 + attempt * 0.5)
        raise RuntimeError(f"bad JSON from {url}: {last}")

    def search(self, params: dict, limit: int | None = None, offset: int = 0) -> list[dict]:
        query = dict(params)
        query.update({
            "limit": str(limit or self.page),
            "offset": str(offset),
            "hidebroken": "true",
            "order": "votes",
            "reverse": "true",
        })
        url = f"{self.api}/stations/search?{urllib.parse.urlencode(query)}"
        return self.api_json(url)

    def candidates(self, params: dict, want: int, log=print) -> list[dict]:
        """Collect up to want unique stations, in vote order."""
        seen: set[str] = set()
        out: list[dict] = []
        offset = 0
        while len(out) < want:
            try:
                page = self.search(params, offset=offset)
            except Exception as exc:  # noqa: BLE001
                log(f"    ! page failed at offset {offset}: {exc}")
                break
            if not page:
                break
            for station in page:
                url = station_url(station)
                if not url or url.lower() in seen:
                    continue
                seen.add(url.lower())
                out.append(station)
                if len(out) >= want:
                    break
            offset += self.page
        return out

    def egress(self) -> dict:
        return json.loads(self.curl_text("https://ipinfo.io/json"))

    # -- stream checks ----------------------------------------------------

    def stream_ok(self, url: str) -> bool:
        if not url.lower().startswith(("http://", "https://")):
            return False
        try:
            if urlsplit(url.lower()).path.endswith(WRAPPER_EXTS):
                return False
        except ValueError:
            return False
        try:
            response = self._session().get(
                url,
                headers={"Icy-MetaData": "1", "Accept": "*/*"},
                stream=True,
                timeout=self.timeout,
                allow_redirects=True,
            )
        except Exception:  # noqa: BLE001
            return False
        try:
            if response.status_code not in (200, 206):
                return False
            content_type = (response.headers.get("content-type") or "").lower()
            if "html" in content_type or "text/" in content_type or "json" in content_type:
                return False
            chunk = b""
            try:
                chunk = next(response.iter_content(4096), b"")
            except Exception:  # noqa: BLE001
                chunk = b""
            magic = (
                chunk[:4] in (b"OggS", b"fLaC", b"RIFF")
                or chunk[:3] == b"ID3"
                or (len(chunk) > 1 and chunk[0] == 0xFF and (chunk[1] & 0xE0) == 0xE0)
            )
            if magic:
                return True
            if content_type.startswith(("audio/", "video/")):
                return True
            if content_type in (
                "application/ogg", "application/octet-stream", "binary/octet-stream",
            ):
                return bool(chunk)
            return False
        finally:
            response.close()


def station_url(station: dict) -> str:
    return (station.get("url_resolved") or station.get("url") or "").strip()


def station_name(station: dict) -> str:
    return re.sub(r"\s+", " ", (station.get("name") or "").strip()) or "Radio"


def sanitize(name: str) -> str:
    name = re.sub(r"[/\\:*?\"<>|\x00-\x1f]", "-", name)
    name = re.sub(r"\s+", " ", name).strip().strip(".")
    return name[:120].rstrip(" .")


def toml_str(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def write_tracks(path: str, tracks: Iterable[dict]) -> None:
    lines = ["# Generated by cliamp_radio_local.", ""]
    for track in tracks:
        lines.append("[[track]]")
        lines.append(f"path = {toml_str(track['path'])}")
        lines.append(f"title = {toml_str(track['title'])}")
        if track.get("genre"):
            lines.append(f"genre = {toml_str(track['genre'])}")
        lines.append("realtime = true")
        lines.append("")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("\n".join(lines))


def write_playlist(
    out_dir: str,
    filename: str,
    genre: str,
    stations: Iterable[tuple[str, str]],
) -> str:
    path = os.path.join(out_dir, sanitize(filename) + ".toml")
    tracks = [
        {"path": url, "title": title, "genre": genre}
        for title, url in stations
    ]
    write_tracks(path, tracks)
    return path
