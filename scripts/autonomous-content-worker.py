#!/usr/bin/env python3
"""Long-running deterministic maintenance worker for conan-archive.

The worker only propagates facts already present in repository data. It never
invents plot facts, spoiler fields, credentials, or external API responses.
Each pass is idempotent and records its result under .autonomous/.
"""
from __future__ import annotations

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
STATE = ROOT / ".autonomous"
LOG = STATE / "worker.log"
STATE_FILE = STATE / "state.json"
DEADLINE_SECONDS = 8 * 60 * 60
PASS_PAUSE_SECONDS = 20


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def log(message: str) -> None:
    STATE.mkdir(exist_ok=True)
    line = f"[{now()}] {message}\n"
    with LOG.open("a", encoding="utf-8") as handle:
        handle.write(line)
    print(line, end="", flush=True)


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, value) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def run(command: list[str]) -> tuple[int, str]:
    result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True)
    output = (result.stdout + result.stderr).strip()
    return result.returncode, output


def numbers_from_ref(value: str) -> list[int]:
    if not value.startswith("episode-"):
        return []
    tail = value.removeprefix("episode-")
    if "-" in tail:
        start, end = tail.split("-", 1)
        return list(range(int(start), int(end) + 1))
    return [int(tail)]


def explicit_relation_closure() -> dict[str, int]:
    """Audit explicit relations without mutating normalized episode data."""
    episodes_path = ROOT / "data/episodes/episodes.json"
    cases_path = ROOT / "data/entities/cases.json"
    arcs_path = ROOT / "data/manga/mainline-arcs.json"
    episodes = load_json(episodes_path)
    cases = load_json(cases_path)
    arcs = load_json(arcs_path)
    by_number = {row.get("number"): row for row in episodes}
    missing_cases = 0
    missing_arcs = 0
    for case in cases:
        for ref in case.get("animeRefs", []):
            for number in numbers_from_ref(ref):
                row = by_number.get(number)
                if not row or case.get("id") not in row.get("caseRefs", []):
                    missing_cases += 1
    for arc in arcs:
        for ref in arc.get("animeRefs", []):
            for number in numbers_from_ref(ref):
                row = by_number.get(number)
                if not row or (row.get("arc") != arc.get("id") and arc.get("id") not in row.get("arcRefs", [])):
                    missing_arcs += 1
    return {
        "episode_relation_changes": 0,
        "unclosed_case_relations": missing_cases,
        "unclosed_arc_relations": missing_arcs,
    }


def write_state(pass_number: int, changes: dict[str, int], commands: list[str]) -> None:
    payload = {
        "updatedAt": now(),
        "pass": pass_number,
        "changes": changes,
        "commands": commands,
    }
    save_json(STATE_FILE, payload)


def main() -> int:
    started = time.monotonic()
    pass_number = 0
    log(f"worker_started root={ROOT} budget_seconds={DEADLINE_SECONDS}")
    while time.monotonic() - started < DEADLINE_SECONDS:
        pass_number += 1
        log(f"pass_started number={pass_number}")
        commands = [
            "python3 scripts/normalize-episodes.py",
            "python3 scripts/enrich-mainline-episodes.py",
            "python3 scripts/enrich-arc-coverage.py",
            "python3 scripts/enrich-catalog-records.py",
        ]
        changes = None
        failed = False
        for command in commands:
            code, output = run(command.split())
            compact = output.replace("\n", " | ")[-800:]
            log(f"pass={pass_number} command={' '.join(command.split())} exit={code} output={compact}")
            if code != 0:
                failed = True
                break
        if not failed:
            changes = explicit_relation_closure()
        commands.extend([
            "python3 scripts/report-content-coverage.py",
            "python3 scripts/report-relation-closure.py",
            "python3 scripts/validate-data.py",
            "node --check app.js",
            "node --check data.js",
        ])
        if not failed:
            for command in commands[4:]:
                code, output = run(command.split())
                compact = output.replace("\n", " | ")[-800:]
                log(f"pass={pass_number} command={' '.join(command.split())} exit={code} output={compact}")
                if code != 0:
                    failed = True
                    break
        write_state(pass_number, changes, commands)
        if failed:
            log(f"worker_stopped reason=verification_failure pass={pass_number}")
            return 1
        if sum(changes.values()) == 0:
            log(f"pass={pass_number} no_new_explicit_relations; waiting_before_next_audit")
        else:
            log(f"pass={pass_number} changed={changes}")
        time.sleep(PASS_PAUSE_SECONDS)
    log(f"worker_finished passes={pass_number} elapsed_seconds={int(time.monotonic() - started)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
