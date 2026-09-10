"""
Generate investment memo from extracted KPIs.
Writes Markdown to memos/<TICKER>_memo.md.
"""
import json
from pathlib import Path

INPUT_PATH = "data/kpis.json"

POSITIVE_QUARTERS = 0
NEGATIVE_QUARTERS = 0


def render(rows):
    global POSITIVE_QUARTERS, NEGATIVE_QUARTERS
    POSITIVE_QUARTERS = sum(1 for r in rows if r.get("sentiment") == "Positive")
    NEGATIVE_QUARTERS = sum(1 for r in rows if r.get("sentiment") == "Negative")

    md = [f"# {rows[0]['ticker']} Ltd - Earnings Memo (synthetic)", ""]
    md.append("| Quarter | Sentiment | KPIs | Source |")
    md.append("|---|---|---|---|")
    for r in rows:
        kpis = ", ".join(f"{k}={v}" for k, v in r.get("kpis", {}).items()) or "-"
        md.append(f"| {r['quarter']} | {r.get('sentiment','-')} | {kpis} | {r.get('source','-')} |")
    md.append("")

    for r in rows:
        md.append(f"### {r['quarter']} - {r.get('sentiment','-')}")
        md.append(f"> {r['text']}")
        md.append("")

    if POSITIVE_QUARTERS > NEGATIVE_QUARTERS:
        view = "BUY"
    elif NEGATIVE_QUARTERS > POSITIVE_QUARTERS:
        view = "SELL"
    else:
        view = "HOLD"
    md.append(f"**View: {view}** ({POSITIVE_QUARTERS} positive vs {NEGATIVE_QUARTERS} negative quarters)")
    return "\n".join(md), view


def generate(in_path=INPUT_PATH, out_path=None):
    rows = json.loads(Path(in_path).read_text(encoding="utf-8"))
    out_path = out_path or f"memos/{rows[0]['ticker']}_memo.md"
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    body, view = render(rows)
    Path(out_path).write_text(body, encoding="utf-8")
    print(f"  wrote memo to {out_path}  (view: {view})")
    return out_path


if __name__ == "__main__":
    generate()