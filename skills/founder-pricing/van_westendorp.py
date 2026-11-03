#!/usr/bin/env python3
"""Price sensitivity (Van Westendorp) for founder-pricing (EU edition). Standard library only.

Every buyer on the panel answers four questions: at what price would it be too
cheap to trust, a bargain, getting expensive, and too expensive to buy. Plotted
together, those four answers give you an acceptable price range and the price
that leaves the fewest people unhappy.

    python3 van_westendorp.py founder/panel/answers
    python3 van_westendorp.py prices.csv --out founder/pricing-curve.md
    python3 van_westendorp.py founder/panel/answers --json
    python3 van_westendorp.py umfrage.csv --decimal comma --price 5,90

Input is either the panel's answers folder (one JSON per buyer, written by
founder-consumer) or a CSV with the columns too_cheap, cheap, expensive,
too_expensive (one row per respondent; extra columns are ignored). A respondent
missing any of the four numbers, or giving them out of order (too cheap must be
the lowest, too expensive the highest), is dropped and counted.

Prices can be written either way: 12,50 and 12.50 are both twelve fifty, and
1.234,56 and 1,234.56 are both one thousand two hundred and something. A lone
"1.234" or "1,234" could be either, so it is dropped (and counted) unless you
say which separator your survey used with --decimal comma or --decimal dot.
German survey tools often export ";"-separated CSVs; both ; and , work.

The four points it reports:

    PMC  point of marginal cheapness   below this, too many think it's too cheap
    PME  point of marginal expensiveness above this, too many think it's too expensive
    OPP  optimal price point            as many say "too cheap" as "too expensive"
    IPP  indifference price point       as many say "a bargain" as "expensive"

PMC to PME is the acceptable range. These are answers from simulated buyers:
use the range to choose what to TEST, then test it with real ones.
"""

import argparse
import csv
import re
import glob
import json
import os
import sys

KEYS = ("too_cheap", "cheap", "expensive", "too_expensive")


class PricingError(Exception):
    pass


SYMBOLS = {"EUR": "€", "GBP": "£", "USD": "$", "CHF": "CHF ", "PLN": "zł", "SEK": "kr", "DKK": "kr", "CZK": "Kč"}


def _f(v, decimal=None):
    """A positive price from a number or a string in EU or US style; None if missing or ambiguous."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v) if v > 0 else None
    s = re.sub(r"[€$£'\s\u00a0\u202f]|EUR|USD|GBP|CHF|zł|Kč|kr", "", str(v))
    if not re.fullmatch(r"[0-9][0-9.,]*", s):
        return None
    if decimal in (",", "."):
        thousands = "." if decimal == "," else ","
        s = s.replace(thousands, "").replace(decimal, ".")
    elif "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in s or "." in s:
        parts = s.split("," if "," in s else ".")
        if len(parts) > 2:
            if not all(len(p) == 3 for p in parts[1:]):
                return None
            s = "".join(parts)
        elif len(parts[1]) == 3 and parts[0] != "0":
            return None  # 1.234 or 1,234: a decimal or a thousand? refuse to guess
        else:
            s = parts[0] + "." + parts[1]
    try:
        x = float(s)
    except ValueError:
        return None
    return x if x > 0 else None


def read(path, decimal=None):
    """Return (rows, dropped) where rows are (too_cheap, cheap, expensive, too_expensive)."""
    raw = []
    if os.path.isdir(path):
        for fp in sorted(glob.glob(os.path.join(path, "*.json"))):
            try:
                with open(fp, encoding="utf-8") as fh:
                    a = json.load(fh)
            except (json.JSONDecodeError, UnicodeDecodeError):
                raw.append(None)
                continue
            raw.append(tuple(_f(a.get("price_" + k), decimal) for k in KEYS))
    elif path.endswith(".csv"):
        with open(path, newline="", encoding="utf-8-sig") as fh:
            header = fh.readline()  # the header has no decimal commas, so it shows the real delimiter
            fh.seek(0)
            delim = ";" if header.count(";") > header.count(",") else ","
            for r in csv.DictReader(fh, delimiter=delim):
                r = {(k or "").strip().lower(): v for k, v in r.items()}
                raw.append(tuple(_f(r.get(k), decimal) for k in KEYS))
    else:
        raise PricingError("give the panel's answers folder or a .csv")
    rows, dropped = [], 0
    for r in raw:
        if r is None or any(v is None for v in r) or not (r[0] <= r[1] <= r[2] <= r[3]):
            dropped += 1
            continue
        rows.append(r)
    return rows, dropped


def curves(rows, grid):
    n = float(len(rows))
    tc = [sum(1 for r in rows if r[0] >= p) / n for p in grid]          # too cheap at p (falls)
    ch = [sum(1 for r in rows if r[1] >= p) / n for p in grid]          # a bargain at p (falls)
    ex = [sum(1 for r in rows if r[2] <= p) / n for p in grid]          # expensive at p (rises)
    te = [sum(1 for r in rows if r[3] <= p) / n for p in grid]          # too expensive at p (rises)
    return tc, ch, ex, te


def cross(grid, falling, rising):
    """First price where the rising curve meets the falling one (linear interpolation)."""
    for i in range(1, len(grid)):
        d0 = rising[i - 1] - falling[i - 1]
        d1 = rising[i] - falling[i]
        if d0 <= 0 <= d1 and d1 != d0:
            t = -d0 / (d1 - d0)
            return grid[i - 1] + t * (grid[i] - grid[i - 1])
        if d0 == 0:
            return grid[i - 1]
    return None


def analyse(rows, step=None):
    if len(rows) < 5:
        raise PricingError("need at least 5 complete answers (got %d)" % len(rows))
    lo = min(r[0] for r in rows)
    hi = max(r[3] for r in rows)
    step = step or max(0.01, round((hi - lo) / 400, 2))
    grid, p = [], lo
    while p <= hi + 1e-9:
        grid.append(round(p, 4))
        p += step
    tc, ch, ex, te = curves(rows, grid)
    not_cheap = [1 - v for v in ch]
    not_exp = [1 - v for v in ex]
    pts = {
        "PMC": cross(grid, tc, not_cheap),
        "PME": cross(grid, not_exp, te),
        "OPP": cross(grid, tc, te),
        "IPP": cross(grid, ch, ex),
    }
    return {"n": len(rows), "points": pts, "range": [pts["PMC"], pts["PME"]],
            "median": {k: sorted(r[i] for r in rows)[len(rows) // 2] for i, k in enumerate(KEYS)}}


def money(v, currency="EUR"):
    if v is None:
        return "n/a"
    return "%s %s" % (("%.2f" % v).replace(".", ","), SYMBOLS.get(currency, currency).strip())


def report(res, dropped, price=None, currency="EUR"):
    m = lambda v: money(v, currency)
    p = res["points"]
    L = ["# Price sensitivity", "",
         "%d complete answers%s. Simulated buyers: use this to pick what to test, not as the final word." % (
             res["n"], (", %d dropped (incomplete, out of order or an ambiguous number like 1.234)" % dropped)
             if dropped else ""), "",
         "| point | price | what it means |", "| --- | ---: | --- |",
         "| PMC | %s | below this, too many think it is too cheap to be good |" % m(p["PMC"]),
         "| OPP | %s | as many say too cheap as too expensive: the least resistance |" % m(p["OPP"]),
         "| IPP | %s | as many call it a bargain as call it expensive |" % m(p["IPP"]),
         "| PME | %s | above this, too many say it is too expensive to buy |" % m(p["PME"]), "",
         "**Acceptable range: %s to %s.**" % (m(p["PMC"]), m(p["PME"])), ""]
    md = res["median"]
    L.append("Median answers: too cheap %s, a bargain %s, getting expensive %s, too expensive %s." % (
        m(md["too_cheap"]), m(md["cheap"]), m(md["expensive"]), m(md["too_expensive"])))
    if price is not None and p["PMC"] is not None and p["PME"] is not None:
        where = "inside" if p["PMC"] <= price <= p["PME"] else ("below" if price < p["PMC"] else "above")
        L += ["", "Your current price, %s, is **%s** the acceptable range." % (m(price), where)]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("source", help="the panel's answers folder, or a CSV")
    ap.add_argument("--price", help="your current price, to place it on the range (5,90 or 5.90)")
    ap.add_argument("--currency", default="EUR")
    ap.add_argument("--decimal", choices=("comma", "dot"), help="the decimal separator your CSV uses, if it is ambiguous")
    ap.add_argument("--out", help="write the report here (markdown)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv)
    decimal = {"comma": ",", "dot": "."}.get(a.decimal)
    price = None
    if a.price is not None:
        price = _f(a.price, decimal)
        if price is None:
            print("error: --price %r is not a price (or is ambiguous: use --decimal)" % a.price, file=sys.stderr)
            return 2
    try:
        rows, dropped = read(a.source, decimal)
        res = analyse(rows)
    except (PricingError, FileNotFoundError) as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if a.json:
        print(json.dumps(dict(res, dropped=dropped), indent=1))
        return 0
    text = report(res, dropped, price, a.currency)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % a.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
