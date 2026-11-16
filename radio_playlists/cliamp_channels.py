"""The built-in cliamp radio channel list."""

from __future__ import annotations

from .core import RadioClient

CLIAMP_M3U = "https://radio.cliamp.stream/streams.m3u"


def fetch_channels(client: RadioClient) -> list[tuple[str, str]]:
    text = client.curl_text(CLIAMP_M3U)
    channels: list[tuple[str, str]] = []
    title = None
    for line in text.splitlines():
        line = line.strip()
        if line.upper().startswith("#EXTINF"):
            title = line.split(",", 1)[1].strip() if "," in line else "cliamp channel"
        elif line and not line.startswith("#") and title:
            channels.append((title, line))
            title = None
    return channels
