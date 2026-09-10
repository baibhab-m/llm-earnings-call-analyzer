# LLM Earnings-Call Analyzer

Python/LLM pipeline that pulls earnings-call transcripts via API (Finnhub), extracts KPIs and sentiment, and generates an investment memo.

## Pipeline
1. **pull** - fetch transcripts via Finnhub API (or fall back to synthetic samples)
2. **extract** - LLM (OpenAI-compatible) extracts KPIs + sentiment, with regex/lexicon fallback when no API key
3. **memo** - render Markdown memo with view (BUY / HOLD / SELL)

## Run
```bash
pip install -r requirements.txt
python main.py
```

To enable live API:
```bash
set FINNHUB_API_KEY=your_key_here
set OPENAI_API_KEY=your_key_here
python main.py
```

Without keys, the pipeline runs on synthetic samples and regex extraction.

## Outputs
- `data/transcripts.json` - raw transcripts
- `data/kpis.json` - extracted KPIs + sentiment per quarter
- `memos/FINBANK_memo.md` - investment memo
- `index.html` - same analyzer as a single page in the browser, just open it

## Note
Synthetic samples ship with the repo so it runs end-to-end without API keys.