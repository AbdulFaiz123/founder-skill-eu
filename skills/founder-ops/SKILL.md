---
name: founder-ops
description: >-
  Your operations manager. Works out how the business actually runs on day one:
  suppliers and what they cost, who works when, the step-by-step routines for
  opening, serving or shipping and closing, the tools to run it, the licences and
  permits to check, and a risk register with what to do when each thing goes
  wrong. Feeds real costs back to the CFO. Use when the user says "how do I run
  this", "operations", "suppliers", "staffing", "SOPs", "what do I need to open",
  "permits", or "day one".
argument-hint: "[city or country]"
---

# founder-ops

A plan that works on paper fails at 7am on a Monday. This skill makes sure the
first day, week and month can actually be run, and that the CFO's numbers include
what running it really costs.

## Step 1: what the business has to do every day

From `founder/idea.md`, `founder/offer.md` and `founder/numbers.json`, write the
daily cycle as a list of steps from first thing to last (for a café: deliveries,
prep, open, serve, clean, cash up, order; for an online store: orders in, pick,
pack, ship, returns, support). Mark which steps a customer sees.

## Step 2: suppliers

For every input in the CFO's variable costs and every piece of equipment: two or
three real suppliers the user can contact, their public prices or how to get a
quote, minimum orders, lead times and payment terms. Link the sources. Where only
a quote will tell, say so and add it to the open questions. If a real price
differs from `founder/numbers.json`, update it and say the CFO should re-run.

## Step 3: people

Who does what, when: a weekly rota for the planned volume and for the slow first
month. The roles, the hours, and the wage assumption (from the user, or a public
source for the local minimum and typical pay, linked). Check every role against
the statutory minimum wage (Germany: 13,90 € an hour in 2026) and working-time
rules (Germany: Arbeitszeitgesetz, max. 10 hours a day, breaks, Sunday rules;
Minijobs at most 603 € a month in 2026). Put the staff in `founder/numbers.json`
under `payroll` as gross wages so the CFO adds employer contributions; flag the
real rates for the payroll office or Steuerberater.

## Step 4: routines (SOPs)

Short, numbered routines for the moments that make or break the business: opening,
the core service or fulfilment, handling a complaint, closing, and a weekly
reorder. Each fits on one page someone could follow on their first day.

## Step 5: tools

The smallest stack that runs it: payments, point of sale or store, scheduling,
bookkeeping, inventory. Real products with their published prices, and why each.
In Germany: a POS with a certified TSE (for example SumUp, orderbird, ready2order),
accounting that exports to DATEV for the Steuerberater (for example lexoffice,
sevDesk), a business account (Kontist, Qonto, Fyrst, or a Sparkasse). Prefer
tools that store data in the EU and offer a GDPR data processing agreement (AVV),
and list the AVVs to sign.

## Step 6: licences, permits and insurance

A checklist of what businesses of this type usually need in the user's city or
country, each with the official page to confirm it. Say plainly that rules
differ by place (in Germany, by Bundesland and city) and change, and the user
must confirm each with the authority or a professional. Not legal advice.

**Germany, the usual list** (pick what applies):

- **Residence permit first, for non-EU founders.** Many visas and residence
  titles (including job-seeker, student and EU Blue Card) do not allow
  self-employment without the Ausländerbehörde's permission. Check the
  Zusatzblatt for "Selbständige Tätigkeit gestattet" or ask before registering
  anything; self-employment residence titles are covered by section 21 AufenthG.
- **Legal form**: Einzelunternehmen (simplest, personal liability), GbR
  (partners), UG (haftungsbeschränkt) from 1 € capital or GmbH (25.000 €), both
  with notary and Handelsregister costs. Freelancers in a liberal profession
  (Freiberufler) do not register a trade.
- **Gewerbeanmeldung** at the city's Gewerbeamt (often online), which also signs
  you up with the IHK (or the Handwerkskammer for crafts; some crafts need a
  Meister to open).
- **Tax registration**: the Fragebogen zur steuerlichen Erfassung in ELSTER,
  within a month of starting, for the Steuernummer and a VAT ID if needed.
  Bookkeeping must follow GoBD, and a business must be able to receive
  e-invoices (since 2025; issuing them becomes mandatory in stages from 2027).
- **Cash registers**: a certified TSE, a receipt for every sale (Belegausgabe-
  pflicht) and registration of the till with the Finanzamt.
- **Staff**: a Betriebsnummer from the Bundesagentur für Arbeit, registration
  with each employee's Krankenkasse (or the Minijob-Zentrale), and with the
  Berufsgenossenschaft (statutory accident insurance, within a week of starting).
- **Food and drink**: registration with the Lebensmittelüberwachung, the
  Infektionsschutz-Belehrung (section 43 IfSG) for everyone handling food, a
  HACCP-based hygiene plan, allergen labelling, and a Gaststättenerlaubnis if
  alcohol is served (depends on the Land).
- **Selling goods online or shipping packages**: Impressum (section 5 DDG) and a
  privacy policy, Widerrufsbelehrung, terms (AGB), the "zahlungspflichtig
  bestellen" button, LUCID registration and a packaging scheme (VerpackG),
  stiftung ear for electronics (ElektroG), battery registration, and an EU
  responsible person and product safety file under the GPSR.
- **Premises**: the use permitted by the building permit (Nutzungsänderung if a
  shop becomes a café), signage and outdoor seating permits
  (Sondernutzungserlaubnis) from the city.
- **Insurance**: Betriebshaftpflicht at least; contents and business
  interruption for premises; the founder's own health insurance is mandatory.

**Other EU countries**: the Your Europe portal (europa.eu/youreurope) and the
country's Point of Single Contact list what to register; give those links and
the national equivalents.

## Step 7: risk register

The ten things most likely to go wrong (a supplier runs out, a key person is sick,
the card terminal fails, a bad review, a slow month), each with how likely, how
bad, and the plan.

## Output

`founder/ops.md`, plus updated `founder/numbers.json` if real costs changed. Next:
`/founder-launch`.
