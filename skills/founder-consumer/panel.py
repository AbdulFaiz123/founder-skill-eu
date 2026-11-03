#!/usr/bin/env python3
"""The buyer panel for founder-consumer (EU edition). Standard library only, no network.

It does the bookkeeping for a swarm of simulated buyers: it deals one persona card
per buyer from your target-customer profile (income, age, behaviour, objection),
writes one brief per buyer for a sub-agent to answer, checks the answers, and
tallies who buys, who doesn't, and why.

    python3 panel.py init --customer founder/customer.json --pitch founder/pitch.md [--n 100 | --quick] [--seed 7]
    python3 panel.py prompts [--wave 10]     # one brief per buyer still to run, listed in waves
    python3 panel.py check                   # which answers are missing or broken
    python3 panel.py save P003 < reply.txt   # file a buyer's own JSON that it printed instead of writing
    python3 panel.py tally [--out founder/panel/results.md]
    python3 panel.py compare                 # buy rate of this run against the last archived run
    python3 panel.py status

State lives in founder/panel/ (--dir to change it): panel.json, personas.json,
briefs/<id>.md, answers/<id>.json, results.md, results.json. Every init starts a
fresh run: the previous run (its answers, briefs and results) is moved to
runs/run-<k>/ first, so a re-test with a new pitch never reuses old answers.

The tool never answers for a buyer. Every number in results.md is counted from
the answer files the sub-agents wrote. Simulated buyers are a fast, cheap way to
find objections and weak spots. They are not customers: confirm what matters
with real ones (a pre-sale, a waitlist, a landing page with a price on it).
"""

import argparse
import json
import os
import random
import re
import shutil
import sys

# a mix that looks like a European city today; customer.json "names" overrides it
FIRST_NAMES = [
    "Lukas", "Mia", "Leon", "Emilia", "Finn", "Hannah", "Jonas", "Lea", "Paul", "Sophie", "Elias", "Lina", "Felix",
    "Marie", "Noah", "Clara", "Ben", "Johanna", "Maximilian", "Laura", "Tim", "Anna", "Julian", "Lena", "Moritz",
    "Katharina", "Niklas", "Greta", "Jan", "Charlotte", "Emre", "Elif", "Mehmet", "Zeynep", "Can", "Ayse", "Kerem",
    "Selin", "Piotr", "Kasia", "Tomasz", "Agnieszka", "Marco", "Giulia", "Luca", "Chiara", "Alessandro", "Sofia",
    "Javier", "Lucia", "Pablo", "Carmen", "Diego", "Ines", "Thomas", "Camille", "Louis", "Chloe", "Hugo", "Manon",
    "Daan", "Sanne", "Bram", "Femke", "Lars", "Ingrid", "Erik", "Freya", "Mateusz", "Ana", "Andrei", "Ioana",
    "Nikola", "Milena", "Dimitris", "Eleni", "Joao", "Beatriz", "Rohan", "Priya", "Arjun", "Ananya", "Faiz",
    "Ayesha", "Omar", "Layla", "Yusuf", "Amira", "Karim", "Nour", "Kwame", "Amara", "Wei", "Mei", "Hiroshi",
    "Yuki", "Minh", "Linh", "Oleksandr", "Olena", "Dmytro", "Iryna", "Samuel", "Ella", "Oskar", "Ida", "Emil",
    "Frieda", "Anton", "Mathilda", "Valentin", "Nele", "Konstantin", "Pia", "Malte", "Svenja", "Jakob", "Theresa",
]
CURRENCY_SYMBOL = {"EUR": "€", "GBP": "£", "USD": "$", "CHF": "CHF", "PLN": "zł", "SEK": "kr", "DKK": "kr", "CZK": "Kč"}
REASONS = ["price", "habit", "need", "trust", "quality", "convenience", "timing", "values", "other"]
ANSWER_FIELDS = {"id", "buys", "reason_code", "reason"}
WAVE = 10


class PanelError(Exception):
    pass


# ── dealing ─────────────────────────────────────────────────────────────────────
def _quota(items, n, key="share"):
    """Split n across items by their shares, exactly (largest remainder)."""
    total = sum(float(it.get(key, 1)) for it in items) or 1.0
    raw = [n * float(it.get(key, 1)) / total for it in items]
    counts = [int(r) for r in raw]
    order = sorted(range(len(items)), key=lambda i: raw[i] - counts[i], reverse=True)
    for i in order[: n - sum(counts)]:
        counts[i] += 1
    return counts


def validate_customer(c):
    for k in ("business", "target", "segments", "behaviours", "objections"):
        if k not in c or c[k] in ("", [], None):
            raise PanelError("customer.json needs '%s'" % k)
    for s in c["segments"]:
        if "name" not in s or "income" not in s or len(s["income"]) != 2:
            raise PanelError("every segment needs a name and an income [low, high]")
    for b in c["behaviours"]:
        if "name" not in b:
            raise PanelError("every behaviour needs a name")


def deal(customer, n=100, seed=7):
    """Deal n persona cards. Same customer + n + seed = the same cards, every time."""
    validate_customer(customer)
    if n < 1:
        raise PanelError("--n must be at least 1")
    rng = random.Random(seed)
    age = customer.get("age", [25, 45])
    segs = []
    for s, k in zip(customer["segments"], _quota(customer["segments"], n)):
        segs += [s] * k
    behs = []
    for b, k in zip(customer["behaviours"], _quota(customer["behaviours"], n)):
        behs += [b] * k
    rng.shuffle(segs)
    rng.shuffle(behs)
    pool = customer.get("names") or FIRST_NAMES
    names = pool[:]
    rng.shuffle(names)
    while len(names) < n:
        names += ["%s %d" % (x, len(names) // len(pool) + 1) for x in pool]
    objections = customer["objections"]
    habits = customer.get("habits") or []
    cards = []
    for i in range(n):
        s, b = segs[i], behs[i]
        lo, hi = float(s["income"][0]), float(s["income"][1])
        cards.append({
            "id": "P%03d" % (i + 1),
            "name": names[i],
            "age": rng.randint(int(age[0]), int(age[1])),
            "segment": s["name"],
            "income": int(round(rng.uniform(lo, hi), -3)),
            "behaviour": b["name"],
            "behaviour_how": b.get("how", ""),
            "objection": objections[rng.randrange(len(objections))],
            "habit": habits[rng.randrange(len(habits))] if habits else "",
        })
    return cards


# ── state ───────────────────────────────────────────────────────────────────────
def _path(d, *p):
    return os.path.join(d, *p)


def _read_json(path):
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def _write_json(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)
        fh.write("\n")


def archive(d):
    """Move the current run to runs/run-<k>/ so the next init starts clean. Returns the run folder or None."""
    if not os.path.exists(_path(d, "panel.json")):
        return None
    k = 1
    while os.path.exists(_path(d, "runs", "run-%d" % k)):
        k += 1
    dest = _path(d, "runs", "run-%d" % k)
    os.makedirs(dest)
    for name in ("panel.json", "personas.json", "briefs", "answers", "results.md", "results.json", "compare.md"):
        if os.path.exists(_path(d, name)):
            shutil.move(_path(d, name), os.path.join(dest, name))
    return dest


def init(d, customer_path, pitch_path, n=100, seed=None):
    try:
        customer = _read_json(customer_path)
    except FileNotFoundError:
        raise PanelError("no such file: %s" % customer_path)
    try:
        with open(pitch_path, encoding="utf-8") as fh:
            pitch = fh.read().strip()
    except FileNotFoundError:
        raise PanelError("no such file: %s (write the pitch first: what you sell, the price, where)" % pitch_path)
    if not pitch:
        raise PanelError("the pitch is empty")
    if seed is None:
        seed = random.SystemRandom().randrange(1, 10 ** 6)
    cards = deal(customer, n, seed)
    archive(d)
    _write_json(_path(d, "panel.json"), {"n": n, "seed": seed, "customer": customer, "pitch": pitch})
    _write_json(_path(d, "personas.json"), cards)
    os.makedirs(_path(d, "briefs"), exist_ok=True)
    os.makedirs(_path(d, "answers"), exist_ok=True)
    return cards


def load_state(d):
    try:
        return _read_json(_path(d, "panel.json")), _read_json(_path(d, "personas.json"))
    except FileNotFoundError:
        raise PanelError("no panel in %s: run init first" % d)


BRIEF = """You are a simulated buyer on a consumer panel. A founder wants to know, before spending any money, whether real people like you would buy. Your answer is only useful if it is honest: most people do not buy most things, and a polite yes is worse than a clear no.

=== WHO YOU ARE ===
{name}, {age}. {segment}. You earn about {income_text} a year before tax.
How you buy: {behaviour}. {behaviour_how}
{habit_line}The first thing that comes to mind when you hear an offer like this: "{objection}"
You are one of these people: {target}.{where_line}
=== END ===

=== WHAT IS BEING OFFERED (you see it for the first time, the way a passer-by or a scroller would) ===
{pitch}
=== END ===

Decide as {name} would, with {name}'s money, habits and doubts, in a normal week where you live. Do not be agreeable. Do not invent facts about the business beyond what is written above. Prices are in {currency}, as a customer here would see them (VAT included unless the offer says otherwise).

Create the file {out} with your file-writing tool (do not just print the answer in your reply) containing ONLY this JSON, no markdown fence, nothing else:
{{
  "id": "{id}",
  "buys": true or false,
  "purchases_first_month": how many times you would buy in the first month (0 if you would not buy),
  "reason_code": one of {reasons},
  "reason": "why, in one or two sentences, in your own voice",
  "objection": "the doubt that weighs most for you, in your own words",
  "would_change_my_mind": "the one thing that would flip your answer, or empty",
  "price_too_cheap": the price at which it would seem too cheap to be any good (a JSON number with a dot, e.g. 3.5),
  "price_cheap": the price at which it would feel like a bargain (a JSON number),
  "price_expensive": the price at which it starts to feel expensive but you might still buy (a JSON number),
  "price_too_expensive": the price at which you would not buy it at all (a JSON number)
}}
"""


def write_briefs(d, wave=WAVE):
    state, cards = load_state(d)
    cust = state["customer"]
    target = cust["target"]
    cur = cust.get("currency", "EUR")
    where = cust.get("where")
    todo = []
    for c in cards:
        out = _path(d, "answers", c["id"] + ".json")
        if _answer_ok(out, c["id"]) is None:
            continue
        brief = BRIEF.format(pitch=state["pitch"], target=target, out=os.path.abspath(out),
                             habit_line=("Your day: %s.\n" % c["habit"]) if c.get("habit") else "",
                             reasons=" / ".join(REASONS), currency=cur,
                             income_text=money(c["income"], cur),
                             where_line=(" You live in or near %s." % where) if where else "", **c)
        bp = _path(d, "briefs", c["id"] + ".md")
        with open(bp, "w", encoding="utf-8") as fh:
            fh.write(brief)
        todo.append((c["id"], os.path.abspath(bp)))
    waves = [todo[i:i + wave] for i in range(0, len(todo), wave)]
    return waves


def _answer_ok(path, pid):
    """None if the answer file is good, else a short problem string."""
    if not os.path.exists(path):
        return "missing"
    try:
        a = _read_json(path)
    except (json.JSONDecodeError, UnicodeDecodeError):
        return "not valid JSON"
    missing = ANSWER_FIELDS - set(a)
    if missing:
        return "missing " + ", ".join(sorted(missing))
    if a.get("id") != pid:
        return "id is %r, expected %s" % (a.get("id"), pid)
    if not isinstance(a.get("buys"), bool):
        return "'buys' must be true or false"
    if a.get("reason_code") not in REASONS:
        return "reason_code %r is not one of %s" % (a.get("reason_code"), ", ".join(REASONS))
    return None


def save(d, pid, text):
    """File a buyer's OWN answer that it printed instead of writing. Never used to answer for a buyer."""
    _, cards = load_state(d)
    if pid not in {c["id"] for c in cards}:
        raise PanelError("no buyer %s on this panel" % pid)
    start = text.find("{")
    if start < 0:
        raise PanelError("no JSON object in the reply")
    try:
        obj, _ = json.JSONDecoder().raw_decode(text[start:])
    except json.JSONDecodeError as e:
        raise PanelError("the reply's JSON does not parse: %s" % e)
    path = _path(d, "answers", pid + ".json")
    _write_json(path, obj)
    prob = _answer_ok(path, pid)
    if prob:
        os.remove(path)
        raise PanelError("%s's answer is not valid (%s); re-run its brief instead" % (pid, prob))
    return path


def check(d):
    _, cards = load_state(d)
    probs = []
    for c in cards:
        p = _answer_ok(_path(d, "answers", c["id"] + ".json"), c["id"])
        if p:
            probs.append((c["id"], p))
    return probs


# ── tally ───────────────────────────────────────────────────────────────────────
def _rate(rows):
    return (sum(1 for r in rows if r["buys"]) / len(rows)) if rows else 0.0


def money(v, cur="EUR"):
    """German-style whole amount: 52.000 €."""
    return "%s %s" % ("{:,.0f}".format(v).replace(",", "."), CURRENCY_SYMBOL.get(cur, cur))


def _num(v):
    """A number, also from "12,50" or "12.50" strings. None if missing or ambiguous ("1.234")."""
    if isinstance(v, bool) or v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = re.sub(r"[€$£\s\u00a0]|EUR|CHF", "", str(v))
    if not re.fullmatch(r"[0-9]+([.,][0-9]{1,2})?", s):
        return None
    return float(s.replace(",", "."))


def tally(d):
    state, cards = load_state(d)
    by_id = {c["id"]: c for c in cards}
    rows, skipped = [], []
    for c in cards:
        path = _path(d, "answers", c["id"] + ".json")
        p = _answer_ok(path, c["id"])
        if p:
            skipped.append((c["id"], p))
            continue
        a = _read_json(path)
        rows.append(dict(by_id[c["id"]], **{k: v for k, v in a.items() if k != "id"}, id=c["id"]))
    if not rows:
        raise PanelError("no valid answers yet: run the briefs first (panel.py prompts)")

    def group(key):
        out = {}
        for r in rows:
            out.setdefault(r[key], []).append(r)
        return sorted(((k, len(v), _rate(v)) for k, v in out.items()), key=lambda t: -t[2])

    # income in thirds of the dealt range, so the bands mean the same thing every run
    cur = state["customer"].get("currency", "EUR")
    incomes = sorted(r["income"] for r in rows)
    cut1, cut2 = incomes[len(incomes) // 3], incomes[2 * len(incomes) // 3]
    for r in rows:
        r["income_band"] = ("under %s" % money(cut1, cur)) if r["income"] < cut1 else (
            ("%s and up" % money(cut2, cur)) if r["income"] >= cut2 else "%s to %s" % (money(cut1, cur), money(cut2, cur)))

    no = [r for r in rows if not r["buys"]]
    yes = [r for r in rows if r["buys"]]

    def reasons(rs):
        out = {}
        for r in rs:
            out.setdefault(r["reason_code"], []).append(r)
        return sorted(((k, v) for k, v in out.items()), key=lambda kv: -len(kv[1]))

    def mean(vals):
        vals = [v for v in vals if v is not None]
        return sum(vals) / len(vals) if vals else None

    res = {
        "business": state["customer"]["business"], "seed": state["seed"], "dealt": len(cards), "pitch": state["pitch"],
        "answered": len(rows), "skipped": skipped, "buys": len(yes), "passes": len(no),
        "buy_rate": len(yes) / len(rows),
        "by_segment": group("segment"), "by_behaviour": group("behaviour"), "by_income": group("income_band"),
        "why_not": [(k, len(v), [r["reason"] for r in v[:2]], [r["id"] for r in v[:2]]) for k, v in reasons(no)],
        "why_yes": [(k, len(v), [r["reason"] for r in v[:2]], [r["id"] for r in v[:2]]) for k, v in reasons(yes)],
        "flip": [r["would_change_my_mind"] for r in no if (r.get("would_change_my_mind") or "").strip()],
        "purchases_first_month_per_buyer": mean([_num(r.get("purchases_first_month")) for r in yes]),
        "price_answers": sum(1 for r in rows if all(_num(r.get(k)) is not None for k in
                                                     ("price_too_cheap", "price_cheap", "price_expensive", "price_too_expensive"))),
    }
    return res


def compare(d):
    """(before, after): results.json of the last archived run and of this run."""
    try:
        after = _read_json(_path(d, "results.json"))
    except FileNotFoundError:
        raise PanelError("no results for this run yet: run panel.py tally first")
    k = 1
    while os.path.exists(_path(d, "runs", "run-%d" % (k + 1))):
        k += 1
    try:
        before = _read_json(_path(d, "runs", "run-%d" % k, "results.json"))
    except FileNotFoundError:
        raise PanelError("no earlier run with results in %s" % _path(d, "runs"))
    return before, after


def compare_md(before, after):
    pct = lambda v: "%.0f%%" % (v * 100)
    L = ["# Re-test: before and after", "",
         "| | buyers | buy | buy rate | seed |", "| --- | ---: | ---: | ---: | ---: |",
         "| before | %d | %d | %s | %s |" % (before["answered"], before["buys"], pct(before["buy_rate"]), before["seed"]),
         "| after | %d | %d | %s | %s |" % (after["answered"], after["buys"], pct(after["buy_rate"]), after["seed"]), ""]
    if before["seed"] != after["seed"] or before["dealt"] != after["dealt"]:
        L += ["Different buyers were dealt (seed or size changed), so part of the difference is the people, not the offer.", ""]
    b = {k: n for k, n, *_ in before["why_not"]}
    a = {k: n for k, n, *_ in after["why_not"]}
    L += ["| reason to pass | before | after |", "| --- | ---: | ---: |"]
    for k in sorted(set(a) | set(b), key=lambda k: -(b.get(k, 0))):
        L.append("| %s | %d | %d |" % (k, b.get(k, 0), a.get(k, 0)))
    return "\n".join(L) + "\n"


def results_md(res):
    pct = lambda v: "%.0f%%" % (v * 100)
    L = ["# Buyer panel: %s" % res["business"], ""]
    L.append("**%d buy · %d pass** (%s buy) out of %d simulated buyers. Seed %s, so the same cards can be dealt again."
             % (res["buys"], res["passes"], pct(res["buy_rate"]), res["answered"], res["seed"]))
    if res["skipped"]:
        L.append("")
        L.append("%d of %d buyers have no valid answer and are left out: %s." % (
            len(res["skipped"]), res["dealt"], ", ".join("%s (%s)" % s for s in res["skipped"][:10])))
    L.append("")
    L.append("These are simulated buyers, not customers. Use this to find objections and weak spots, then confirm the"
             " big ones with real people before you spend.")
    for title, key in (("By segment", "by_segment"), ("By buying behaviour", "by_behaviour"), ("By income", "by_income")):
        L += ["", "## %s" % title, "", "| group | buyers | buy rate |", "| --- | ---: | ---: |"]
        for k, n, r in res[key]:
            L.append("| %s | %d | %s%s |" % (k, n, pct(r), "  (thin)" if n < 8 else ""))
    L += ["", "## Why they pass", "", "| reason | buyers | in their words |", "| --- | ---: | --- |"]
    for k, n, quotes, ids in res["why_not"]:
        L.append("| %s | %d | %s |" % (k, n, " · ".join('"%s" (%s)' % (q.replace("|", "/"), i) for q, i in zip(quotes, ids))))
    L += ["", "## Why they buy", "", "| reason | buyers | in their words |", "| --- | ---: | --- |"]
    for k, n, quotes, ids in res["why_yes"]:
        L.append("| %s | %d | %s |" % (k, n, " · ".join('"%s" (%s)' % (q.replace("|", "/"), i) for q, i in zip(quotes, ids))))
    if res["flip"]:
        L += ["", "## What would flip a no", ""]
        for f in res["flip"][:12]:
            L.append("- %s" % f)
    if res["purchases_first_month_per_buyer"] is not None:
        L += ["", "Buyers say they would buy **%.1f times** in the first month on average." % res["purchases_first_month_per_buyer"]]
    if res["price_answers"]:
        L += ["", "%d buyers gave all four price answers. Run founder-pricing's van_westendorp.py on the answers folder." % res["price_answers"]]
    return "\n".join(L) + "\n"


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--dir", default=os.path.join("founder", "panel"))
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("init")
    i.add_argument("--customer", required=True)
    i.add_argument("--pitch", required=True)
    i.add_argument("--n", type=int, default=100)
    i.add_argument("--quick", action="store_true", help="a first look: 20 buyers instead of 100")
    i.add_argument("--seed", type=int)
    p = sub.add_parser("prompts")
    p.add_argument("--wave", type=int, default=WAVE)
    sub.add_parser("check")
    sv = sub.add_parser("save")
    sv.add_argument("id")
    t = sub.add_parser("tally")
    t.add_argument("--out")
    sub.add_parser("compare")
    sub.add_parser("status")
    a = ap.parse_args(argv)
    try:
        if a.cmd == "init":
            had_run = os.path.exists(_path(a.dir, "panel.json"))
            cards = init(a.dir, a.customer, a.pitch, 20 if a.quick else a.n, a.seed)
            st, _ = load_state(a.dir)
            if had_run:
                print("the previous run was moved to %s" % _path(a.dir, "runs"))
            print("dealt %d buyers (seed %s) into %s. Next: panel.py prompts" % (len(cards), st["seed"], a.dir))
        elif a.cmd == "prompts":
            waves = write_briefs(a.dir, a.wave)
            n = sum(len(w) for w in waves)
            if not n:
                print("every buyer has a valid answer. Next: panel.py tally")
            else:
                print("%d briefs in %d waves of up to %d. Launch one wave at a time:" % (n, len(waves), a.wave))
                for k, w in enumerate(waves, 1):
                    print("wave %d: %s" % (k, " ".join("%s=%s" % job for job in w)))
        elif a.cmd == "check":
            probs = check(a.dir)
            if not probs:
                print("all answers present and valid")
            for pid, prob in probs:
                print("%s: %s" % (pid, prob))
            return 1 if probs else 0
        elif a.cmd == "save":
            print("saved %s" % save(a.dir, a.id, sys.stdin.read()))
        elif a.cmd == "tally":
            res = tally(a.dir)
            text = results_md(res)
            out = a.out or _path(a.dir, "results.md")
            with open(out, "w", encoding="utf-8") as fh:
                fh.write(text)
            _write_json(_path(a.dir, "results.json"), res)
            print("%d buy · %d pass (%.0f%%). Wrote %s" % (res["buys"], res["passes"], res["buy_rate"] * 100, out))
        elif a.cmd == "compare":
            before, after = compare(a.dir)
            text = compare_md(before, after)
            with open(_path(a.dir, "compare.md"), "w", encoding="utf-8") as fh:
                fh.write(text)
            sys.stdout.write(text)
        elif a.cmd == "status":
            st, cards = load_state(a.dir)
            probs = check(a.dir)
            print("%d buyers dealt (seed %s), %d answered, %d to go" % (len(cards), st["seed"], len(cards) - len(probs), len(probs)))
    except PanelError as e:
        print("error: %s" % e, file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
