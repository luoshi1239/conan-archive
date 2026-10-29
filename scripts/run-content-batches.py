#!/usr/bin/env python3
"""Batch-driven maintenance worker: process pending reviewed batches once.

Unlike the old time-loop worker, this process stops after the queue is empty or
verification fails. It never treats repeated validation as content progress.
"""
from __future__ import annotations

import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE_DIR = ROOT / ".autonomous"
STATE_FILE = STATE_DIR / "batch-worker-state.json"
LOG = STATE_DIR / "batch-worker.log"
BATCHES = ROOT / "docs" / "CONTENT-BATCHES.json"


def now():
    return datetime.now(timezone.utc).isoformat()


def log(message):
    STATE_DIR.mkdir(exist_ok=True)
    line = f"[{now()}] {message}\n"
    LOG.open("a", encoding="utf-8").write(line)
    print(line, end="", flush=True)


def run(command):
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip().replace("\n", " | ")[-1000:]
    log(f"command={' '.join(command)} exit={result.returncode} output={output}")
    return result.returncode


def save(state):
    STATE_DIR.mkdir(exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main():
    batches = json.loads(BATCHES.read_text(encoding="utf-8"))["batches"]
    candidates = [
        batch for batch in batches
        if batch.get("status") in {"reviewed", "candidate"}
        and batch.get("batchId") not in {"p0-regression-baseline"}
    ]
    state = {"startedAt": now(), "queue": [b["batchId"] for b in candidates], "processed": [], "status": "running"}
    save(state)
    log(f"worker_started queue={len(candidates)}")
    for batch in candidates:
        batch_id = batch["batchId"]
        log(f"batch_started id={batch_id} status={batch.get('status')}")
        if batch_id.startswith("p2-manga-file") and batch.get("status") == "reviewed":
            code = run([sys.executable, "scripts/apply-reviewed-candidates.py", "--batch-id", batch_id])
            if code != 0:
                state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        run([sys.executable, "scripts/validate-candidates.py"])
        if run([sys.executable, "scripts/normalize-episodes.py"]) != 0:
            state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        if run([sys.executable, "scripts/report-content-coverage.py"]) != 0:
            state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        if run([sys.executable, "scripts/report-field-confidence.py"]) != 0:
            state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        if run([sys.executable, "scripts/report-batch-progress.py"]) != 0:
            state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        if run([sys.executable, "scripts/report-relation-closure.py"]) != 0:
            state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        if run([sys.executable, "scripts/validate-data.py"]) != 0:
            state["status"] = "failed"; state["failedBatch"] = batch_id; save(state); return 1
        state["processed"].append(batch_id)
        save(state)
        log(f"batch_finished id={batch_id}")
    state["status"] = "queue_empty"
    state["finishedAt"] = now()
    save(state)
    log("worker_finished reason=queue_empty")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
