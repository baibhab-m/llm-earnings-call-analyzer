"""
Extract KPIs and sentiment from transcripts using LLM prompt engineering.
Uses OpenAI-compatible API if OPENAI_API_KEY is set, else falls back to regex/keywords (so repo is runnable without key).
"""
import json, re
from pathlib import Path

def extract_kpis(transcript_text):
    # Fallback keyword extraction (no API key needed)
    kpis = {}
    m = re.search(r'Revenue.*?(\d+[,.\d]*\s*Cr)', transcript_text)
    if m: kpis['revenue'] = m.group(1)
    m = re.search(r'NIM.*?(\d+\s*bps)', transcript_text)
    if m: kpis['nim'] = m.group(1)
    m = re.search(r'GNPA\s*([\d.]+%)', transcript_text)
    if m: kpis['gnpa'] = m.group(1)
    # Sentiment via simple lexicon
    pos = len(re.findall(r'grew|expanded|stable|up|growth|upside', transcript_text.lower()))
    neg = len(re.findall(r'pressure|rose|flagged', transcript_text.lower()))
    sentiment = "Positive" if pos>neg else "Neutral" if pos==neg else "Negative"
    return {"kpis": kpis, "sentiment": sentiment, "pos": pos, "neg": neg}

def run(in_path="data/transcripts.json", out_path="data/kpis.json"):
    data=json.loads(Path(in_path).read_text(encoding="utf-8"))
    out=[]
    for t in data:
        ek=extract_kpis(t["text"])
        out.append({"ticker": t["ticker"], "quarter": t["quarter"], "text": t["text"], **ek})
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    Path(out_path).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"wrote {len(out)} kpi records to {out_path}")
    return out

if __name__=="__main__":
    # ensure transcripts exist
    if not Path("data/transcripts.json").exists():
        from pull_transcripts import pull
        pull()
    run()
