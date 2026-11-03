# The Founder skill, EU edition

Eleven Claude skills that test a business before you launch it, adapted for
Europe and Germany. A fork of [founder-skill](https://github.com/Jakeschincariol/founder-skill)
by Jake Schincariol (MIT), with the four reliability bugs from its audit fixed.
No signup, no API key, nothing to connect.

`skills/founder-board` `skills/founder-marketing` `skills/founder-cfo`
`skills/founder-consumer` `skills/founder-launch` `skills/founder-pricing`
`skills/founder-offer` `skills/founder-competitors` `skills/founder-brand`
`skills/founder-ops` `skills/founder-plan`

## What is different from the original

**Money the European way**

- Prices are entered as the customer sees them, with VAT (`price_includes_vat`,
  `vat_rate`). The CFO splits every sale into net price and VAT, so VAT never
  counts as revenue, and shows the VAT to set aside for the Umsatzsteuer-Voranmeldung.
- German Kleinunternehmer (section 19 UStG, 2025 rules): the CFO flags the month
  a plan passes 25.000 € of turnover, and the plan fails a check if it does.
- Staff go in as gross wages (`payroll`, regular or Minijob); employer social
  contributions are added on top (estimates: ~21% and ~31%, overridable).
- Reports in euros and German number format (`1.234,56 €`), or `"en"` style.
  Inputs accept `5,90`, `5.90`, `1.234,56` and `1,234.56`; an ambiguous `1.234`
  is refused, never guessed.

**Rules the US original did not know about**, written into the skills:
residence permits for non-EU founders, Gewerbeanmeldung, the ELSTER tax
questionnaire, TSE cash registers, Berufsgenossenschaft, food hygiene, Impressum,
GDPR and double opt-in, cookie consent for ad pixels, the Omnibus 30-day price
rule, the 14-day withdrawal right and 2-year warranty (never sold as a "bonus"),
EU health-claim rules, VerpackG and GPSR, DPMA / EUIPO / TMview trademark checks,
Handelsregister names, minimum wage and Minijob limits, and pointers to the
Your Europe portal for other EU countries.

**European buyers** on the panel: local names, gross incomes in euros, the city
in the brief, and objections like card vs cash, packaging waste and "is it bio?".

## Bugs fixed (from the audit of the original, commit fd9385b)

1. **"Profitable" with costs missing.** `numbers.json` with only a price used to
   compile to "Verdict: Profitable". Now any missing cost section
   (`variable`, `fixed_monthly` or `payroll`, `startup`) makes it **Incomplete**.
   Write `[]` for "none".
2. **Re-tests reused old answers.** `panel.py init` with a new pitch kept the old
   answers, so the "after" buy rate equalled the "before". Now every `init`
   archives the previous run to `founder/panel/runs/run-<k>/`, and the new
   `panel.py compare` shows before and after.
3. **"12,50" read as 1250.** The price tools now read decimal commas correctly
   and drop ambiguous numbers instead of guessing; `--decimal comma|dot` for CSVs.
   Semicolon CSVs (German Excel) work.
4. **`--quick` did nothing.** `panel.py init --quick` now deals 20 buyers, and
   the skill passes it through.

## Install

Copy the folders (commands are then `/founder-board` and so on):

```bash
cp -r skills/founder-* ~/.claude/skills/
```

Or project-local: copy them into your repo's `.claude/skills/`. The tools need
Python 3.8 or newer, standard library only, no network.

## How to use it

Run them in this order. Each one reads what the others wrote, in a `founder/`
folder in your project.

```
board -> competitors -> consumer -> pricing -> offer -> cfo -> marketing -> brand -> ops -> launch -> plan
```

The example in this repo is a matcha café at Rosenthaler Platz in Berlin, 5,90 €
a cup with 19% VAT. With the example numbers each cup leaves 4,96 € net and
3,57 € after its own costs, break-even is 111 cups a day, and the margin at the
planned 260 cups a day is 41%. These are example inputs, not research: replace
every one with real quotes.

`/founder-consumer --quick` on an idea you are only thinking about is the
cheapest first look (20 sub-agents instead of 100).

## The tools

```bash
python3 skills/founder-cfo/unit_economics.py founder/numbers.json --out founder/cfo.md
python3 skills/founder-consumer/panel.py init --customer founder/customer.json --pitch founder/pitch.md --quick
python3 skills/founder-consumer/panel.py compare
python3 skills/founder-pricing/van_westendorp.py founder/panel/answers --price 5,90
python3 skills/founder-plan/compile.py --dir founder --check
```

```bash
python3 -m unittest discover -s tests -v
```

## Fine print

**The board applies published frameworks. It is not those people.** The lenses
summarise ideas from *$100M Offers* (Alex Hormozi), *Zero to One* (Peter Thiel
with Blake Masters) and Walter Isaacson's *Steve Jobs*. Not affiliated with any
of them.

**The consumer panel is simulated buyers, not customers.** Language models lean
agreeable: read the buy rate as an upper bound and confirm with real people.
Never use panel answers as testimonials (in the EU that is also unlawful).

**Tax and legal rules here are pointers, not advice.** Rates, limits and permits
change and differ by country, Bundesland and city. The figures in the skills
(VAT handling, Kleinunternehmer limits, minimum wage, Minijob limit, employer
contribution estimates) were written in late 2026: check them against the
official source, and have a Steuerberater and, where needed, a lawyer confirm
before money moves.

## Contributors

- **Abdul Faiz** ([AbdulFaiz123](https://github.com/AbdulFaiz123)): the EU edition, idea and review.
- **Claude** (Anthropic, via [Claude Code](https://claude.com/claude-code)): the audit, the bug fixes, the EU and
  Germany adaptation and the tests.
- **Jake Schincariol** ([Jakeschincariol](https://github.com/Jakeschincariol)): the original
  [founder-skill](https://github.com/Jakeschincariol/founder-skill).

## License

MIT, like the original. See LICENSE.
