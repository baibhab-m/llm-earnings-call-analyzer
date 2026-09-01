"""
Pull earnings transcripts via API (synthetic example).
In production, replace SAMPLE_TRANSCRIPTS with real API calls (e.g., Alpha Vantage, Finnhub).
"""
import json
from pathlib import Path

SAMPLE_TRANSCRIPTS = [
    {"ticker": "FINBANK", "quarter": "Q1 FY25", "text": "Revenue grew 14% YoY to INR 1,320 Cr. NIM expanded 15 bps. Management guides credit growth 12-14%. Asset quality stable, GNPA 2.1%. Digital lending pipeline up 30%."},
    {"ticker": "FINBANK", "quarter": "Q2 FY25", "text": "Revenue 1,480 Cr (+12% YoY). Fee income drove upside. Opex rose 9% on tech hires. Management flagged NIM pressure from rate cuts. Loan book +11%."},
]

def pull(ticker="FINBANK", out="data/transcripts.json"):
    Path(out).parent.mkdir(parents=True, exist_ok=True)
    # Synthetic: filter sample
    data = [t for t in SAMPLE_TRANSCRIPTS if t["ticker"]==ticker]
    Path(out).write_text(json.dumps(data, indent=2), encoding="utf-8")
    print(f"wrote {len(data)} transcripts to {out}")
    return data

if __name__=="__main__":
    pull()
