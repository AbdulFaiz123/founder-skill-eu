---
name: founder-offer
description: >-
  Builds an offer too good to refuse. Lists every problem the buyer hits on the way
  to the result they want, turns each into a solution, trims to what is cheap to
  deliver and valuable to the buyer, and stacks it with honest bonuses, a guarantee
  the CFO can afford, real urgency and a clear name. Scores it on the value
  equation (outcome, likelihood, time, effort) and re-tests it on a quick buyer
  panel. Use when the user says "make my offer better", "why won't people buy",
  "what should I include", "guarantee", "bonuses", "grand slam offer", or after the
  panel shows people passing.
argument-hint: "[what you sell]"
---

# founder-offer

Most businesses sell a product. Good ones sell an offer: the product plus
everything that makes buying it an easy yes. This skill builds that, using the
Offers lens in `../founder-board/lenses.md` as the method (a summary of the
framework in Alex Hormozi's *$100M Offers*; never present it as his words).

## Step 1: read what is already known

- `founder/idea.md` and `founder/pitch.md`: what is sold today.
- `founder/panel/results.md`: why buyers pass, in their words. This is the raw
  material: every top objection should be answered by something in the offer.
- `founder/numbers.json`: what each extra costs, so the stack stays profitable.
- `founder/board.md`: the board's conditions.

## Step 2: the problem list

Write every obstacle between the buyer and the result they want, in the buyer's
words: before buying (doubt, price, effort to switch), during (waiting, learning,
inconvenience), after (does it last, what if it fails). Aim for 15 to 30. Pull
from the panel objections and the competitor complaints first.

## Step 3: solutions, trimmed and stacked

Turn each problem into a solution (a feature, a service, a guarantee, a format).
Score each on value to the buyer (1 to 5) and cost to deliver (1 to 5, from the
CFO's numbers). Keep high value, low cost. Stack what is left into:

- **The core**: the thing itself, described by the outcome, not the ingredients.
- **Bonuses**: two or three, each killing one specific objection.
- **The guarantee**: what happens if it does not deliver. Model what it costs at a
  realistic claim rate with the CFO's tool before promising it.
- **Urgency and scarcity**: only if they are true (a launch week, a limited first
  batch). Never fake a countdown or a "only 3 left".
- **The name**: a clear, specific name for the offer, not the company.

## Step 4: score it

On the value equation, before and after, 1 to 10 each: dream outcome, perceived
likelihood of getting it, time to the result, effort and sacrifice. Say which
element of the stack moves which score.

## Step 5: re-test it

Write the new offer into `founder/pitch.md` (keep the old one as
`founder/pitch-v1.md`). Re-run the panel with the SAME size and seed as the
"before" run (both are in `founder/panel/panel.json`), so the only thing that
changes is the offer:

```bash
python3 "${CLAUDE_SKILL_DIR}/../founder-consumer/panel.py" init --customer founder/customer.json --pitch founder/pitch.md --n <same n> --seed <same seed>
```

`init` moves the old run to `founder/panel/runs/` and deals the same buyers again
with no answers, so every buyer reads the new pitch. Run the waves as in
`/founder-consumer`, then `tally`, then:

```bash
python3 "${CLAUDE_SKILL_DIR}/../founder-consumer/panel.py" compare
```

which writes `founder/panel/compare.md`: the buy rate before and after and each
reason to pass, before and after. If nothing moved, say so: the problem may be
the market or the price, not the offer.

## Rules

- Every promise must be deliverable and affordable; check costs with the CFO.
- No fake reviews, testimonials, scarcity, discounts or "as seen on".
- EU consumer law (the Unfair Commercial Practices Directive; Germany: UWG):
  - Never sell a right the buyer already has as a bonus. Online and distance
    sales already carry a 14-day right of withdrawal (Widerrufsrecht) and goods
    a 2-year legal warranty (Gewährleistung). "14 days to return it" is not a
    guarantee you are giving; a 30-day no-questions refund or a 3-year promise
    can be.
  - A voluntary guarantee (Garantie) must state its terms, who gives it, and
    that it does not limit the legal warranty.
  - Fake scarcity, fake countdowns and fake reviews are blacklisted outright.
  - Health claims on food are limited to the EU's approved list (Regulation
    1924/2006): "rich in antioxidants" or "boosts focus" need an approved claim.
  Not legal advice; a lawyer or the IHK checks claims and guarantee wording.

## Output

`founder/offer.md` (problem list, the stack, costs, the value-equation scores, the
re-test result) and the updated `founder/pitch.md`. Next: `/founder-cfo` to re-run
the numbers with the stack, then `/founder-marketing`.
