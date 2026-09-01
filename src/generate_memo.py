"""
Generate investment memo from KPIs (synthetic).
"""
import json
from pathlib import Path

def generate(kpis_path="data/kpis.json", out_path="memos/FINBANK_memo.md"):
    data=json.loads(Path(kpis_path).read_text(encoding="utf-8"))
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    md=["# FinBank Ltd — Earnings Memo (synthetic)", ""]
    for r in data:
        md.append(f"## {r['quarter']} — Sentiment: {r['sentiment']}")
        md.append(f"- KPIs: {r['kpis']}")
        md.append(f"- Pos/Neg hits: {r['pos']}/{r['neg']}")
        md.append(f"> {r['text']}")
        md.append("")
    md.append("**View:** Hold — revenue momentum intact, NIM pressure in Q2 warrants watch. (Illustrative)")
    Path(out_path).write_text("\n".join(md), encoding="utf-8")
    print(f"wrote memo to {out_path}")

if __name__=="__main__":
    generate()
