#!/usr/bin/env python3
"""
Market Briefing — data builder.
Runs on GitHub Actions each morning, fetches live market data from Yahoo
Finance's public chart endpoint (free, no API key), and rewrites data.js.
Designed to fail SOFTLY: any symbol that can't be fetched shows "n/a" rather
than breaking the page.
"""
import json
import sys
import time
from datetime import datetime
from zoneinfo import ZoneInfo

import requests

TZ = ZoneInfo("Asia/Bangkok")
HOSTS = ["https://query1.finance.yahoo.com", "https://query2.finance.yahoo.com"]
HEADERS = {
    "User-Agent": ("Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                   "AppleWebKit/537.36 (KHTML, like Gecko) "
                   "Chrome/124.0 Safari/537.36"),
    "Accept": "application/json",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)


def fetch_last_prev(symbol):
    """Return (last_price, prev_close) for a Yahoo symbol, or (None, None)."""
    for host in HOSTS:
        url = f"{host}/v8/finance/chart/{symbol}"
        for attempt in range(2):
            try:
                r = SESSION.get(url, params={"interval": "1d", "range": "5d"}, timeout=20)
                if r.status_code != 200:
                    time.sleep(1)
                    continue
                data = r.json()
                result = (data.get("chart", {}).get("result") or [None])[0]
                if not result:
                    continue
                meta = result.get("meta", {})
                last = meta.get("regularMarketPrice")
                prev = meta.get("chartPreviousClose") or meta.get("previousClose")
                # Fallback: derive from the close series if meta is incomplete.
                if last is None or prev is None:
                    try:
                        closes = result["indicators"]["quote"][0]["close"]
                        closes = [c for c in closes if c is not None]
                        if last is None and closes:
                            last = closes[-1]
                        if prev is None and len(closes) >= 2:
                            prev = closes[-2]
                    except Exception:
                        pass
                if last is not None:
                    return float(last), (float(prev) if prev is not None else None)
            except Exception as e:
                print(f"  ! {symbol} ({host}): {e}", file=sys.stderr)
                time.sleep(1)
    return None, None


def fmt_level(v, kind):
    if v is None:
        return "—"
    if kind == "index":
        return f"{v:,.2f}"
    if kind == "yield":
        return f"{v:.2f}%"
    if kind == "fx":
        return f"{v:,.4f}" if v < 10 else f"{v:,.2f}"
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
    last, prev = fetch_last_prev(symbol)
    chg = pct_change(last, prev)
    return {
        "name": name,
        "lvl": fmt_level(last, kind),
        "chg": chg_str(chg),
        "dir": dir_of(chg),
        "_chg": chg,
    }


# ---- symbol map (Yahoo Finance tickers) -----------------------------------
US = [
    ("S&P 500", "%5EGSPC", "index"),
    ("Nasdaq Composite", "%5EIXIC", "index"),
    ("Dow Jones", "%5EDJI", "index"),
    ("PHLX Semis (SOX)", "%5ESOX", "index"),
]
ASIA = [
    ("Nikkei 225 (Tokyo)", "%5EN225", "index"),
    ("Hang Seng", "%5EHSI", "index"),
    ("Shanghai Composite", "000001.SS", "index"),
    ("Kospi (Seoul)", "%5EKS11", "index"),
]
EUROPE = [
    ("FTSE 100", "%5EFTSE", "index"),
    ("DAX", "%5EGDAXI", "index"),
]
FX = [
    ("US 10-yr Treasury", "%5ETNX", "yield"),
    ("USD/THB", "THB=X", "fx"),
    ("USD/JPY", "JPY=X", "fx"),
    ("EUR/USD", "EURUSD=X", "fx"),
    ("Dollar Index (DXY)", "DX-Y.NYB", "fx"),
]
COMMODITIES = [
    ("WTI Crude", "CL=F", "usd"),
    ("Brent Crude", "BZ=F", "usd"),
    ("Gold", "GC=F", "usd"),
]


def strip(rows):
    return [{k: v for k, v in r.items() if not k.startswith("_")} for r in rows]


def phrase(chg):
    # Number-neutral wording (reads fine after singular or plural subjects).
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
    print("Fetching market data from Yahoo Finance…")
    us = [build_row(*x) for x in US]
    asia = [build_row(*x) for x in ASIA]
    europe = [build_row(*x) for x in EUROPE]
    fx = [build_row(*x) for x in FX]
    commodities = [build_row(*x) for x in COMMODITIES]

    now = datetime.now(TZ)
    date_str = now.strftime("%A, %B %-d, %Y")
    updated_str = now.strftime("%b %-d, %Y · 7:00 AM ICT")

    spx = us[0]["_chg"]
    ndq = us[1]["_chg"]
    wti = commodities[0]["_chg"]
    gold = commodities[2]["_chg"]
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
             "note": "US 10-year Treasury yield, key USD pairs, and the dollar index."},
            {"icon": "🛢️", "title": "Commodities", "span": False, "rows": strip(commodities),
             "note": "WTI and Brent crude, and spot gold futures."},
            {"icon": "📅", "title": "Macro Watch", "span": True, "rows": [],
             "note": "Watch central-bank commentary, scheduled inflation/jobs data, and major geopolitical headlines. Your full 7:00 AM briefing covers the day's specific catalysts."},
        ],
        "sources": [
            {"label": "Yahoo Finance — Markets", "url": "https://finance.yahoo.com/markets/"},
            {"label": "CNBC Markets", "url": "https://www.cnbc.com/markets/"},
            {"label": "Trading Economics", "url": "https://tradingeconomics.com/"},
        ],
    }

    payload = "/* Auto-generated by GitHub Actions. Do not edit by hand. */\n"
    payload += "window.BRIEFING = " + json.dumps(briefing, ensure_ascii=False, indent=2) + ";\n"

    with open("data.js", "w", encoding="utf-8") as f:
        f.write(payload)

    ok = sum(1 for r in us + asia + europe + fx + commodities if r["chg"] != "n/a")
    total = len(us + asia + europe + fx + commodities)
    print(f"Wrote data.js — {ok}/{total} symbols fetched successfully.")
    if ok == 0:
        # Signal failure so the run is visibly red rather than silently blank.
        sys.exit(1)


if __name__ == "__main__":
    main()
