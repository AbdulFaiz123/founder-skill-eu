---
name: founder-brand
description: >-
  Your brand designer. Names the business (with the trademark, domain and handle
  checks to run before falling in love with a name), writes the voice, a one-line
  promise and a tagline, and briefs the look: colours, type, logo and the first
  things a customer sees, so they match the positioning the marketing director
  chose. Use when the user says "name my business", "brand this", "logo", "brand
  identity", "what should it look like", "tagline", or "brand voice".
argument-hint: "[name ideas, if any]"
---

# founder-brand

A brand is the promise a customer remembers. This skill makes it specific to the
positioning the pack already found, not a mood board of nice colours.

## Step 1: read the brief

`founder/idea.md`, `founder/marketing.md` (the positioning line and the first
audience), `founder/competitors.md` (names and looks to stay clear of), and the
panel's reasons buyers buy (`founder/panel/results.md`). If the positioning is
missing, ask for it or run `/founder-marketing` first.

## Step 2: name candidates

Ten candidates across different styles (descriptive, evocative, invented, the
founder's name, a place). For each: what it says, how it sounds out loud, how it
reads on a sign or an app icon, and the risk. Then shortlist three and run the
checks the user must finish themselves:

- **Trademark**: search TMview (tmdn.org/tmview, every EU national office and
  the EUIPO at once), then DPMAregister for Germany and EUIPO eSearch for EU
  marks, for the name in the same Nice classes of goods and services (UKIPO for
  the UK, Swissreg for Switzerland). Give the search links and the classes to
  check. Mention cost: a German mark starts around 290 € (DPMA, 3 classes), an
  EU mark around 850 € (EUIPO, 1 class); check the current fees.
- **Company name**: if it will be a registered company (UG, GmbH, e.K.), search
  the Handelsregister (handelsregister.de) and Northdata for the same or a
  similar name in the region. A sole trader that is not registered must trade
  under their own first and last name on letters and invoices, with the brand
  as an addition.
- **Domain**: whether the .de (DENIC), .eu (EURid), the local ccTLD and the .com
  are free (check, do not assume); good alternatives if not.
- **Language**: how the name sounds and what it means in German and the main
  languages of the market (and that it is not a rude word in any of them).
- **Handles**: Instagram, TikTok, X, YouTube.
- **Confusion**: no name close to a competitor in `founder/competitors.md`.

Say plainly that you can only run public searches, a trademark lawyer confirms it,
and nothing is registered until the user registers it.

## Step 3: voice and promise

- The one-line promise (what the customer can count on, every time).
- A tagline, three options.
- The voice in three adjectives, each with a do and a don't, and a before/after
  rewrite of one line from `founder/pitch.md`.

## Step 4: the look, as a brief

- **Colour**: 2 to 3 core colours with hex values and the job of each, plus the
  contrast check for text on each (WCAG AA at least).
- **Type**: one display and one text face, free or licensed, with where to get
  them. No font the user does not have a licence for.
- **Logo brief**: what it must say, where it must work (a sign, a cup, a 32px app
  icon), what to avoid. Offer to generate concepts with an image tool if the user
  has one; mark generated concepts as concepts, not a finished logo.
- **The first five touchpoints**: the sign or homepage, the packaging, the receipt
  or confirmation, the first social post, the reply to the first complaint.

## Rules

- Never copy a competitor's name, logo, colours or tagline.
- No fonts, images or icons the user has no right to use.
- Not legal advice on trademarks.

## Output

`founder/brand.md`. Next: `/founder-ops` and `/founder-launch`.
