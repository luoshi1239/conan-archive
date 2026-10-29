#!/usr/bin/env python3
"""Print per-episode detailStatus/coverage/caseRefs for a range (diagnostic)."""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def main(argv: list[str]) -> int:
    lo = int(argv[1]) if len(argv) > 1 else 90
    hi = int(argv[2]) if len(argv) > 2 else 97
    data = json.loads((ROOT / "data/episodes/episodes.json").read_text(encoding="utf-8"))
    rows = data["episodes"] if isinstance(data, dict) else data
    idx = {r.get("number"): r for r in rows}
    for n in range(lo, hi + 1):
        r = idx.get(n)
        if not r:
            print(f"{n} MISSING")
            continue
        cov = r.get("coverage") or {}
        flags = "".join(
            k[0].upper() for k in ("directory", "basicFacts", "structure", "deepSpoilers") if cov.get(k) is True
        )
        print(
            f"{n:>4} {r.get('detailStatus'):<11} cov={flags or '-':<5} "
            f"cases={r.get('caseRefs') or []} title={(r.get('title') or {}).get('zhHans', '')[:20]}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv))
