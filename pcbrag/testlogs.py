"""
Parser for the functional test logs. Format:

    serial: CB-24-00117
    [08:12:05] STEP 01 power_on_current   312.4 mA  lim 250.0..400.0   PASS
    [08:12:30] STEP 07 uart_loopback          -                         FAIL (timeout ...)
    result: FAIL

RAG is bad at counting ("how many boards failed X?") so there's also a
stats() function that does it properly with pandas, and the assistant
adds that table to the context for those kinds of questions.
"""
import re
from pathlib import Path

import pandas as pd

HEADER = re.compile(r"^(\w+):\s*(.+)$")
STEP = re.compile(
    r"^\[(?P<time>[\d:]+)\]\s+STEP\s+(?P<num>\d+)\s+(?P<name>\S+)\s+"
    r"(?:(?P<value>-?[\d.]+)\s+(?P<unit>\S+)\s+lim\s+(?P<lo>-?[\d.]+)\.\.(?P<hi>-?[\d.]+)|-)\s+"
    r"(?P<status>PASS|FAIL)\s*(?P<note>.*)$")


def parse(text, filename=""):
    rec = {"file": filename, "steps": []}
    for line in text.splitlines():
        line = line.strip()
        m = STEP.match(line)
        if m:
            d = m.groupdict()
            for k in ("value", "lo", "hi"):
                d[k] = float(d[k]) if d[k] is not None else None
            d["note"] = d["note"].strip("() ")
            rec["steps"].append(d)
            continue
        m = HEADER.match(line)
        if m and m.group(1) in ("station", "board", "serial", "pcb_lot", "operator", "start", "end", "result"):
            rec[m.group(1)] = m.group(2).strip()
    return rec


def parse_dir(log_dir):
    return [parse(p.read_text(errors="ignore"), p.name) for p in sorted(Path(log_dir).glob("*.log"))]


def summarize(rec):
    """turns a log into a short text that embeds / searches well"""
    fails = [s for s in rec["steps"] if s["status"] == "FAIL"]
    lines = [
        f"Test log for board {rec.get('serial')} ({rec.get('board')}), PCB lot {rec.get('pcb_lot')}.",
        f"Tested on station {rec.get('station')} by {rec.get('operator')} at {rec.get('start')}.",
        f"Overall result: {rec.get('result')}.",
    ]
    if fails:
        lines.append("Failed steps: " + "; ".join(
            f"{s['name']}" + (f" measured {s['value']} {s['unit']} (limit {s['lo']}..{s['hi']})"
                              if s["value"] is not None else "")
            + (f" - {s['note']}" if s["note"] else "") for s in fails) + ".")
    else:
        lines.append("All steps passed.")
    meas = [f"{s['name']} = {s['value']} {s['unit']}" for s in rec["steps"] if s["value"] is not None]
    if meas:
        lines.append("Measurements: " + ", ".join(meas) + ".")
    return "\n".join(lines)


def to_frame(records):
    rows = []
    for r in records:
        for s in r["steps"]:
            rows.append({"serial": r.get("serial"), "board": r.get("board"), "lot": r.get("pcb_lot"),
                         "station": r.get("station"), "start": r.get("start"),
                         "result": r.get("result"), **{k: s[k] for k in
                         ("name", "value", "unit", "lo", "hi", "status", "note")}})
    return pd.DataFrame(rows)


def stats(records):
    """plain text summary of failures, used as extra context + by `pcbrag stats`"""
    df = to_frame(records)
    if df.empty:
        return "No test logs found."
    boards = df.drop_duplicates("serial")
    fails = df[df.status == "FAIL"]
    out = [f"Test log statistics: {len(boards)} boards tested, "
           f"{(boards.result == 'FAIL').sum()} failed, yield {(boards.result == 'PASS').mean():.1%}."]

    if not fails.empty:
        out.append("Failures per test step: " + ", ".join(
            f"{name}: {n}" for name, n in fails.name.value_counts().items()) + ".")
        for name, g in fails.groupby("name"):
            out.append(f"Boards failing {name}: " + ", ".join(
                f"{r.serial} ({r.board}, lot {r.lot}"
                + (f", {r.value} {r.unit}" if pd.notna(r.value) else "") + ")"
                for r in g.itertuples()) + ".")

    by_board = boards.groupby("board").result.apply(lambda s: f"{(s == 'PASS').mean():.0%} yield ({len(s)} boards)")
    out.append("Yield by board revision: " + ", ".join(f"{k}: {v}" for k, v in by_board.items()) + ".")

    num = df[df.value.notna()]
    by_lot = num.groupby(["name", "lot"]).value.mean().unstack()
    out.append("Average measurements by PCB lot: " + "; ".join(
        f"{name}: " + ", ".join(f"{lot} {v:.3g}" for lot, v in row.items())
        for name, row in by_lot.iterrows()) + ".")
    return "\n".join(out)
