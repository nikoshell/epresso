#!/usr/bin/env python3
"""Build-time regression gate.

Builds a bundled theme a few times, divides the best run by a fixed pure-Python
CPU workload measured in the same process, and compares that *ratio* to a
committed baseline. Dividing by the reference workload cancels most of the
difference between a laptop and a CI runner, so one baseline survives both.

    python scripts/bench.py                    # gate against the baseline
    python scripts/bench.py --update           # re-record the baseline
    python scripts/bench.py --runs 5 --theme themes/blog

Exit codes: 0 = within threshold, 1 = regression, 2 = the build itself failed.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import statistics
import subprocess
import sys
import time
from collections.abc import Callable
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
BASELINE = REPO / "scripts" / "perf_baseline.json"
DEFAULT_THEME = "themes/docs"
DEFAULT_THRESHOLD = 0.25
REFERENCE_ITERS = 5_000_000

# ponytail: one arithmetic loop as the machine-speed yardstick. It approximates
# CPU speed well enough for a 25% gate but not memory/IO-bound drift; if this
# ever produces false positives, replace the ratio with a per-runner-side baseline.
def _reference_seconds(runs: int = 3) -> float:
    """Best-of-``runs`` wall time of a fixed pure-Python workload."""

    def work() -> int:
        acc = 0
        for i in range(REFERENCE_ITERS):
            acc = (acc + i * i) % 1_000_003
        return acc

    return min(_time(work) for _ in range(runs))


def _time(fn: Callable[[], object]) -> float:
    start = time.perf_counter()
    fn()
    return time.perf_counter() - start


def _pages_built(stdout: str) -> int:
    """Parse ``Built N pages`` out of the CLI's success line.

    Needed because a wrong ``--theme`` path is not an error to the CLI: it loads
    an empty config and reports a successful zero-page build in ~0.2 s. Without
    this check that reads as a 90% speedup and the gate waves it through.
    """
    match = re.search(r"Built (\d+) pages", stdout)
    return int(match.group(1)) if match else -1


def build_seconds(theme: str, runs: int) -> tuple[float, float]:
    """Return ``(best, median)`` wall seconds for a full CLI build of ``theme``.

    Times the whole command, so interpreter startup and imports are included —
    that is the number a user waits for. ``cwd`` is the repo root so the theme
    paths and the installed package resolve the same way as in CI.
    """
    cmd = [sys.executable, "-m", "epresso", "build", theme]
    times: list[float] = []
    for _ in range(runs):
        start = time.perf_counter()
        proc = subprocess.run(cmd, cwd=REPO, capture_output=True, text=True)
        times.append(time.perf_counter() - start)
        if proc.returncode != 0:
            sys.stderr.write(f"build failed ({theme}):\n{proc.stdout}\n{proc.stderr}\n")
            raise SystemExit(2)
        pages = _pages_built(proc.stdout)
        if pages <= 0:
            sys.stderr.write(
                f"build produced no pages (--theme {theme}):\n{proc.stdout}\n"
                "that is a silent no-op, not a fast build — check the theme path\n"
            )
            raise SystemExit(2)
    times.sort()
    return times[0], statistics.median(times)


def compare(current: float, baseline: float, threshold: float) -> tuple[bool, float]:
    """``(ok, delta)`` for a ratio against the baseline; positive delta = slower."""
    delta = (current - baseline) / baseline
    return delta <= threshold, delta


def _load_baseline(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--theme", default=DEFAULT_THEME, help=f"theme project to build (default: {DEFAULT_THEME})")
    ap.add_argument("--runs", type=int, default=3, help="builds to time; the best is used (default: 3)")
    ap.add_argument(
        "--threshold",
        type=float,
        default=float(os.environ.get("EPRESSO_PERF_THRESHOLD", DEFAULT_THRESHOLD)),
        help="fractional slowdown allowed before failing (default: 0.25, or $EPRESSO_PERF_THRESHOLD)",
    )
    ap.add_argument("--baseline", type=Path, default=BASELINE, help="baseline JSON to compare against")
    ap.add_argument("--update", action="store_true", help="re-record the baseline instead of comparing")
    ap.add_argument("--force", action="store_true", help="gate even when the baseline was recorded on another python")
    ap.add_argument("--json", type=Path, help="also write the measurements as JSON here")
    args = ap.parse_args()

    ref = _reference_seconds()
    best, median = build_seconds(args.theme, args.runs)
    ratio = best / ref
    measured = {
        "theme": args.theme,
        "python": f"{sys.version_info.major}.{sys.version_info.minor}",
        "reference_seconds": round(ref, 6),
        "build_seconds": round(best, 4),
        "build_median_seconds": round(median, 4),
        "ratio": round(ratio, 4),
    }

    print("── perf ──")
    print(f"  reference      {ref * 1000:9.1f} ms")
    print(f"  build (best)   {best:9.3f} s")
    print(f"  build (median) {median:9.3f} s")
    print(f"  ratio          {ratio:9.3f}")

    if args.update:
        measured["created"] = time.strftime("%Y-%m-%d")
        args.baseline.parent.mkdir(parents=True, exist_ok=True)
        args.baseline.write_text(json.dumps(measured, indent=2) + "\n", encoding="utf-8")
        print(f"  baseline updated → {args.baseline}")
        _write_json(args.json, measured)
        return 0

    baseline = _load_baseline(args.baseline)
    if not baseline.get("ratio"):
        print(f"\n  no baseline at {args.baseline} — run with --update to record one")
        _write_json(args.json, measured)
        return 0

    # A different interpreter means a different constant factor, not a regression.
    if baseline.get("python") != measured["python"] and not args.force:
        was_py, now_py = baseline.get("python"), measured["python"]
        print(f"\n  baseline recorded on python {was_py}, running {now_py} — not comparable")
        print("  re-record under this interpreter: python scripts/bench.py --update  (or pass --force)")
        _write_json(args.json, measured)
        return 0
    ok, delta = compare(ratio, baseline["ratio"], args.threshold)
    was = f"{baseline.get('created', '?')}, python {baseline.get('python', '?')}"
    print(f"  baseline       {baseline['ratio']:9.3f}  ({was})")
    print(f"  delta          {delta * 100:+8.1f}%  (threshold {args.threshold * 100:.0f}%)")
    print(f"  {'✅ within threshold' if ok else '❌ REGRESSION'}")
    if not ok:
        print("\n  The build got measurably slower. Look at what changed with:")
        print(f"    python -m epresso build {args.theme} --profile")
        print(f"    py-spy record -o perf.svg -- python -m epresso build {args.theme}")
        print("  If the slowdown is intended, re-record: python scripts/bench.py --update")
    elif delta < -args.threshold:
        print(f"\n  Baseline is stale — {abs(delta) * 100:.0f}% faster than recorded.")
        print("  Re-record: python scripts/bench.py --update")

    measured["baseline_ratio"] = baseline["ratio"]
    measured["delta"] = round(delta, 4)
    measured["ok"] = ok
    measured["gated"] = True
    _write_json(args.json, measured)
    return 0 if ok else 1


def _write_json(path: Path | None, payload: dict) -> None:
    if path is None:
        return
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    raise SystemExit(main())
