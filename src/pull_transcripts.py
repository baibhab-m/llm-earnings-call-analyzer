"""
Pull earnings-call transcripts via API.
Uses Finnhub-style /company_earnings_transcripts endpoint if FINNHUB_API_KEY is set,
otherwise falls back to bundled synthetic samples so the pipeline still runs.
"""
import json
import os
import urllib.request
from pathlib import Path

OUTPUT_PATH = "data/transcripts.json"

SYNTHETIC_TRANSCRIPTS = [
    {
        "ticker": "FINBANK",
        "quarter": "Q1 FY25",
        "text": "Revenue grew 14% YoY to INR 13,680 Cr. NIM expanded 15 bps. Management guides credit growth 12-14%. Asset quality stable, GNPA 2.1%. Digital lending pipeline up 30%.",
    },
    {
        "ticker": "FINBANK",
        "quarter": "Q2 FY25",
        "text": "Revenue INR 15,460 Cr (+13% YoY). Fee income drove upside. Opex rose 9% on tech hires. Management flagged NIM pressure from rate cuts. Loan book +11%.",
    },
    {
        "ticker": "FINBANK",
        "quarter": "Q3 FY25",
        "text": "Revenue INR 17,160 Cr (+11% YoY). Strong deposit growth at 14%. Asset quality improved, GNPA down to 1.9%. NIM stable. Guidance maintained.",
    },
]


def fetch_from_api(ticker):
    """Hit Finnhub transcripts endpoint. Returns [] if key not set or call fails."""
    api_key = os.environ.get("FINNHUB_API_KEY")
    if not api_key:
        return []
    try:
        # Finnhub transcripts endpoint shape: returns {transcript: [{quarter, year, text}]}
        url = f"https://finnhub.io/api/v1/stock/transcripts?symbol={ticker}&token={api_key}"
        with urllib.request.urlopen(url, timeout=10) as r:
            payload = json.loads(r.read().decode("utf-8"))
        out = []
        for t in payload.get("transcript", []):
            out.append({"ticker": ticker, "quarter": f"Q{t.get('quarter','?')} {t.get('year','?')}", "text": t.get("text", "")})
        return out
    except Exception:
        return []


def pull(ticker="FINBANK", out=OUTPUT_PATH):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    transcripts = fetch_from_api(ticker)
    source = "Finnhub API" if transcripts else "synthetic samples"
    if not transcripts:
        transcripts = [t for t in SYNTHETIC_TRANSCRIPTS if t["ticker"] == ticker]
    Path(out).write_text(json.dumps(transcripts, indent=2), encoding="utf-8")
    print(f"  pulled {len(transcripts)} transcripts for {ticker} (source: {source}) -> {out}")
    return transcripts


if __name__ == "__main__":
    pull()