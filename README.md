# LLM Earnings-Call Analyzer

AI-Powered Credit Memo Automation — Python, LLMs, APIs

Built Python-LLM pipeline pulling earnings transcripts via APIs, extracting KPIs and sentiment to generate research memos.

## Pipeline
1. src/pull_transcripts.py — pulls (synthetic) transcripts via API, writes data/transcripts.json`n2. src/extract_kpis.py — prompt-engineered LLM extraction (falls back to regex if no API key), writes data/kpis.json`n3. src/generate_memo.py — generates memos/FINBANK_memo.md`n
## Run
``npython src/pull_transcripts.py
python src/extract_kpis.py
python src/generate_memo.py
``n
## Notes
Synthetic transcripts for FinBank Ltd — replace SAMPLE_TRANSCRIPTS with real API. Illustrative sentiment/memo.

