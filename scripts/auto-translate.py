#!/usr/bin/env python3
"""无人值守翻译器：直连中转站 API，不经过 Hermes 会话（不产生任何聊天记录）。

用法：
    python3 scripts/auto-translate.py                 # 跑到底（直到 ALL_TRANSLATED）
    python3 scripts/auto-translate.py --max-chunks 3  # 只跑 3 块
    python3 scripts/auto-translate.py --dry-run       # 只打印 prompt，不调 API

流程（每块）：
    dump-translation-batch.py --json  →  API  →  写 batch-XXX-auto-HHMMSS.json
    →  apply-translations.py  →  validate-data.py

设计要点：
    - 每次只译 5KB 左右的块，单次调用 300s 超时，不会撞 Hermes cron 的 90s 上限。
    - 幂等：已译字段自动从队列消失；中断后重跑即续。
    - 术语表 docs/TRANSLATION-GLOSSARY.md 全文注入 system prompt。
"""
from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GLOSSARY = ROOT / "docs" / "TRANSLATION-GLOSSARY.md"
TRANSLATIONS = ROOT / "docs" / "translations"
CONFIG = Path.home() / ("Library/Application Support/cn.org.hermesagent.desktop/"
                        "runtime/hermes-home/config.yaml")

FIELDS = ("culprit", "motive", "method", "evidence", "resolution")

SYSTEM_RULES = """你是《名侦探柯南》案件资料库的英译中译者。严格遵守下列规范：

1. 只翻译英文原文里已有的事实：不补充、不推测、不删减、不解释、不加评论。
2. 专名：术语表里有的用表内中文译名；术语表里没有的人名一律保留罗马字原样（例：Masayo Aoshima 就写 Masayo Aoshima），绝不自己拼汉字、猜译名。
3. 数字、地点、时间点、武器、人名必须与原文一一对应，不合并、不省略、不换算。
4. 保持原文句数与人称时态；原文两句译文也大致两句，不要压成一句概括。
5. culprit 字段若原文只有人名，译文也只有人名。
6. 原文本身就是残句或字段边界混乱（例如 motive 里装的是手法细节）时：该字段照原文直译，不要补全、不要重写。

输出格式：只输出一个 JSON 数组，不要任何解释、不要 markdown 代码块：
[{"caseId": "...", "field": "...", "zhHans": "..."}]
数组必须覆盖输入的每一条，顺序一致。"""


def read_api() -> tuple[str, str, str]:
    text = CONFIG.read_text(encoding="utf-8")

    def grab(key: str, default: str = "") -> str:
        m = re.search(rf"^\s*{key}:\s*['\"]?([^'\"\n]+)['\"]?\s*$", text, re.M)
        return m.group(1).strip() if m else default

    base = grab("base_url", "https://api.ls1223.cn/v1")
    key = grab("api_key")
    # config.yaml 里第一个 default: 往往是某个 provider 的模型名（本机是 mimo-v2.6-flash），
    # 与翻译任务无关。翻译固定走 deepseek-v4.1-flash：无 thinking、单块 3-6 秒。
    model = os.environ.get("TRANSLATE_MODEL", "deepseek-v4.1-flash")
    if not key:
        sys.exit("找不到 api_key，检查 config.yaml")
    return base.rstrip("/"), key, model


def dump_chunk() -> dict | None:
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "dump-translation-batch.py"),
                          "--json"], capture_output=True, text=True, cwd=ROOT)
    raw = out.stdout.strip()
    if not raw or raw.startswith("ALL_TRANSLATED"):
        return None
    if not raw.startswith("{"):
        sys.exit(f"dump 输出异常：{raw[:300]}")
    return json.loads(raw)


def remaining_count() -> int:
    out = subprocess.run([sys.executable, str(ROOT / "scripts" / "dump-translation-batch.py")],
                         capture_output=True, text=True, cwd=ROOT)
    m = re.search(r"全库剩余 (\d+) 字段", out.stdout)
    if m:
        return int(m.group(1))
    return 0 if "ALL_TRANSLATED" in out.stdout else -1


def call_api(base: str, key: str, model: str, chunk: dict, glossary: str) -> str:
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": SYSTEM_RULES + "\n\n===== 术语表 =====\n" + glossary},
            {"role": "user", "content": json.dumps(
                {"batch": chunk["batch"],
                 "items": [{"caseId": i["caseId"], "field": i["field"], "en": i["en"]}
                           for i in chunk["items"]]},
                ensure_ascii=False, indent=1)},
        ],
        "temperature": 0.2,
        "max_tokens": 8000,
    }
    req = urllib.request.Request(
        base + "/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=300) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def parse_items(content: str, chunk: dict) -> list[dict]:
    text = content.strip()
    text = re.sub(r"^```(?:json)?|```$", "", text, flags=re.M).strip()
    start, end = text.find("["), text.rfind("]")
    if start < 0 or end <= start:
        raise ValueError(f"模型没返回 JSON 数组：{text[:200]}")
    rows = json.loads(text[start:end + 1])
    allowed = {(i["caseId"], i["field"]) for i in chunk["items"]}
    out = []
    for row in rows:
        cid, field = row.get("caseId"), row.get("field")
        zh = (row.get("zhHans") or "").strip()
        if (cid, field) in allowed and zh and field in FIELDS:
            out.append({"caseId": cid, "field": field, "zhHans": zh})
    return out


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--max-chunks", type=int, default=200)
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    base, key, model = read_api()
    glossary = GLOSSARY.read_text(encoding="utf-8")
    TRANSLATIONS.mkdir(parents=True, exist_ok=True)

    done = 0
    consecutive_failures = 0
    while done < args.max_chunks:
        chunk = dump_chunk()
        if chunk is None:
            print("[DONE] 翻译队列已清空", flush=True)
            return
        batch = chunk["batch"]
        items = chunk["items"]
        print(f"[{time.strftime('%H:%M:%S')}] 第{done + 1}块 batch={batch} "
              f"{len(items)}字段 {sum(len(i['en']) for i in items)}字节 "
              f"| 全库剩余 {remaining_count()}", flush=True)
        if args.dry_run:
            print(json.dumps(items[:2], ensure_ascii=False)[:300])
            return

        translated: list[dict] = []
        for attempt in range(1, 4):
            try:
                content = call_api(base, key, model, chunk, glossary)
                translated = parse_items(content, chunk)
                if translated:
                    break
                print(f"  尝试{attempt}: 解析到 0 条，重试", flush=True)
            except Exception as exc:  # noqa: BLE001
                print(f"  尝试{attempt} 失败: {type(exc).__name__}: {exc}", flush=True)
                time.sleep(3 * attempt)
        if not translated:
            consecutive_failures += 1
            print(f"  [SKIP] 本块三次失败（连续 {consecutive_failures} 块），留待下次", flush=True)
            if consecutive_failures >= 3:
                print("[STOP] 连续 3 块失败，判定 API/网络异常，退出避免空转", flush=True)
                return
            time.sleep(5)
            continue
        consecutive_failures = 0

        path = TRANSLATIONS / f"batch-{batch:03d}-auto-{time.strftime('%H%M%S')}.json"
        path.write_text(json.dumps({"batch": batch, "translator": "ai",
                                    "glossaryVersion": "2026-10-27",
                                    "items": translated},
                                   ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        applied = subprocess.run([sys.executable, str(ROOT / "scripts" / "apply-translations.py")],
                                 capture_output=True, text=True, cwd=ROOT)
        print(f"  {path.name} {len(translated)}条 | apply: {applied.stdout.strip()[:200]}", flush=True)
        valid = subprocess.run([sys.executable, str(ROOT / "scripts" / "validate-data.py")],
                               capture_output=True, text=True, cwd=ROOT)
        ok = "VALIDATION_OK" in valid.stdout
        print(f"  validate: {'VALIDATION_OK' if ok else 'FAILED ' + valid.stdout[-300:]}", flush=True)
        if not ok:
            print("  [STOP] 校验失败，停止以免污染数据", flush=True)
            return
        done += 1

    print(f"[PAUSE] 已跑 {done} 块，全库剩余 {remaining_count()} 字段", flush=True)


if __name__ == "__main__":
    main()
