"""
Extract KPIs and sentiment from transcripts.
Uses an LLM (OpenAI-compatible API) if OPENAI_API_KEY is set, else a regex + lexicon fallback.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

INPUT_PATH = "data/transcripts.json"
OUTPUT_PATH = "data/kpis.json"

POS_WORDS = {"grew", "expanded", "stable", "up", "growth", "upside", "improved", "strong", "maintained"}
NEG_WORDS = {"pressure", "rose", "flagged", "decline", "miss", "weak", "down"}


def llm_extract(transcript_text):
    """Call OpenAI-compatible chat completions. Returns None on any failure."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        body = {
            "model": "gpt-4o-mini",
            "messages": [
                {"role": "system", "content": "You extract KPIs and sentiment from earnings-call transcripts. Respond as JSON: {kpis: {revenue, nim, gnpa, ...}, sentiment: Positive|Neutral|Negative, rationale: short}"},
                {"role": "user", "content": transcript_text[:3000]},
            ],
            "response_format": {"type": "json_object"},
        }
        req = urllib.request.Request(
            "https://api.openai.com/v1/chat/completions",
            data=json.dumps(body).encode("utf-8"),
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
        )
        with urllib.request.urlopen(req, timeout=20) as r:
            data = json.loads(r.read().decode("utf-8"))
        content = data["choices"][0]["message"]["content"]
        return json.loads(content)
    except Exception:
        return None


def regex_extract(transcript_text):
    kpis = {}
    m = re.search(r"Revenue.*?([\d,]+\s*Cr)", transcript_text)
    if m:
        kpis["revenue"] = m.group(1)
    m = re.search(r"NIM.*?(\d+\s*bps)", transcript_text)
    if m:
        kpis["nim"] = m.group(1)
    m = re.search(r"GNPA\s*([\d.]+%)", transcript_text)
    if m:
        kpis["gnpa"] = m.group(1)
    m = re.search(r"Loan book.*?\+(\d+%)", transcript_text)
    if m:
        kpis["loan_growth"] = m.group(1)
    pos = sum(1 for w in re.findall(r"\w+", transcript_text.lower()) if w in POS_WORDS)
    neg = sum(1 for w in re.findall(r"\w+", transcript_text.lower()) if w in NEG_WORDS)
    sentiment = "Positive" if pos > neg else "Negative" if neg > pos else "Neutral"
    return {"kpis": kpis, "sentiment": sentiment, "pos": pos, "neg": neg, "source": "regex"}


def extract_one(transcript):
    out = llm_extract(transcript["text"])
    if out is None:
        out = regex_extract(transcript["text"])
    else:
        out["source"] = "llm"
    return {"ticker": transcript["ticker"], "quarter": transcript["quarter"], "text": transcript["text"], **out}


def run(in_path=INPUT_PATH, out_path=OUTPUT_PATH):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(Path(in_path).read_text(encoding="utf-8"))
    out = [extract_one(t) for t in data]
    Path(out_path).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"  extracted {len(out)} records -> {out_path}")
    return out


if __name__ == "__main__":
    if not Path(INPUT_PATH).exists():
        from pull_transcripts import pull
        pull()
    run()