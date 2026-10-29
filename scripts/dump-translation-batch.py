#!/usr/bin/env python3
"""取出「下一批待译字段」，供人工或无人值守翻译使用。

用法：
    python3 scripts/dump-translation-batch.py              # 下一批（最小的还有余量的批次）
    python3 scripts/dump-translation-batch.py --batch 3    # 指定批次
    python3 scripts/dump-translation-batch.py --limit 20   # 本次只取 20 个字段（无人值守小步跑）
    python3 scripts/dump-translation-batch.py --json       # 输出 JSON（默认人读格式）
    python3 scripts/dump-translation-batch.py --chunk-bytes 5000   # 只取一小块（默认 5000）

输出只含**尚未翻译**且**未登记为可疑**的字段：
    - en 非空
    - zhHans 为空
    - 不在 docs/translations/flagged.json 里

切块（--chunk-bytes）说明：整批 dump 可能达 70KB，单次模型调用会撞 90s 超时上限
（实测 5KB/12 字段 ≈ 25s，安全）。切块时按队列顺序取整个案件，累计英文不超过
N 字节；单案超限则独成一块。连续多轮跑同一个 `--chunk-bytes` 即可自然推进，
因为已译字段会从待译集合里消失，不需要游标。
"""
import argparse
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
QUEUE = ROOT / "docs" / "TRANSLATION-QUEUE.json"
CASES = ROOT / "data" / "entities" / "cases.json"
FLAGGED = ROOT / "docs" / "translations" / "flagged.json"


def load_cases() -> dict:
    rows = json.loads(CASES.read_text(encoding="utf-8"))
    rows = rows if isinstance(rows, list) else rows.get("cases", [])
    return {row["id"]: row for row in rows}


def flagged_keys() -> set:
    if not FLAGGED.exists():
        return set()
    data = json.loads(FLAGGED.read_text(encoding="utf-8"))
    return {(item["caseId"], item["field"]) for item in data.get("items", [])}


def pending_items() -> list:
    queue = json.loads(QUEUE.read_text(encoding="utf-8"))
    cases = load_cases()
    skip = flagged_keys()
    out = []
    for item in queue["items"]:
        case = cases.get(item["caseId"])
        if not case:
            continue
        value = case.get(item["field"])
        if not isinstance(value, dict):
            continue
        if not (value.get("en") or "").strip():
            continue
        if (value.get("zhHans") or "").strip():
            continue
        if (item["caseId"], item["field"]) in skip:
            continue
        out.append({**item, "caseTitle": case.get("title") or item["caseId"]})
    return out


def group_by_case(items: list) -> list:
    """按队列顺序分组为 [(caseId, [item...])]，保持首次出现顺序。"""
    order: list = []
    buckets: dict = {}
    for item in items:
        cid = item["caseId"]
        if cid not in buckets:
            buckets[cid] = []
            order.append(cid)
        buckets[cid].append(item)
    return [(cid, buckets[cid]) for cid in order]


def chunk_pick(picked: list, limit: int) -> list:
    """按案件整取，累计英文不超过 limit 字节；单案超限则独成一块。"""
    out: list = []
    acc = 0
    for _cid, group in group_by_case(picked):
        size = sum(len(item.get("en") or "") for item in group)
        if out and acc + size > limit:
            break
        out.extend(group)
        acc += size
        if acc >= limit:
            break
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--batch", type=int)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--chunk-bytes", type=int, default=5000,
                        help="单块英文上限（字节）；0 = 不切块")
    args = parser.parse_args()

    items = pending_items()
    if not items:
        print("ALL_TRANSLATED")
        return

    batch = args.batch
    if batch is None:
        batch = min(item["batch"] for item in items)
    picked = [item for item in items if item["batch"] == batch]
    if not picked:
        print(f"BATCH_{batch}_EMPTY (剩余批次: {sorted({i['batch'] for i in items})})")
        return

    limit = args.chunk_bytes
    if limit and limit > 0 and len(picked) > 0:
        picked = chunk_pick(picked, limit)

    if args.json:
        print(json.dumps({"batch": batch, "count": len(picked), "items": picked},
                         ensure_ascii=False, indent=1))
        return

    import time

    cases = []
    for item in picked:
        if item["caseId"] not in cases:
            cases.append(item["caseId"])
    en_bytes = sum(len(item.get("en") or "") for item in picked)
    batch_rest = sum(1 for item in items if item["batch"] == batch) - len(picked)
    chunks_left = 0
    rest = [item for item in items if item["batch"] == batch]
    while rest:
        rest = rest[len(chunk_pick(rest, limit)):] if limit else []
        chunks_left += 1
    filename = f"batch-{batch:03d}-auto-{time.strftime('%H%M%S')}.json"

    print(f"BATCH {batch} | 本块 {len(picked)} 字段 | {len(cases)} 案 | {en_bytes} 字节 "
          f"| 该批剩余 {batch_rest} 字段 | 全库剩余 {len(items)} 字段 | 约还有 {chunks_left} 块")
    print(f"请写入 docs/translations/{filename}，文件里 \"batch\": {batch}")
    for case_id in cases:
        print(f"\n===== {case_id}")
        for item in picked:
            if item["caseId"] == case_id:
                print(f"[{item['field']}] {item['en']}")


if __name__ == "__main__":
    main()
