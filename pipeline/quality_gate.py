"""Quality gate for the monitor workflow.

- Prints a per-source status table to $GITHUB_STEP_SUMMARY.
- Emits ::error annotations so partial failures are unmistakable in the UI.
- Exit codes: 0 = all sources healthy; 1 = partial or total failure.
Distinguishes: total failure (no report / zero results) vs partial (some failed)
vs publication-guard blocks (expected, notice-level).
"""
import json
import os
import sys

REPORT = os.path.join("data", "run_report.json")


lines = []


def main():
    global lines
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    lines = []

    def emit(s=""):
        lines.append(s)

    try:
        with open(REPORT) as f:
            report = json.load(f)
    except Exception as e:
        emit(f"::error::COMPLETE MONITOR FAILURE: no run report produced ({e})")
        emit("## ❌ COMPLETE MONITOR FAILURE")
        emit("Pipeline crashed before producing a report. No data was published.")
        _flush(summary)
        return 1

    results = report.get("results", [])
    if not results:
        emit("::error::COMPLETE MONITOR FAILURE: zero results in report")
        emit("## ❌ COMPLETE MONITOR FAILURE — zero sources ran")
        _flush(summary)
        return 1

    failed = [r for r in results if not r.get("ok")]
    blocked = [r for r in results if r.get("blocked")]
    ok = [r for r in results if r.get("ok")]

    emit(f"## Monitor cycle {report.get('run_at', '')}")
    emit("")
    emit("| status | source | detail |")
    emit("|---|---|---|")
    for r in results:
        if r.get("ok"):
            mark = "✅"
        elif r.get("blocked"):
            mark = "🚫"
        else:
            mark = "❌"
        if r.get("blocked"):
            detail = "blocked by publication guard (test/non-official source)"
        elif r.get("error"):
            detail = str(r["error"])
        else:
            detail = f"{r.get('changes', 0)} change(s), {r.get('announcements', 0)} announcement(s)"
        emit(f"| {mark} | {r['id']} | {detail[:140].replace('|', '/')} |")
    emit("")
    emit(f"**{len(ok)}/{len(results)} sources healthy.**")
    emit(f"Site: https://dekopon1.github.io/modelsignal/ · Health page: /status/")

    for r in blocked:
        emit(f"::notice::publication guard blocked source {r['id']}")

    if len(failed) == len(results):
        emit("::error::COMPLETE MONITOR FAILURE: every source failed")
        emit("## ❌ TOTAL OUTAGE — every source failed. Treat as an incident.")
        _flush(summary)
        return 1
    if failed:
        names = ", ".join(r["id"] for r in failed)
        emit(f"::error::PARTIAL SOURCE FAILURE ({len(failed)}/{len(results)}): {names}")
        emit(f"## ⚠️ DEGRADED RUN — {len(failed)}/{len(results)} sources failed: {names}")
        emit("Good sources were still published. Fix failing sources before next cycle.")
        _flush(summary)
        return 1

    emit("::notice::all sources healthy")
    _flush(summary)
    return 0


def _flush(path):
    text = "\n".join(lines) + "\n"
    print(text)
    if path:
        with open(path, "a", encoding="utf-8") as f:
            f.write(text + "\n")


if __name__ == "__main__":
    sys.exit(main())
