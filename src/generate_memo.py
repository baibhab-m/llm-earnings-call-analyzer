"""
Generate investment memo from scored fields.
Writes Markdown to memos/<TICKER>_memo.md, one file per company.
"""
import json
from pathlib import Path

INPUT_PATH = "data/kpis.json"


def render(rec):
    t = rec["ticker"]
    lines = [f"# {t} - Earnings Memo ({rec['quarter']})", ""]
    f = rec["fields"]
    lines.append("| Field | Value |")
    lines.append("|---|---|")
    for k in ["revenue", "revenue_growth_yoy_pct", "profit", "profit_growth_yoy_pct",
              "profit_vs_estimate", "margin_direction", "guidance", "operating",
              "tone", "one_off_note", "red_flags"]:
        lines.append(f"| {k} | {f.get(k, '—')} |")
    lines.append("")
    lines.append("| # | Signal | Reading | Points |")
    lines.append("|---|---|---|---|")
    for i, s in enumerate(rec["signals"], 1):
        lines.append(f"| {i} | {s['name']} | {s['reading']} | {s['pts']:+d} |")
    lines.append("")
    pos = [s["name"] for s in rec["signals"] if s["pts"] > 0]
    neg = [s["name"] for s in rec["signals"] if s["pts"] < 0]
    why = f"Driven by {pos[0].lower() if pos else 'no clear positive'}" + \
          (f", weighed down by {neg[0].lower()}." if neg else " with no clear negative.")
    if f.get("one_off_note"):
        why += " Note: " + f["one_off_note"]
    lines.append(f"**View: {rec['view']}** (score {rec['total']:+d} across 8 signals)")
    lines.append("")
    lines.append(why)
    if f.get("red_flags"):
        lines.append("")
        lines.append("Red flags: " + " ".join(f["red_flags"]))
    lines.append("")
    lines.append(f"> {rec['text']}")
    return "\n".join(lines)


def generate(in_path=INPUT_PATH, out_dir="memos"):
    rows = json.loads(Path(in_path).read_text(encoding="utf-8"))
    Path(out_dir).mkdir(parents=True, exist_ok=True)
    for rec in rows:
        path = Path(out_dir) / f"{rec['ticker']}_memo.md"
        path.write_text(render(rec), encoding="utf-8")
        print(f"  wrote memo to {path}  (view: {rec['view']})")


if __name__ == "__main__":
    generate()
