"""
LLM Earnings-Call Analyzer
Pipeline: pull transcripts via API (or bundled real Q1 FY27 packs)
-> extract 8 fields + score 8 signals (LLM smart prompt, regex fallback)
-> generate Markdown memo per company with BUY / HOLD / SELL view.
"""
import json
from pathlib import Path

from src.pull_transcripts import load_packs
from src.extract_kpis import run as extract
from src.generate_memo import generate as memo


def main():
    print("=" * 60)
    print("Earnings-Call Analyzer - real Q1 FY27 packs")
    print("=" * 60)
    for pack in load_packs():
        print(f"\n[{pack['ticker']}] {pack['company']} {pack['quarter']} (announced {pack['announced']})")
        print("[1/3] Pulling transcript...")
        from src.pull_transcripts import pull
        pull(ticker=pack["ticker"], out="data/transcripts.json")
        print("[2/3] Extracting fields + scoring...")
        rows = extract()
        print("[3/3] Generating memo...")
        memo()
        print(f"  => {rows[0]['view']} (score {rows[0]['total']:+d})")
    print("\nDone. Memos in memos/.")


if __name__ == "__main__":
    main()
