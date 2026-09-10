"""
LLM Earnings-Call Analyzer
Pipeline: pull transcripts via API -> extract KPIs + sentiment -> generate Markdown memo.
Uses OpenAI-compatible API if OPENAI_API_KEY is set, otherwise regex/lexicon fallback.
"""
from src.pull_transcripts import pull
from src.extract_kpis import run as extract
from src.generate_memo import generate as memo

TICKER = "FINBANK"


def main():
    print("=" * 60)
    print(f"Earnings-Call Analyzer - {TICKER}")
    print("=" * 60)
    print("\n[1/3] Pulling transcripts...")
    pull(ticker=TICKER)
    print("\n[2/3] Extracting KPIs and sentiment...")
    extract()
    print("\n[3/3] Generating memo...")
    memo()
    print("\nDone.")


if __name__ == "__main__":
    main()