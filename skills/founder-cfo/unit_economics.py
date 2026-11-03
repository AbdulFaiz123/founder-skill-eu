#!/usr/bin/env python3
"""Unit economics for founder-cfo (EU edition). Standard library only, no network.

Takes one JSON file describing the business and prints the numbers a CFO would
check before a single euro is spent: what one unit earns after VAT and its own
costs, the real margin at the volume you plan, how many units a day you need to
break even, what year 1 looks like month by month, and how long it takes to earn
the startup money back.

    python3 unit_economics.py founder/numbers.json
    python3 unit_economics.py founder/numbers.json --out founder/cfo.md
    python3 unit_economics.py founder/numbers.json --json
    python3 unit_economics.py founder/numbers.json --price 7,50 --volume 0.8

The input (see example.json in this folder):

    business            name, for the report
    unit                what you sell one of: "cup", "order", "client-month"
    currency            "EUR" (default), "GBP", "CHF", "PLN", "SEK", "DKK", "CZK"...
    number_format       "de" (1.234,56 EUR, default) or "en" (EUR1,234.56) for the report
    price               the price per unit as the customer sees it
    price_includes_vat  true (default, how B2C prices are shown in the EU) or false (B2B net price)
    vat_rate            e.g. 0.19 or 0.07 in Germany, 0.21 in the Netherlands; required
                        unless kleinunternehmer is true
    kleinunternehmer    true if you use a small-business VAT exemption (Germany: section 19
                        UStG); then no VAT is charged and input VAT is not refunded
    variable            [{label, cost}]  cost of ONE unit, net of reclaimable VAT
                        (gross if you are a Kleinunternehmer): ingredients, packaging,
                        shipping, card fees, a per-unit commission
    fixed_monthly       [{label, cost}]  costs you pay every month whatever you sell:
                        rent, software, insurance, Berufsgenossenschaft, Steuerberater
    payroll             [{label, gross_monthly, kind}]  staff by gross monthly wage;
                        kind is "regular" (default) or "minijob"; employer social
                        contributions are added on top (see payroll_oncost)
    payroll_oncost      {"regular": 0.21, "minijob": 0.31} by default (estimates for
                        Germany: confirm with a payroll office)
    startup             [{label, cost}]  one-off spend before you open
    days_per_month      selling days in a month (default 30; 26 if you close on Sundays)
    capacity_per_day    the most units a day you can physically sell (optional)
    plan_per_day        the volume you plan for once you are up and running
    ramp_per_day        12 numbers: units a day in each month of year 1
                        (optional; default = plan_per_day every month)

Numbers may be JSON numbers or strings in either style: "12,50", "1.234,56",
"1,234.56", "€ 6,50". A string like "1.234" is ambiguous (one euro or a thousand?)
and is refused, never guessed.

Every number in the report comes from that file. Nothing is looked up or
guessed. A missing cost section is reported as missing, and founder-plan will
not call the business profitable until it is filled in (an empty list [] means
"none" and is accepted).

--price and --volume run a what-if without editing the file: --price replaces
the price, --volume scales every volume (0.8 = 20 percent fewer sales).
"""

import argparse
import json
import math
import re
import sys

REQUIRED = ("price", "variable", "fixed_monthly", "startup")
SYMBOLS = {"EUR": "€", "GBP": "£", "USD": "$", "CHF": "CHF ", "PLN": "zł", "SEK": "kr", "DKK": "kr",
           "NOK": "kr", "CZK": "Kč", "HUF": "Ft", "RON": "lei"}
DEFAULT_ONCOST = {"regular": 0.21, "minijob": 0.31}
# Germany, section 19 UStG since 2025: the founding year's turnover must stay at or under 25,000 EUR
KLEINUNTERNEHMER_LIMIT = 25000.0


class NumbersError(Exception):
    pass


def parse_amount(v, field="value"):
    """A number from JSON or from a string in EU or US style. Ambiguous strings raise."""
    if isinstance(v, bool) or v is None:
        raise NumbersError("%s is not a number: %r" % (field, v))
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[€$£'\s  ]|EUR|USD|GBP|CHF|zł|Kč|kr|Ft|lei", "", str(v))
    neg = s.startswith("-")
    s = s.lstrip("-")
    if not re.fullmatch(r"[0-9][0-9.,]*", s or ""):
        raise NumbersError("%s is not a number: %r" % (field, v))
    if "," in s and "." in s:
        dec = "," if s.rfind(",") > s.rfind(".") else "."
        s = s.replace("." if dec == "," else ",", "").replace(dec, ".")
    elif "," in s or "." in s:
        sep = "," if "," in s else "."
        parts = s.split(sep)
        if len(parts) > 2:
            if not all(len(p) == 3 for p in parts[1:]):
                raise NumbersError("%s is not a number: %r" % (field, v))
            s = "".join(parts)
        elif len(parts[1]) == 3 and parts[0] != "0":
            raise NumbersError("%s %r is ambiguous (a decimal or a thousand?): write it as a plain JSON number,"
                               " e.g. %s or %s" % (field, v, "".join(parts), parts[0] + "." + parts[1]))
        else:
            s = parts[0] + "." + parts[1]
    return -float(s) if neg else float(s)


def money(v, currency="EUR", fmt="de", decimals=2):
    sym = SYMBOLS.get(currency, currency + " ")
    body = ("{:,.%df}" % decimals).format(abs(v))
    sign = "-" if v < 0 else ""
    if fmt == "de":
        body = body.replace(",", "_").replace(".", ",").replace("_", ".")
        return "%s%s %s" % (sign, body, sym.strip())
    return "%s%s%s" % (sign, sym, body)


def _sum(items, field):
    total = 0.0
    if not isinstance(items, list):
        raise NumbersError("'%s' must be a list of {label, cost}" % field)
    for i, it in enumerate(items):
        if not isinstance(it, dict) or "cost" not in it:
            raise NumbersError("%s[%d] needs a 'cost'" % (field, i))
        total += parse_amount(it["cost"], "%s[%d].cost" % (field, i))
    return total


def payroll_lines(spec):
    """[(label, gross, oncost, total)] with employer contributions added."""
    rates = dict(DEFAULT_ONCOST, **(spec.get("payroll_oncost") or {}))
    out = []
    for i, p in enumerate(spec.get("payroll") or []):
        if not isinstance(p, dict) or "gross_monthly" not in p:
            raise NumbersError("payroll[%d] needs a 'gross_monthly'" % i)
        kind = p.get("kind", "regular")
        if kind not in rates:
            raise NumbersError("payroll[%d].kind must be one of %s" % (i, ", ".join(sorted(rates))))
        gross = parse_amount(p["gross_monthly"], "payroll[%d].gross_monthly" % i)
        oncost = gross * parse_amount(rates[kind], "payroll_oncost.%s" % kind)
        out.append((p.get("label", "staff"), gross, oncost, gross + oncost, kind))
    return out


def load(path):
    try:
        with open(path, encoding="utf-8") as fh:
            return json.load(fh)
    except FileNotFoundError:
        raise NumbersError("no such file: %s" % path)
    except json.JSONDecodeError as e:
        raise NumbersError("%s is not valid JSON: %s" % (path, e))


def analyse(spec, price=None, volume=1.0):
    """Return a dict of every number in the report. Pure function, easy to test."""
    missing = [k for k in REQUIRED if k not in spec and not (k == "price" and price is not None)]
    if "fixed_monthly" in missing and "payroll" in spec:
        missing.remove("fixed_monthly")
    if "price" in missing:
        raise NumbersError("'price' is missing")
    p = parse_amount(price if price is not None else spec["price"], "price")
    if p <= 0:
        raise NumbersError("price must be above zero")

    ku = bool(spec.get("kleinunternehmer", False))
    incl = bool(spec.get("price_includes_vat", True))
    if ku:
        vat = 0.0
    elif "vat_rate" not in spec:
        raise NumbersError("'vat_rate' is missing (e.g. 0.19), or set \"kleinunternehmer\": true")
    else:
        vat = parse_amount(spec["vat_rate"], "vat_rate")
        if vat > 1:
            vat = vat / 100.0  # someone wrote 19 for 19%
    net = p / (1 + vat) if incl else p
    gross = net * (1 + vat)

    days = parse_amount(spec.get("days_per_month", 30), "days_per_month")
    var = _sum(spec.get("variable", []), "variable")
    staff = payroll_lines(spec)
    fixed = _sum(spec.get("fixed_monthly", []), "fixed_monthly") + sum(s[3] for s in staff)
    startup = _sum(spec.get("startup", []), "startup")

    if "plan_per_day" not in spec and "ramp_per_day" not in spec:
        raise NumbersError("give 'plan_per_day' or 'ramp_per_day' (12 numbers)")
    plan = parse_amount(spec.get("plan_per_day", 0), "plan_per_day") * volume
    ramp = spec.get("ramp_per_day")
    if ramp is None:
        ramp = [plan] * 12
    else:
        if len(ramp) != 12:
            raise NumbersError("'ramp_per_day' needs 12 numbers, one per month (got %d)" % len(ramp))
        ramp = [parse_amount(v, "ramp_per_day") * volume for v in ramp]
    if not plan:
        plan = ramp[-1]

    contribution = net - var
    contribution_pct = contribution / net
    breakeven_day = math.inf if contribution <= 0 else fixed / (contribution * days)
    plan_units_month = plan * days
    margin_at_plan = (contribution - (fixed / plan_units_month if plan_units_month else math.inf)) / net

    months = []
    cumulative = -startup
    payback_month = None
    turnover = 0.0
    ku_lost_month = None
    for m, per_day in enumerate(ramp, start=1):
        units = per_day * days
        revenue = units * net
        variable_cost = units * var
        profit = revenue - variable_cost - fixed
        cumulative += profit
        turnover += revenue
        if ku and ku_lost_month is None and turnover > KLEINUNTERNEHMER_LIMIT:
            ku_lost_month = m
        if payback_month is None and cumulative >= 0:
            payback_month = m
        months.append({"month": m, "per_day": per_day, "units": units, "revenue": revenue,
                       "vat": units * (gross - net), "variable": variable_cost, "fixed": fixed,
                       "profit": profit, "cumulative": cumulative})
    year_profit = sum(m["profit"] for m in months)
    year_revenue = sum(m["revenue"] for m in months)
    year_vat = sum(m["vat"] for m in months)
    # the cash you need: startup plus the deepest hole the monthly losses dig
    lowest = min([-startup] + [m["cumulative"] for m in months])
    cash_needed = -lowest

    cur, fmt = spec.get("currency", "EUR"), spec.get("number_format", "de")
    capacity = spec.get("capacity_per_day")
    if capacity is not None:
        capacity = parse_amount(capacity, "capacity_per_day")
    flags, notes = [], []
    if missing:
        flags.append("Missing from numbers.json: %s. Add them (use [] for none) before trusting any number below."
                     % ", ".join(missing))
    if "variable" in spec and not spec["variable"]:
        notes.append("No variable costs given. Almost every sale has some (card fees, packaging): check.")
    if contribution <= 0:
        flags.append("Each unit loses money before rent and salaries: the net price is below the variable cost.")
    if capacity is not None and breakeven_day > capacity:
        flags.append("Break-even needs %.0f %ss a day but capacity is %g." % (breakeven_day, spec.get("unit", "unit"), capacity))
    if capacity is not None and plan > capacity:
        flags.append("The plan (%.0f a day) is above capacity (%g)." % (plan, capacity))
    if year_profit < 0:
        flags.append("Year 1 loses money on operations (%s)." % money(year_profit, cur, fmt, 0))
    if payback_month is None:
        flags.append("The startup spend is not earned back within year 1.")
    if ku_lost_month:
        flags.append("Kleinunternehmer: turnover passes %s in month %d. From that sale on you charge VAT, so the"
                     " same shelf price earns less. Re-run with kleinunternehmer false and your vat_rate."
                     % (money(KLEINUNTERNEHMER_LIMIT, cur, fmt, 0), ku_lost_month))
    if not ku and year_revenue <= KLEINUNTERNEHMER_LIMIT:
        notes.append("Year 1 turnover is under %s: in Germany you may qualify as a Kleinunternehmer (no VAT to"
                     " charge, but no input VAT back). Ask your Steuerberater." % money(KLEINUNTERNEHMER_LIMIT, cur, fmt, 0))

    return {
        "business": spec.get("business", ""), "unit": spec.get("unit", "unit"), "currency": cur, "number_format": fmt,
        "price": p, "price_includes_vat": incl, "vat_rate": vat, "kleinunternehmer": ku,
        "net_price": net, "gross_price": gross, "vat_per_unit": gross - net,
        "variable_per_unit": var, "contribution": contribution,
        "contribution_pct": contribution_pct, "fixed_monthly": fixed, "payroll_monthly": sum(s[3] for s in staff),
        "startup": startup, "plan_per_day": plan, "margin_at_plan": margin_at_plan, "breakeven_per_day": breakeven_day,
        "capacity_per_day": capacity, "year1_revenue": year_revenue, "year1_vat": year_vat,
        "year1_profit": year_profit, "year1_after_startup": year_profit - startup, "payback_month": payback_month,
        "cash_needed": cash_needed, "months": months, "flags": flags, "notes": notes, "missing": missing,
        "kleinunternehmer_lost_month": ku_lost_month,
        "variable_items": spec.get("variable", []), "fixed_items": spec.get("fixed_monthly", []),
        "payroll_items": staff, "startup_items": spec.get("startup", []),
    }


def sensitivity(spec):
    """The three what-ifs every plan should survive."""
    base = analyse(spec)
    rows = [("Base plan", base)]
    rows.append(("Price -10%", analyse(spec, price=base["price"] * 0.9)))
    rows.append(("Volume -20%", analyse(spec, volume=0.8)))
    worse = json.loads(json.dumps(spec))
    for it in worse.get("variable", []):
        it["cost"] = parse_amount(it["cost"]) * 1.15
    rows.append(("Unit costs +15%", analyse(worse)))
    return rows


def report(spec, a):
    u = a["unit"]
    m = lambda v, d=2: money(v, a["currency"], a["number_format"], d)
    L = []
    L.append("# Unit economics: %s" % (a["business"] or "your business"))
    L.append("")
    L.append("Every number below comes from the input file. Nothing is looked up or guessed.")
    L.append("")
    if a["missing"]:
        L.append("> **Incomplete:** %s missing from numbers.json. The numbers below treat them as zero, so they"
                 " look better than they are." % ", ".join(a["missing"]))
        L.append("")
    L.append("## One %s" % u)
    L.append("")
    L.append("| line | per %s |" % u)
    L.append("| --- | ---: |")
    if a["kleinunternehmer"]:
        L.append("| Price (Kleinunternehmer: no VAT charged) | %s |" % m(a["price"]))
    else:
        L.append("| Price the customer pays (incl. %.0f%% VAT) | %s |" % (a["vat_rate"] * 100, m(a["gross_price"])))
        L.append("| VAT you pass to the tax office | -%s |" % m(a["vat_per_unit"]))
        L.append("| Net price | %s |" % m(a["net_price"]))
    for it in a["variable_items"]:
        L.append("| %s | -%s |" % (it.get("label", "cost"), m(parse_amount(it["cost"]))))
    L.append("| **Contribution** (what each %s leaves to pay the fixed costs) | **%s** (%.0f%% of net) |"
             % (u, m(a["contribution"]), a["contribution_pct"] * 100))
    L.append("")
    L.append("## The margin that matters")
    L.append("")
    fixed_bits = ["%s %s" % (it.get("label", "cost"), m(parse_amount(it["cost"]), 0)) for it in a["fixed_items"]]
    fixed_bits += ["%s %s (%s gross + %s employer costs, %s)" % (lab, m(t, 0), m(g, 0), m(o, 0), k)
                   for lab, g, o, t, k in a["payroll_items"]]
    L.append("Fixed costs: %s a month (%s)." % (m(a["fixed_monthly"], 0), ", ".join(fixed_bits) or "none given"))
    if a["payroll_items"]:
        L.append("")
        L.append("Employer social contributions are an estimate (regular ~21%, Minijob ~31% in Germany). A payroll"
                 " office or Steuerberater confirms the real rate.")
    L.append("")
    be = a["breakeven_per_day"]
    L.append("- **Break-even: %s %ss a day.** Below that you lose money every month." % (
        "never (each unit loses money)" if math.isinf(be) else "{:,.0f}".format(math.ceil(be)), u))
    L.append("- **Profit margin at your plan** (%s a day): **%.0f%%** of every net sale, after every cost." % (
        "{:,.0f}".format(a["plan_per_day"]), a["margin_at_plan"] * 100))
    if a["capacity_per_day"] is not None:
        L.append("- Capacity: %g a day." % a["capacity_per_day"])
    L.append("")
    L.append("## Year 1, month by month")
    L.append("")
    L.append("| month | %ss a day | net revenue | profit | cumulative (after %s startup) |" % (u, m(a["startup"], 0)))
    L.append("| ---: | ---: | ---: | ---: | ---: |")
    for mo in a["months"]:
        L.append("| %d | %s | %s | %s | %s |" % (mo["month"], "{:,.0f}".format(mo["per_day"]), m(mo["revenue"], 0),
                                               m(mo["profit"], 0), m(mo["cumulative"], 0)))
    L.append("")
    L.append("- **Year 1 operating profit: %s** on %s of net revenue." % (m(a["year1_profit"], 0), m(a["year1_revenue"], 0)))
    if a["year1_vat"]:
        L.append("- VAT collected for the tax office in year 1: %s. It is not yours: keep it aside for the"
                 " Umsatzsteuer-Voranmeldung." % m(a["year1_vat"], 0))
    L.append("- After the %s startup spend: %s." % (m(a["startup"], 0), m(a["year1_after_startup"], 0)))
    L.append("- Startup money earned back: %s." % ("month %d" % a["payback_month"] if a["payback_month"] else "not within year 1"))
    L.append("- Cash you need before it pays for itself: **%s**." % m(a["cash_needed"], 0))
    L.append("- Profit here is before income tax and trade tax (Gewerbesteuer; sole traders and partnerships"
             " have a 24.500 € allowance in Germany).")
    L.append("")
    L.append("## What if")
    L.append("")
    L.append("| scenario | margin at plan | break-even a day | year 1 profit |")
    L.append("| --- | ---: | ---: | ---: |")
    for name, s in sensitivity(spec):
        be = s["breakeven_per_day"]
        L.append("| %s | %.0f%% | %s | %s |" % (name, s["margin_at_plan"] * 100,
                                              "never" if math.isinf(be) else "{:,.0f}".format(math.ceil(be)),
                                              m(s["year1_profit"], 0)))
    L.append("")
    if a["flags"]:
        L.append("## Red flags")
        L.append("")
        for f in a["flags"]:
            L.append("- %s" % f)
    else:
        L.append("No red flags in these numbers. They are only as good as the inputs: check every cost against a real quote.")
    if a["notes"]:
        L.append("")
        L.append("## Notes")
        L.append("")
        for n in a["notes"]:
            L.append("- %s" % n)
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("numbers", help="the business's numbers.json")
    ap.add_argument("--out", help="write the report here (markdown)")
    ap.add_argument("--json", action="store_true", help="print the numbers as JSON")
    ap.add_argument("--price", help="what-if price, e.g. 7,50 or 7.50")
    ap.add_argument("--volume", type=float, default=1.0, help="what-if volume multiplier")
    args = ap.parse_args(argv)
    try:
        spec = load(args.numbers)
        if args.price is not None:
            spec = dict(spec, price=parse_amount(args.price, "--price"))
        if args.volume != 1.0:
            spec = dict(spec)
            if "plan_per_day" in spec:
                spec["plan_per_day"] = parse_amount(spec["plan_per_day"]) * args.volume
            if "ramp_per_day" in spec:
                spec["ramp_per_day"] = [parse_amount(v) * args.volume for v in spec["ramp_per_day"]]
        a = analyse(spec)
        text = None if args.json else report(spec, a)
    except NumbersError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    if args.json:
        out = {k: v for k, v in a.items() if not k.endswith("_items")}
        out["breakeven_per_day"] = None if math.isinf(out["breakeven_per_day"]) else out["breakeven_per_day"]
        print(json.dumps(out, indent=1))
        return 0
    if args.out:
        with open(args.out, "w", encoding="utf-8") as fh:
            fh.write(text)
        print("wrote %s" % args.out)
    else:
        sys.stdout.write(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
