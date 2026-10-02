"""Loglan Bench runner via the local OpenCode server (stateless session/generate).

Reconstructed runner. Methodology deviations from src/benchmark.py (documented on purpose):
- SYSTEM_PROMPT is prepended to the user prompt: the endpoint body is only {"prompt": ...},
  there is no separate system channel (verified against GET /openapi.json).
- No temperature: benchmark uses T=0.2/0.3, the endpoint exposes no such parameter.
- input/output tokens are 0: the endpoint returns {"data": {"text": ...}} only.
- An empty completion (HTTP 200 with data.text == "") is a FAILED attempt and is retried
  up to LOGLAN_BENCH_RETRIES times (default 3; fill passes use 8). Retries are mandatory:
  without them ~42% of cells come back empty.

Resume semantics (idempotent):
- a non-empty A/B response is never re-requested;
- translation runs are tracked per run_index (1..5); only missing/empty runs are re-requested;
- translation top-level "response" is refreshed to the first non-empty run after each save;
- saved prompts/gold of completed entries are reused verbatim (never rebuilt), so a resumed
  run keeps byte-identical prompts even if the retriever would change.

Usage:
    python scripts/run_opencode_api.py [--limit N] [--dry]
Environment:
    LOGLAN_BENCH_RETRIES (default 3), LOGLAN_BENCH_WORKERS (default 3)
"""

import argparse
import base64
import json
import os
import sys
import threading
import time
import urllib.error
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, ".")

try:
    from src.config import DATA_DIR, RAW_RESULTS_DIR
    from src.retriever import LoglanRetriever
    from src.prompts import (
        SYSTEM_PROMPT,
        DISAMBIGUATION_PROMPT_TEMPLATE,
        SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
        BENCHMARK_PROMPT_TEMPLATE,
    )
except ImportError:
    from config import DATA_DIR, RAW_RESULTS_DIR
    from retriever import LoglanRetriever
    from prompts import (  # type: ignore
        SYSTEM_PROMPT,
        DISAMBIGUATION_PROMPT_TEMPLATE,
        SLOT_IDENTIFICATION_PROMPT_TEMPLATE,
        BENCHMARK_PROMPT_TEMPLATE,
    )

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")

MODEL_TAG = "opencode_mimo-v2.6-flash-free"
PROVIDER = "opencode-server/session-generate"
SESSION_TITLES = ["loglan-bench-0", "loglan-bench-1", "loglan-bench-2"]
RUNS = 5
RETRIES = int(os.environ.get("LOGLAN_BENCH_RETRIES", "3"))
WORKERS = int(os.environ.get("LOGLAN_BENCH_WORKERS", "3"))

OUT_FILE = RAW_RESULTS_DIR / f"{MODEL_TAG}_results.json"
DATASET = DATA_DIR / "benchmark_dataset.json"


# --------------------------------------------------------------------------- API client
class OpenCodeClient:
    def __init__(self) -> None:
        svc = json.loads((Path.home() / ".config" / "opencode" / "service.json").read_text())
        self.base = f"http://127.0.0.1:{svc['port']}"
        token = base64.b64encode(f"opencode:{svc['password']}".encode()).decode()
        self.auth = {"Authorization": f"Basic {token}", "Content-Type": "application/json"}

    def _request(self, method: str, path: str, payload: dict | None = None,
                 timeout: int = 600, attempts: int = 4) -> dict:
        body = json.dumps(payload).encode() if payload is not None else None
        last = None
        for i in range(attempts):
            req = urllib.request.Request(self.base + path, data=body,
                                         headers=self.auth, method=method)
            try:
                with urllib.request.urlopen(req, timeout=timeout) as r:
                    return json.loads(r.read().decode())
            except urllib.error.HTTPError as e:
                detail = e.read().decode(errors="replace")[:200]
                last = f"HTTP {e.code}: {detail}"
                if e.code in (400, 404):
                    raise RuntimeError(last) from None
            except Exception as e:  # network hiccup, timeout
                last = repr(e)
            time.sleep(2 * (i + 1))
        raise RuntimeError(f"{method} {path} failed after {attempts} attempts: {last}")

    def session_ids(self) -> list[str]:
        """Reuse the pinned mimo sessions; create them if they were cleaned up."""
        sessions = self._request("GET", "/api/session")["data"]
        by_title = {s.get("title"): s["id"] for s in sessions}
        ids = []
        for title in SESSION_TITLES:
            if title in by_title:
                ids.append(by_title[title])
            else:
                created = self._request("POST", "/api/session", {
                    "title": title,
                    "model": {"id": "mimo-v2.6-flash-free", "providerID": "opencode"},
                })
                ids.append(created["data"]["id"])
        return ids

    def generate(self, session_id: str, prompt: str) -> tuple[str, float]:
        """Returns (text, latency_sec). Empty text is a valid-but-failed response."""
        t0 = time.perf_counter()
        data = self._request("POST", f"/api/session/{session_id}/generate",
                             {"prompt": prompt}, timeout=900)
        return data["data"].get("text", ""), time.perf_counter() - t0


# --------------------------------------------------------------------------- prompts
def build_prompt(case: dict, retriever: LoglanRetriever) -> str:
    cat = case["category"]
    if cat == "disambiguation":
        ctx = retriever.retrieve_context(case["english"] + " " + case.get("loglan", ""))
        body = DISAMBIGUATION_PROMPT_TEMPLATE.format(
            english=case["english"], loglan=case.get("loglan", ""), context=ctx)
    elif cat == "slot_identification":
        ctx = retriever.retrieve_context(case["predicate"])
        body = SLOT_IDENTIFICATION_PROMPT_TEMPLATE.format(
            predicate=case["predicate"], sentence=case.get("sentence", ""), context=ctx)
    else:
        ctx = retriever.retrieve_context(case["english"])
        body = BENCHMARK_PROMPT_TEMPLATE.format(
            question=f"Translate '{case['english']}' to unambiguous Loglan.", context=ctx)
    return SYSTEM_PROMPT + "\n\n" + body


# --------------------------------------------------------------------------- state
def load_state() -> tuple[dict, dict[str, dict]]:
    if OUT_FILE.exists():
        data = json.loads(OUT_FILE.read_text(encoding="utf-8"))
    else:
        data = {"model": MODEL_TAG, "provider": PROVIDER,
                "timestamp": "", "total_cases": 0, "results": []}
    by_id = {r["case_id"]: r for r in data["results"]}
    return data, by_id


def first_non_empty(runs: list[dict]) -> str:
    for r in sorted(runs, key=lambda x: x.get("run_index", 0)):
        if r.get("response"):
            return r["response"]
    return ""


def pending_jobs(by_id: dict, dataset: list[dict]) -> list[tuple]:
    """[(case_id, run_index)] — run_index 0 for A/B, 1..5 for translation."""
    jobs = []
    for case in dataset:
        cid, cat = case["id"], case["category"]
        entry = by_id.get(cid)
        if cat == "translation_consistency":
            runs = {r.get("run_index"): r for r in (entry or {}).get("repeated_runs", [])}
            for i in range(1, RUNS + 1):
                if not runs.get(i, {}).get("response"):
                    jobs.append((cid, i))
        else:
            if not (entry or {}).get("response"):
                jobs.append((cid, 0))
    return jobs


def save(data: dict) -> None:
    data["timestamp"] = time.strftime("%Y-%m-%d %H:%M:%S")
    data["total_cases"] = len(data["results"])
    tmp = OUT_FILE.parent / (OUT_FILE.name + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
    os.replace(tmp, OUT_FILE)


# --------------------------------------------------------------------------- main
def main() -> None:
    ap = argparse.ArgumentParser(description="Loglan Bench via OpenCode session/generate")
    ap.add_argument("--limit", type=int, default=0, help="stop after N completed jobs")
    ap.add_argument("--dry", action="store_true", help="print pending jobs and exit")
    args = ap.parse_args()

    cases = json.loads(DATASET.read_text(encoding="utf-8"))["cases"]
    data, by_id = load_state()
    jobs = pending_jobs(by_id, cases)
    print(f"Jobs: {len([c for c in cases if c['category'] != 'translation_consistency']) * 1 + RUNS * len([c for c in cases if c['category'] == 'translation_consistency'])} total, "
          f"{len(jobs)} pending", flush=True)

    if args.dry:
        for cid, run in jobs:
            print("  pending:", cid, f"run={run}" if run else "")
        return

    client = OpenCodeClient()
    sessions = client.session_ids()
    print(f"Model: {MODEL_TAG} via {client.base}", flush=True)
    print(f"Sessions: {sessions}  retries={RETRIES} workers={WORKERS}", flush=True)

    retriever = LoglanRetriever() if any(not by_id.get(c["id"]) for c in cases) else None
    case_by_id = {c["id"]: c for c in cases}
    pool: list[str] = list(sessions)
    pool_lock = threading.Lock()
    state_lock = threading.Lock()
    counter = {"n": 0, "errors": 0, "done": 0}
    t_start = time.time()
    stop = args.limit and args.limit <= 0

    def run_job(job: tuple) -> None:
        nonlocal stop
        if stop:
            return
        cid, run_idx = job
        case = case_by_id[cid]
        with pool_lock:
            if not pool:
                return
            sid = pool.pop()

        text, lat, prompt = "", 0.0, None
        try:
            entry = by_id.get(cid)
            prompt = (entry or {}).get("prompt") or build_prompt(case, retriever)
            for attempt in range(1, RETRIES + 1):
                text, lat = client.generate(sid, prompt)
                if text:
                    break
                print(f"    [{cid} run={run_idx}] empty attempt {attempt}/{RETRIES}", flush=True)
        except Exception as e:
            counter["errors"] += 1
            print(f"    [{cid} run={run_idx}] ERR {e}", flush=True)
        finally:
            with pool_lock:
                pool.append(sid)

        with state_lock:
            counter["n"] += 1
            if not text:
                counter["errors"] += 1
            entry = by_id.get(cid)
            if entry is None:
                entry = {
                    "case_id": cid, "category": case["category"],
                    "prompt": prompt or "", "response": "", "input_tokens": 0,
                    "output_tokens": 0, "latency_sec": 0.0, "gold": case,
                }
                data["results"].append(entry)
                by_id[cid] = entry
            if case["category"] == "translation_consistency":
                runs = {r.get("run_index"): r for r in entry.get("repeated_runs", [])}
                runs[run_idx] = {"run_index": run_idx, "response": text, "latency_sec": round(lat, 3)}
                entry["repeated_runs"] = [runs[i] for i in sorted(runs) if i in runs]
                entry["response"] = first_non_empty(entry["repeated_runs"])
            elif text:
                entry["response"] = text
                entry["latency_sec"] = round(lat, 3)
            if text:
                counter["done"] += 1
            save(data)

        n = counter["n"]
        tag = f"[{n}/{len(jobs)}] {cid}" + (f" run={run_idx}" if run_idx else "")
        if text:
            print(f"{tag} {lat:.2f}s {len(text)} chars", flush=True)
        else:
            print(f"{tag} {lat:.2f}s 0 chars ERR=empty completion", flush=True)
        if args.limit and counter["done"] >= args.limit:
            stop = True

    with ThreadPoolExecutor(max_workers=min(WORKERS, len(sessions))) as ex:
        list(ex.map(run_job, jobs))

    print(f"\nDone: {counter['n']} calls in {time.time() - t_start:.1f}s "
          f"({counter['errors']} errors) -> {OUT_FILE}", flush=True)


if __name__ == "__main__":
    main()
