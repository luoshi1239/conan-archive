#!/usr/bin/env python3
"""Shared helper: expand case animeRefs into individual episode ids.

animeRefs uses two formats in this repo:
  "episode-0094"          single episode
  "episode-0057-0058"     multi-episode arc span (also "episode-0068-0070")

Scripts that compared ids literally treated every span as missing, which is
why coverage reconciliation under-reported deep episodes.
"""

from __future__ import annotations

import re

_SPAN = re.compile(r"^episode-(\d{4})(?:-(\d{4}))?$")


def expand_episode_refs(refs) -> set[str]:
    """Return every covered episode id ('episode-0057' ... 'episode-0058')."""
    out: set[str] = set()
    for ref in refs or []:
        if not isinstance(ref, str):
            continue
        m = _SPAN.match(ref)
        if not m:
            continue
        start = int(m.group(1))
        end = int(m.group(2)) if m.group(2) else start
        if end < start:
            start, end = end, start
        for n in range(start, end + 1):
            out.add(f"episode-{n:04d}")
    return out


def expand_case_episodes(cases) -> dict[str, set[str]]:
    """For each deep case id, the set of episodes it covers."""
    return {c["id"]: expand_episode_refs(c.get("animeRefs")) for c in cases}
