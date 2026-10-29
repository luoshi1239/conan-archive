#!/usr/bin/env python3
"""批量抓取 DCW 剧集/案件页面到本地缓存。

用法：python3 scripts/fetch-dcw-pages.py [--max N] [--workers W]
幂等：已存在且非空（>20KB）的文件跳过。
输出：data/raw/dcw-pages/<Page_Name>.html + docs/DCW-FETCH-STATE.json
"""
from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "data" / "raw" / "dcw-pages"
STATE = ROOT / "docs" / "DCW-FETCH-STATE.json"
PAGE_MAP = Path("/tmp/ca/dcw-page-map.json")
BASE = "https://www.detectiveconanworld.com/wiki/"
UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120 Safari/537.36"
MIN_BYTES = 20_000


def load_targets() -> list[str]:
    data = json.load(PAGE_MAP.open(encoding="utf-8"))
    pages = sorted(data["page2eps"].keys())
    return pages


def safe_name(page: str) -> str:
    return page.replace("/", "_").replace("?", "_").replace(":", "_")


def fetch_one(page: str) -> tuple[str, str, int]:
    dest = OUT_DIR / f"{safe_name(page)}.html"
    if dest.exists() and dest.stat().st_size >= MIN_BYTES:
        return page, "cached", dest.stat().st_size
    url = BASE + urllib.parse.quote(page)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    last_err = ""
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                body = resp.read()
            if len(body) < MIN_BYTES:
                last_err = f"too_small:{len(body)}"
                time.sleep(2 + attempt * 2)
                continue
            dest.write_bytes(body)
            return page, "ok", len(body)
        except Exception as exc:  # noqa: BLE001 - 记录一切失败
            last_err = type(exc).__name__ + ":" + str(exc)[:80]
            time.sleep(2 + attempt * 3)
    return page, f"fail:{last_err}", 0


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max", type=int, default=0, help="只抓前 N 个（调试用）")
    ap.add_argument("--workers", type=int, default=5)
    args = ap.parse_args()

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    targets = load_targets()
    if args.max:
        targets = targets[: args.max]

    print(f"targets={len(targets)} workers={args.workers}", flush=True)
    stats = {"ok": 0, "cached": 0, "fail": 0}
    failures: list[dict] = []
    started = time.time()

    with ThreadPoolExecutor(max_workers=args.workers) as pool:
        futures = {pool.submit(fetch_one, p): p for p in targets}
        for i, fut in enumerate(as_completed(futures), 1):
            page, status, size = fut.result()
            key = status.split(":")[0]
            stats[key if key in stats else "fail"] = stats.get(key if key in stats else "fail", 0) + 1
            if key not in ("ok", "cached"):
                failures.append({"page": page, "error": status})
            if i % 50 == 0 or i == len(targets):
                el = time.time() - started
                print(f"  [{i}/{len(targets)}] ok={stats['ok']} cached={stats['cached']} fail={stats['fail']} {el:.0f}s", flush=True)

    state = {
        "generatedAt": time.strftime("%Y-%m-%dT%H:%M:%S"),
        "baseUrl": BASE,
        "total": len(targets),
        "stats": stats,
        "failures": failures,
        "pageMapSource": str(PAGE_MAP),
    }
    STATE.write_text(json.dumps(state, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print(f"done ok={stats['ok']} cached={stats['cached']} fail={stats['fail']}")
    if failures:
        print("failures:", json.dumps(failures[:10], ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(main())
