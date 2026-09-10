# LLM Earnings-Call Analyzer

Python/LLM pipeline that takes a company, pulls its latest earnings call, extracts fields with a fixed smart prompt, scores 8 signals, and generates an investment memo with a view.

## Architecture (5 stages, same in Python and the web app)
1. **Input** - company + quarter. A bundled verified pack or your own pasted transcript.
2. **Fetch** - tries a live transcripts API (Finnhub) if a key is set, else the bundled pack.
3. **Extract** - one fixed prompt asks an LLM for strict JSON with 8 fields (shown in `index.html` and `PROMPT_TEMPLATE` in `src/extract_kpis.py`). With no key, regex rules produce the same 8 fields.
4. **Score** - 8 signals, each +1 / 0 / −1. Total ≥ +2 → BUY, ≤ −2 → SELL, else HOLD.
5. **Memo** - fields table + signal breakdown + one-line reason + view.

## Real data
`data/companies.json` ships verbatim excerpts from the official Q1 FY27 sources
(HDFC Bank earnings-call transcript PDF, Reliance media release + webcast, Infosys
earnings-call transcript + press release - source URLs in each pack) with real
reported numbers, street estimates where published, and post-results price reaction.
Regex path gives HDFC HOLD (−1), Reliance BUY (+2), Infosys HOLD (+1);
live-LLM readings can differ by a point where the model judges operating/tone
differently, and the memo always shows which path produced the fields.

## Run
```bash
pip install -r requirements.txt
python main.py
```

To enable the real LLM path (OpenRouter free models, MiniMax, or OpenAI):
```bash
set OPENROUTER_API_KEY=your_key_here
set MINIMAX_API_KEY=your_key_here
set OPENAI_API_KEY=your_key_here
python main.py
```

Without keys, the pipeline runs on the bundled packs and regex extraction.
In the web app, paste a key into the LLM box (provider + model selectable) -
it stays in the page memory only and is never stored or committed.

## Outputs
- `data/transcripts.json` - raw transcripts (per run)
- `data/kpis.json` - extracted fields + signal scores (per run)
- `memos/<TICKER>_memo.md` - investment memo per company
- `index.html` - same analyzer as a single page in the browser, just open it

## Files
- `main.py` - runs all companies end to end
- `src/pull_transcripts.py` - fetch layer (API or packs)
- `src/extract_kpis.py` - smart prompt + regex fallback + scoring
- `src/generate_memo.py` - memo renderer
- `data/companies.json` - the 3 verified company packs
