---
name: founder-cfo
description: >-
  Your CFO. Builds the unit economics of a business before money is spent: what
  one unit earns after its direct costs, the real profit margin at the planned
  volume, the break-even point in units a day, year 1 month by month, the cash
  needed before it pays for itself, how long the startup spend takes to earn back,
  and what happens if the price drops, sales come in low or costs rise. Every
  number traces to an input the user can check. Use when the user says "find the
  profit margins", "do the numbers", "is this profitable", "break-even", "unit
  economics", "how much do I need to start", or "run the CFO".
argument-hint: "[path to numbers.json]"
---

# founder-cfo

The person who asks "and what does that cost?" Margins decide whether a good idea
is a business. This skill finds them, with every number traceable to an input.

EU edition: prices are in euros (or the local currency) and include VAT the way
European customers see them, staff are entered by gross wage with employer social
contributions added on top, and German Kleinunternehmer status is checked.

Tool in this folder:

```bash
python3 "${CLAUDE_SKILL_DIR}/unit_economics.py" founder/numbers.json --out founder/cfo.md
```

## Step 1: gather the inputs

Write `founder/numbers.json` (shape: `example.json` in this folder, a walk-in
matcha café in Berlin). It needs:

| field | what goes in it |
| --- | --- |
| `unit` | what one sale is: a cup, an order, a client-month, a seat |
| `currency`, `number_format` | `"EUR"` and `"de"` (1.234,56 €) by default; `"en"` for €1,234.56 |
| `price` | the price per unit as the customer sees it |
| `price_includes_vat` | `true` for consumer prices (in the EU they must be shown with VAT), `false` for B2B net prices |
| `vat_rate` | the rate for THIS product, e.g. Germany 0.19 standard or 0.07 reduced; ask if unsure (see below) |
| `kleinunternehmer` | `true` only if the user will use the German small-business VAT exemption (section 19 UStG) |
| `variable` | the cost of ONE unit, net of VAT you can reclaim: ingredients, packaging, shipping, card fees, commissions |
| `payroll` | staff: `{label, gross_monthly, kind}` with kind `regular` or `minijob`; the tool adds employer costs |
| `fixed_monthly` | everything else you pay monthly: rent and Nebenkosten, Steuerberater, insurance, Berufsgenossenschaft, software |
| `startup` | one-off spend before opening: deposit (Kaution, often 3 months' cold rent), fit-out, equipment, first inventory, launch ads |
| `days_per_month` | 30 if you open every day, about 26 if you close on Sundays (most shops in Germany must) |
| `plan_per_day` | the volume once it is up and running |
| `ramp_per_day` | 12 numbers: realistic volume in each month of year 1 |
| `capacity_per_day` | the most you can physically sell in a day, if there is a limit |

Every cost section must be present; write `[]` if there really is none. A missing
section makes the plan **Incomplete**, never "Profitable". Numbers can be JSON
numbers or strings like `"5,90"`; never write an ambiguous `"1.234"` (the tool
refuses it).

**VAT is where EU plans go wrong.** The tool splits the shelf price into net price
and VAT, because VAT is the tax office's money, not revenue. Rates differ by
country and by product (in Germany, for example, food and drinks are treated
differently, and takeaway and eat-in rules have changed over the years). Check
the rate for the exact product on the national tax authority's site or with a
Steuerberater, and write the source in `founder/cfo-sources.md`. Selling online
to consumers in other EU countries above 10.000 € a year means their VAT rates
and the OSS scheme: flag it.

**Kleinunternehmer (Germany).** Since 2025 a business can skip charging VAT if
last year's turnover was at most 25.000 € and this year's stays at most
100.000 €; in the founding year the 25.000 € line applies. The tool flags the
month the plan crosses it. It is a trade-off (simpler, cheaper for consumers, but
no input VAT back on the fit-out and equipment), so present it as a question for
the Steuerberater, not a recommendation.

**Staff.** Put wages in `payroll` as gross. Employer social contributions are
added (defaults: about 21% for regular staff, about 31% for a Minijob in
Germany; override with `payroll_oncost`). Check every wage is at or above the
statutory minimum wage of the country (Germany: Mindestlohn, 13,90 € an hour in
2026, 14,60 € from 2027) for the hours in the rota, and that a Minijob stays under
its monthly limit (603 € in 2026). For other countries, ask for the local rate
and say it is an estimate.

Where the numbers come from, in this order:

1. The user's own quotes, invoices, leases and supplier price lists.
2. Public prices the user can check (a supplier's price list, a listing on
   ImmoScout24 or a commercial property site, SumUp's or the bank's published
   card fees, the Minijob-Zentrale's rates). Write the source next to the number in
   `founder/cfo-sources.md`.
3. Your estimate, clearly marked as an estimate, with the reasoning. Never present
   an estimate as a fact.

Ask the user for anything only they know (rent quoted, wages they will pay). Use the
price from `founder/pricing.md` or `founder/pitch.md` if those exist.

**The ramp is where plans lie.** Month 1 is almost never the plan volume. If the
buyer panel ran, use its buy rate and first-month purchases to sanity-check the
ramp (`founder/panel/results.md`), and say how you did it.

## Step 2: run it

```bash
python3 "${CLAUDE_SKILL_DIR}/unit_economics.py" founder/numbers.json --out founder/cfo.md
```

It writes: the per-unit table (shelf price, VAT, net price, unit costs) and the contribution (what each sale leaves after
its own costs), fixed costs, the break-even in units a day, the profit margin at
the plan volume, year 1 month by month, the year 1 operating profit and the result
after the startup spend, the cash needed before it pays for itself, the month the
startup money is earned back, and a what-if table (price -10%, volume -20%, unit
costs +15%). It flags a price below variable cost, a break-even above capacity, a
losing year 1, a payback beyond 12 months, missing cost sections and a
Kleinunternehmer plan that outgrows the limit. It also shows the VAT collected in
year 1, money to set aside for the Umsatzsteuer-Voranmeldung.

What-ifs without editing the file:

```bash
python3 "${CLAUDE_SKILL_DIR}/unit_economics.py" founder/numbers.json --price 6,50
python3 "${CLAUDE_SKILL_DIR}/unit_economics.py" founder/numbers.json --volume 0.8
```

## Step 3: the CFO's note

Add a short section at the top of `founder/cfo.md`, in plain words:

- **The margin**: the profit margin at plan, and the contribution per unit.
- **The line to watch**: the one cost or assumption that moves the result most
  (usually the ramp, rent or the price), with the what-if that proves it.
- **Cash**: how much money the founder needs before it pays for itself.
- **Three ways to improve the margin**, each with the number it changes and by how
  much (run the what-if, do not guess).
- Whether the board's conditions about money (`founder/board.md`) are met.

## Rules

- Every number in your note comes from the tool's output or an input you can name.
- Revenue in the report is net of VAT. Profit is before income tax and trade tax
  (Gewerbesteuer in Germany, with a 24.500 € allowance for sole traders and
  partnerships; corporations such as a UG or GmbH pay corporate tax instead).
- The legal form changes the numbers: a sole trader's own pay is not a cost (it
  comes out of profit, and they pay their own health insurance, often 400 to
  1.000 € a month in Germany); a GmbH or UG managing director's salary is. Ask
  which form, and put the founder's own health insurance in `fixed_monthly` if
  the business has to cover it.
- Not financial, tax or legal advice. Say once that a Steuerberater should check
  the structure, payroll costs and tax before money moves.

## Output

`founder/numbers.json`, `founder/cfo.md`, `founder/cfo-sources.md`. Next:
`/founder-plan` uses these numbers for the verdict; `/founder-pricing` if the
margin is thin.
