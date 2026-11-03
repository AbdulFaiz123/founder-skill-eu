---
name: founder-launch
description: >-
  Your launch lead. Builds a dated, step-by-step launch plan: a cheap real-world
  test first (a waitlist, a pre-sale or a pop-up with a real price, so real buyers
  confirm what the simulated panel said), then the countdown to opening day with
  owners and deadlines, the launch-day run sheet, and the first 30 days of what to
  measure and what to change. Use when the user says "how do I launch", "launch
  plan", "when can I open", "launch checklist", "go live", or "soft open".
argument-hint: "[target launch date]"
---

# founder-launch

Launching is a project with a date. This skill turns everything else in the pack
into a dated plan, and starts with the cheapest way to find out if real people
will pay before the big money goes out.

## Step 1: test before you spend

Pick the cheapest real test that fits the business, and run it before signing the
big costs in `founder/numbers.json`:

| business | the test |
| --- | --- |
| physical shop or café | a pop-up, a market stall or a pre-order list with a price and a date |
| online product | a landing page with the price and a "pre-order" or "join the waitlist" button |
| service or agency | three paid pilot clients at the planned price |
| subscription | a founding-member offer, paid up front |

Write the success line before running it (for example: 50 pre-orders in two weeks
at 5,90 €), and compare the result with the panel's buy rate.

EU rules for the test itself:

- A waitlist or landing page collects personal data: privacy policy, Impressum,
  double opt-in for the email, and no tracking pixels before consent.
- A paid pre-sale online is a distance sale: the 14-day right of withdrawal,
  clear delivery dates, and the "zahlungspflichtig bestellen" button apply.
- A pop-up or market stall needs the city's permit for public space
  (Sondernutzungserlaubnis) or the market operator's place, a hygiene setup for
  food, and a registered trade (a short test can still need a Gewerbeanmeldung).
- Non-EU founders: make sure the residence permit allows the test before taking
  money. If real buyers fall
well short of the panel, trust the real buyers and go back to `/founder-offer` or
`/founder-pricing`.

## Step 2: the countdown

From today to launch day, with real dates (ask for the target date; default to the
earliest realistic one given lead times in `founder/ops.md`). Weekly blocks, each
task with an owner and a deadline:

- Legal and money: residence permit check, Gewerbeanmeldung, the ELSTER tax
  questionnaire, business bank account, TSE till, Berufsgenossenschaft and the
  permits from `founder/ops.md`. Lead times are real: the Steuernummer can take
  weeks, a Gaststättenerlaubnis or a Nutzungsänderung months.
- Build: fit-out or website, suppliers ordered by their lead times.
- Brand: sign, packaging, profiles from `founder/brand.md`.
- Marketing: the calendar in `founder/marketing.md` from launch minus 14 days.
- Team: hiring and training on the SOPs.
- A soft open or friends-and-family day before the public launch.

Mark the critical path: the tasks that move the launch date if they slip.

## Step 3: launch day

An hour-by-hour run sheet: who is where, what goes out on which channel, the
opening offer, what to do if something breaks (from the risk register).

## Step 4: the first 30 days

The weekly numbers to track (from the CFO: units a day against break-even; from
marketing: the channel numbers), the level that triggers a change, and a review on
days 7, 14 and 30 with the questions to answer.

## Output

`founder/launch.md` with the test, the countdown, the run sheet and the 30-day
review. Next: `/founder-plan` compiles everything into the business plan.
