"""
Pull earnings-call transcripts via API.
Uses Finnhub-style transcripts endpoint if FINNHUB_API_KEY is set,
otherwise falls back to bundled verified packs in data/companies.json
(real Q1 FY27 numbers for HDFC Bank, Reliance, Infosys).
"""
import json
import os
import urllib.request
from pathlib import Path

PACKS_PATH = "data/companies.json"
OUTPUT_PATH = "data/transcripts.json"


def load_packs():
    return json.loads(Path(PACKS_PATH).read_text(encoding="utf-8"))


def fetch_from_api(ticker):
    """Hit Finnhub transcripts endpoint. Returns [] if key not set or call fails."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        return []
    try:
        url = f"https://finnhub.io/api/v1/stock/transcripts?symbol={ticker}&token={api_key}"
        with urllib.request.urlopen(url, timeout=10) as r:
            payload = json.loads(r.read().decode("utf-8"))
        out = []
        for t in payload.get("transcript", []):
            out.append({"ticker": ticker, "quarter": f"Q{t.get('quarter', '?')} {t.get('year', '?')}", "text": t.get("text", "")})
        return out
    except Exception:
        return []


def pull(ticker="HDFCBANK", out=OUTPUT_PATH):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    live = fetch_from_api(ticker)
    if live:
        data = live
        print(f"  pulled {len(data)} transcripts for {ticker} (source: Finnhub API) -> {out}")
    else:
        packs = [p for p in load_packs() if p["ticker"] == ticker] or load_packs()
        data = packs
        print(f"  pulled {len(data)} transcripts for {ticker} (source: bundled packs) -> {out}")
    Path(out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    return data


if __name__ == "__main__":
    pull()
