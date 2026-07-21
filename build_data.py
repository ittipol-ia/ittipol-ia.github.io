#!/usr/bin/env python3
"""
Market Briefing — data builder.
Runs on GitHub Actions each morning, fetches live market data from Stooq
(free, no API key), and rewrites data.js. Designed to fail SOFTLY: any symbol
that can't be fetched shows "n/a" rather than breaking the page.
"""
import csv
import io
import json
import sys
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("Asia/Bangkok")
SESSION = requests.Session()
SESSION.headers.update({"User-Agent": "market-brief-bot/1.0"})


def fetch_last_two_closes(symbol):
    """Return (last_close, prev_close) from Stooq daily history, or (None, None)."""
    url = "https://stooq.com/q/d/l/"
    try:
        r = SESSION.get(url, params={"s": symbol, "i": "d"}, timeout=20)
        r.raise_for_status()
        text = r.text.strip()
        if not text or text.lower().startswith("<"):
            return None, None
        rows = list(csv.DictReader(io.StringIO(text)))
        closes = [float(row["Close"]) for row in rows if row.get("Close") not in (None, "", "N/D")]
        if len(closes) >= 2:
            return closes[-1], closes[-2]
        if len(closes) == 1:
            return closes[-1], None
    except Exception as e:
        print(f"  ! {symbol}: {e}", file=sys.stderr)
    return None, None


def fmt_level(v, kind):
    if v is None:
        return "—"
    if kind == "index":
        return f"{v:,.2f}"
    if kind == "pct":          # yields quoted as a percent level
        return f"{v:.2f}%"
    if kind == "fx":
        return f"{v:,.3f}" if v < 10 else f"{v:,.2f}"
    if kind == "usd":
        return f"${v:,.2f}"
    return f"{v:,.2f}"


def pct_change(last, prev):
    if last is None or prev in (None, 0):
        return None
    return (last - prev) / prev * 100.0


def dir_of(chg):
    if chg is None:
        return "flat"
    if chg > 0.05:
        return "up"
    if chg < -0.05:
        return "down"
    return "flat"


def chg_str(chg):
    if chg is None:
        return "n/a"
    return f"{chg:+.1f}%"


def build_row(name, symbol, kind="index"):
    last, prev = fetch_last_two_closes(symbol)
    chg = pct_change(last, prev)
    return {
        "name": name,
        "lvl": fmt_level(last, kind),
        "chg": chg_str(chg),
        "dir": dir_of(chg),
        "_chg": chg,           # kept for the narrative, stripped before output
    }


# ---- symbol map (Stooq tickers) -------------------------------------------
US = [
    ("S&P 500", "^spx", "index"),
    ("Nasdaq Composite", "^ndq", "index"),
    ("Dow Jones", "^dji", "index"),
    ("PHLX Semis (SOX)", "^sox", "index"),
]
ASIA = [
    ("Nikkei 225 (Tokyo)", "^nkx", "index"),
    ("Hang Seng", "^hsi", "index"),
    ("Shanghai Composite", "^shc", "index"),
    ("Kospi (Seoul)", "^kospi", "index"),
]
EUROPE = [
    ("FTSE 100", "^ukx", "index"),
    ("DAX", "^dax", "index"),
]
FX = [
    ("US 10-yr Treasury", "10usy.b", "pct"),
    ("US 2-yr Treasury", "2usy.b", "pct"),
    ("USD/THB", "usdthb", "fx"),
    ("USD/JPY", "usdjpy", "fx"),
    ("EUR/USD", "eurusd", "fx"),
]
COMMODITIES = [
    ("WTI Crude", "cl.f", "usd"),
    ("Gold", "xauusd", "usd"),
]


def strip(rows):
    """Remove private _chg keys before serialising."""
    out = []
    for r in rows:
        out.append({k: v for k, v in r.items() if not k.startswith("_")})
    return out


def phrase(chg):
    # Wording is deliberately number-neutral so it reads correctly after both
    # singular subjects ("the Nasdaq") and plural ones ("US equities").
    if chg is None:
        return "held steady"
    if chg > 0.75:
        return "rose sharply"
    if chg > 0.05:
        return "edged higher"
    if chg < -0.75:
        return "fell sharply"
    if chg < -0.05:
        return "edged lower"
    return "held steady"


def main():
    print("Fetching market data from Stooq…")
    us = [build_row(*x) for x in US]
    asia = [build_row(*x) for x in ASIA]
    europe = [build_row(*x) for x in EUROPE]
    fx = [build_row(*x) for x in FX]
    commodities = [build_row(*x) for x in COMMODITIES]

    now = datetime.now(TZ)
    date_str = now.strftime("%A, %B %-d, %Y")
    updated_str = now.strftime("%b %-d, %Y · 7:00 AM ICT")

    # --- lightweight auto-generated narrative ---
    spx = us[0]["_chg"]
    ndq = us[1]["_chg"]
    wti = commodities[0]["_chg"]
    gold = commodities[1]["_chg"]
    top = (
        f"US equities {phrase(spx)} in the latest session, "
        f"with the Nasdaq {phrase(ndq)}. "
        f"Crude {phrase(wti)} and gold {phrase(gold)}. "
        "See the sections below for the full board; your 7:00 AM briefing has the detailed analysis."
    )
    tech_note = (
        f"The Nasdaq {phrase(ndq)} and the PHLX Semiconductor index "
        f"{phrase(us[3]['_chg'])} — the clearest read on the day's AI/chip sentiment. "
        "Watch the US open for direction."
    )

    briefing = {
        "date": date_str,
        "asOf": "Live figures, latest available close",
        "updated": updated_str,
        "topStory": top,
        "sections": [
            {"icon": "🇺🇸", "title": "US Markets", "span": False, "rows": strip(us),
             "note": "Index levels and daily change from the most recent session."},
            {"icon": "🌏", "title": "Asia-Pacific", "span": False, "rows": strip(asia),
             "note": "Regional benchmarks; some markets may be closed for local holidays."},
            {"icon": "🇪🇺", "title": "Europe & Global", "span": False, "rows": strip(europe),
             "note": "Major European benchmarks."},
            {"icon": "💻", "title": "Tech / AI Theme", "span": False, "rows": [],
             "note": tech_note},
            {"icon": "💵", "title": "FX & Rates", "span": False, "rows": strip(fx),
             "note": "Treasury yields shown as levels; FX as spot rates."},
            {"icon": "🛢️", "title": "Commodities", "span": False, "rows": strip(commodities),
             "note": "WTI crude and spot gold."},
            {"icon": "📅", "title": "Macro Watch", "span": True, "rows": [],
             "note": "Watch central-bank commentary, scheduled inflation/jobs data, and major geopolitical headlines. Your full 7:00 AM briefing covers the day's specific catalysts."},
        ],
        "sources": [
            {"label": "Stooq (market data)", "url": "https://stooq.com"},
            {"label": "Yahoo Finance — Markets", "url": "https://finance.yahoo.com/markets/"},
            {"label": "CNBC Markets", "url": "https://www.cnbc.com/markets/"},
        ],
    }

    payload = "/* Auto-generated by GitHub Actions. Do not edit by hand. */\n"
    payload += "window.BRIEFING = " + json.dumps(briefing, ensure_ascii=False, indent=2) + ";\n"

    with open("data.js", "w", encoding="utf-8") as f:
        f.write(payload)

    ok = sum(1 for r in us + asia + europe + fx + commodities if r["chg"] != "n/a")
    total = len(us + asia + europe + fx + commodities)
    print(f"Wrote data.js — {ok}/{total} symbols fetched successfully.")


if __name__ == "__main__":
    main()
