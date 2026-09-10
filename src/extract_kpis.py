"""
Extract 8 fields + score 8 signals from transcripts.
Uses an LLM (OpenAI-compatible API) with a fixed smart prompt if OPENAI_API_KEY
is set, else regex rules that produce the same 8 fields.
"""
import json
import os
import re
import urllib.request
from pathlib import Path

INPUT_PATH = "data/transcripts.json"
OUTPUT_PATH = "data/kpis.json"

# The fixed smart prompt - identical in index.html (shown in the web app).
PROMPT_TEMPLATE = """You are an equity analyst. Read the earnings excerpt below for {company} ({quarter}).
Return ONLY valid JSON with exactly these fields:
{{"revenue": "e.g. Rs 19,060 crore or null", "revenue_growth_yoy_pct": number or null,
"profit": "e.g. Rs 7,769 crore or null", "profit_growth_yoy_pct": number or null,
"profit_vs_estimate": "beat" | "miss" | "na", "margin_direction": "expand" | "compress" | "flat",
"guidance": "raised" | "cut" | "maintained" | "na", "operating": "strong" | "weak" | "mixed",
"tone": "optimistic" | "cautious", "one_off_note": string or null,
"red_flags": ["short strings"]}}
Use null / na for anything not stated. No commentary outside the JSON.
Excerpt: {text}"""


def _clean_json(text):
    """Strip thinking blocks / fences, return parsed object."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.S).strip()
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.S)
    if m:
        text = m.group(1)
    else:
        s, e = text.find("{"), text.rfind("}")
        if s != -1 and e != -1:
            text = text[s:e + 1]
    return json.loads(text)


def _normalize_llm(obj):
    """Force the 8 prompt fields + red_flags; fill safe defaults for missing."""
    f = {"revenue": None, "revenue_growth_yoy_pct": None, "profit": None,
         "profit_growth_yoy_pct": None, "profit_vs_estimate": "na",
         "margin_direction": "flat", "guidance": "na", "operating": "mixed",
         "tone": "cautious", "one_off_note": None, "red_flags": []}
    if not isinstance(obj, dict):
        return None
    for k in f:
        if k in obj and obj[k] not in ("",):
            f[k] = obj[k]
    if f["profit_vs_estimate"] not in ("beat", "miss", "na"):
        f["profit_vs_estimate"] = "na"
    if f["margin_direction"] not in ("expand", "compress", "flat"):
        f["margin_direction"] = "flat"
    if f["guidance"] not in ("raised", "cut", "maintained", "na"):
        f["guidance"] = "na"
    if f["operating"] not in ("strong", "weak", "mixed"):
        f["operating"] = "mixed"
    if f["tone"] not in ("optimistic", "cautious"):
        f["tone"] = "cautious"
    if not isinstance(f["red_flags"], list):
        f["red_flags"] = []
    f["source"] = "llm"
    return f


def _post_json(url, key, payload):
    req = urllib.request.Request(url, data=json.dumps(payload).encode("utf-8"),
                                 headers={"Authorization": f"Bearer {key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        data = json.loads(r.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"]


def llm_extract(pack):
    """Try OpenRouter, then MiniMax, then OpenAI. Returns fields dict or None."""
    prompt = PROMPT_TEMPLATE.format(company=pack.get("company", pack["ticker"]),
                                       quarter=pack.get("quarter", "?"), text=pack["text"][:6000])
    providers = []
    if os.environ.get("OPENROUTER_API_KEY"):
        providers.append(("openrouter", "https://openrouter.ai/api/v1/chat/completions",
                          os.environ["OPENROUTER_API_KEY"],
                          os.environ.get("OPENROUTER_MODEL", "meta-llama/llama-3.3-70b-instruct:free")))
    if os.environ.get("MINIMAX_API_KEY"):
        providers.append(("minimax",
                          os.environ.get("MINIMAX_BASE_URL", "https://api.minimax.io/v1").rstrip("/") + "/chat/completions",
                          os.environ["MINIMAX_API_KEY"],
                          os.environ.get("MINIMAX_MODEL", "MiniMax-M2.1")))
    if os.environ.get("OPENAI_API_KEY"):
        providers.append(("openai", "https://api.openai.com/v1/chat/completions",
                          os.environ["OPENAI_API_KEY"], "gpt-4o-mini"))
    for name, url, key, model in providers:
        try:
            raw = _post_json(url, key, {"model": model,
                                        "messages": [{"role": "user", "content": prompt}],
                                        "temperature": 0, "max_tokens": 4000})
            f = _normalize_llm(_clean_json(raw))
            if f:
                f["llm_provider"] = name
                return f
        except Exception as e:
            print(f"  llm via {name} failed ({e}), trying next…")
    return None


def regex_extract(text):
    f = {"revenue": None, "revenue_growth_yoy_pct": None, "profit": None,
         "profit_growth_yoy_pct": None, "profit_vs_estimate": "na",
         "margin_direction": "flat", "guidance": "na", "operating": "mixed",
         "tone": "cautious", "one_off_note": None, "red_flags": []}
    m = re.search(r"(?:revenue|net interest income)[^.]*?([\d,.]+\s*(?:lakh crore|crore|cr))", text, re.I)
    if m:
        f["revenue"] = "Rs " + m.group(1)
    m = re.search(r"(?:revenue|net interest income).{0,80}?(up|down|grew|fell).{0,40}?([\d.]+)%", text, re.I)
    if m:
        f["revenue_growth_yoy_pct"] = (1 if m.group(1).lower() in ("up", "grew") else -1) * float(m.group(2))
    m = re.search(r"(?:net profit|profit after tax)[^.]*?Rs ([\d,.]+\s*(?:lakh crore|crore|cr))", text, re.I)
    if m:
        f["profit"] = "Rs " + m.group(1)
    m = re.search(r"(?:net profit|profit after tax)[^.]*?(up|down)[^.]*?([\d.]+)%", text, re.I)
    if m:
        f["profit_growth_yoy_pct"] = (1 if m.group(1).lower() == "up" else -1) * float(m.group(2))
    if re.search(r"beat[^.]*?estimate", text, re.I):
        f["profit_vs_estimate"] = "beat"
    elif re.search(r"below[^.]*?estimate|missed[^.]*?estimate", text, re.I):
        f["profit_vs_estimate"] = "miss"
    m = re.search(r"margin.{0,60}?(expanded|expand\w*|compress\w*|down from|up from)|NIM.{0,60}?(expanded|compressed)", text, re.I)
    if m:
        w = (m.group(1) or m.group(2)).lower()
        f["margin_direction"] = "expand" if re.search(r"expand|up from", w) else "compress"
    m = re.search(r"guidance.{0,40}?(cut|trimmed|lowered|raised|increased|maintained|retained|unchanged)"
                  r"|(cut|trimmed|lowered|raised|increased|maintained|retained)[^.]{0,60}?guidance", text, re.I)
    if m:
        w = (m.group(1) or m.group(2)).lower()
        f["guidance"] = "cut" if re.match(r"cut|trimmed|lowered", w) else ("raised" if re.match(r"raised|increased", w) else "maintained")
    if re.search(r"strong|record|improved|gain|added [\d.]+ million", text, re.I):
        f["operating"] = "strong"
    elif re.search(r"deteriorated|weak demand|slowed", text, re.I):
        f["operating"] = "weak"
    if re.search(r"optimistic|confident", text, re.I):
        f["tone"] = "optimistic"
    m = re.search(r"(one-time|one-off)[^.]{0,80}?(Rs [\d,.]+\s*crore|[\d.]+ basis point)", text, re.I)
    if m:
        f["one_off_note"] = f"One-off mentioned ({m.group(0).strip()}) — YoY comparison may be distorted."
    m = re.search(r"(?:shares|ADR|stock) (fell|rose|gained|slipped|dropped)[^.]*?([\d.]+)%", text, re.I)
    if m:
        f["market_move_pct"] = (-1 if m.group(1).lower() in ("fell", "slipped", "dropped") else 1) * float(m.group(2))
    if f["profit_vs_estimate"] == "miss":
        f["red_flags"].append("Missed street estimates.")
    if f["guidance"] == "cut":
        f["red_flags"].append("Guidance cut.")
    if f["margin_direction"] == "compress":
        f["red_flags"].append("Margin compression.")
    f["source"] = "regex"
    return f


def score(fields, pack):
    """8 signals, +1/0/-1 each. >= +2 BUY, <= -2 SELL, else HOLD."""
    s = []
    s.append(("Profit vs street estimate", fields["profit_vs_estimate"],
              1 if fields["profit_vs_estimate"] == "beat" else (-1 if fields["profit_vs_estimate"] == "miss" else 0)))
    rg = fields["revenue_growth_yoy_pct"]
    s.append((f"Revenue growth YoY ({rg if rg is not None else 'n/a'}%)",
              "positive" if (rg or 0) > 0 else ("not stated" if rg is None else "negative"),
              0 if rg is None else (1 if rg > 0 else -1)))
    pg = fields["profit_growth_yoy_pct"]
    s.append((f"Profit growth YoY ({pg if pg is not None else 'n/a'}%)",
              "positive" if (pg or 0) > 0 else ("not stated" if pg is None else "negative"),
              0 if pg is None else (1 if pg > 0 else -1)))
    s.append(("Margin direction", fields["margin_direction"],
              1 if fields["margin_direction"] == "expand" else (-1 if fields["margin_direction"] == "compress" else 0)))
    s.append(("Guidance", fields["guidance"],
              1 if fields["guidance"] == "raised" else (-1 if fields["guidance"] == "cut" else 0)))
    s.append(("Operating (asset quality / deals / subs)", fields["operating"],
              1 if fields["operating"] == "strong" else (-1 if fields["operating"] == "weak" else 0)))
    s.append(("Management tone", fields["tone"], 1 if fields["tone"] == "optimistic" else -1))
    mr = fields.get("market_move_pct", pack.get("market_reaction_pct"))
    s.append((f"Market reaction ({mr if mr is not None else 'n/a'}%)",
              "no data" if mr is None else ("up" if mr > 1 else ("down" if mr < -1 else "flat")),
              0 if mr is None else (1 if mr > 1 else (-1 if mr < -1 else 0))))
    total = sum(p for _, _, p in s)
    view = "BUY" if total >= 2 else ("SELL" if total <= -2 else "HOLD")
    return [{"name": n, "reading": r, "pts": p} for n, r, p in s], total, view


def run(in_path=INPUT_PATH, out_path=OUTPUT_PATH):
    Path(out_path).parent.mkdir(parents=True, exist_ok=True)
    data = json.loads(Path(in_path).read_text(encoding="utf-8"))
    out = []
    for t in data:
        f = llm_extract(t) or regex_extract(t["text"])
        if "source" not in f:
            f["source"] = "llm"
        signals, total, view = score(f, t)
        out.append({"ticker": t["ticker"], "quarter": t.get("quarter", "?"), "text": t["text"],
                    "fields": f, "signals": signals, "total": total, "view": view})
    Path(out_path).write_text(json.dumps(out, indent=2), encoding="utf-8")
    print(f"  extracted + scored {len(out)} records -> {out_path}")
    return out


if __name__ == "__main__":
    if not Path(INPUT_PATH).exists():
        from pull_transcripts import pull
        pull()
    for r in run():
        print(f"  {r['ticker']} {r['quarter']}: score {r['total']:+d} -> {r['view']}")
