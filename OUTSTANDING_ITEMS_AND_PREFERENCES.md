# Couchbase Sales Intelligence Engine — Outstanding Items & Working Preferences

## Resolved: Top 20 Accounts sheet

- ✅ Tier Distribution pie chart moved from beside the table to below it, into
  the whitespace next to the Top Opportunity Drivers list.
- ✅ Industry Opportunity Distribution bar chart was anchored on top of its
  own source data table (same row *and* same columns) — this was the actual
  cause of the "charts collide" complaint, not just a sizing issue. Moved
  below the pie chart with real vertical spacing.
- ✅ Both charts enlarged.
- ✅ "Recommended First Contact" column widened; header now wraps to two
  lines with a taller header row instead of being cut off.
- ✅ Column A widened (was serving double duty: short Rank numbers up top,
  and the wider "Top Opportunity Drivers" percentage bullets further down —
  the bullets were the ones getting clipped).
- ✅ "Why Couchbase" — root cause was `get_why_couchbase()` truncating to the
  first sentence, then capping that at 15 words with "...". This was already
  supposed to be reverted per earlier notes but was still live in code.
  Fixed to return the full `couchbase_point_of_view` text untouched, wrapped.
  Row heights already scaled dynamically from real text length, so no
  separate height fix was needed once the text itself stopped being cut.

## Resolved: Full Landscape sheet

- ✅ Avg COI (Actionable) "looks too low" — re-confirmed correct; not
  revisited further, no new evidence presented.
- ✅ Title bar didn't extend over the KPI row — root cause: title merge was
  `A1:G1` (7 cols) while the 5-KPI row spans `A:J` (10 cols, 5 KPIs × 2
  merged columns each). Widened to `A1:J1`.
- ✅ Once the title/KPI width was fixed, the actual data table underneath
  turned out to be narrower still (real columns only run A–G; H–J have
  widths defined but no data) — this made the title look misaligned again
  from the other side. Resolved by extending the table's visible box border
  out to column J with blank bordered filler cells, so title, KPI row, and
  table all read as one continuous width.
- ✅ Title text centered horizontally (was left-indented).
- ✅ Table boxed in with thin borders (previously had none) and enlarged —
  header row 22→26pt, data rows 20→24pt, columns widened.
- Conditional formatting colors (white→yellow→red) — not yet revisited;
  still worth softening per the original note if it comes up again.

## Resolved: Top 20 Accounts — title alignment

- ✅ Title text centered horizontally to match Full Landscape's treatment.

## Resolved: Call Briefs sheet

- ✅ Enlarged throughout — new `BRIEF_*` font constants (scoped separately
  from the shared `TITLE_FONT`/`LABEL_FONT`/`BODY_FONT` used by Top 20
  Accounts and Full Landscape, specifically so this change wouldn't resize
  those other sheets as a side effect). Title 17→19pt, labels/body 13→15pt,
  section headers 12→14pt, markers and pressure-bar font 11→13pt. Columns
  widened (A: 26→30, B: 95→105). Row-height math recalibrated for the larger
  font (chars-per-line divisor and points-per-line multiplier both adjusted)
  so wrapped paragraphs don't end up clipped despite the bigger text.

## Resolved: Sales Intelligence Platform tab (formerly "Top 20 Accounts")

- ✅ Renamed from "Top 20 Accounts" to "Sales Intelligence Platform" and set
  as the first/active tab.
- ✅ Real Couchbase brand banner (licensed asset, not generated/reconstructed
  - see `assets/couchbase_banner.png` and `LOGO_FILE` in the script) added as
  a proper splash row at the top, sized to preserve its real 4:1 ratio.
  Falls back gracefully (prints a warning, doesn't fail the build) if the
  asset file isn't present at build time.
- ✅ Project title + sheet subtitle added below the banner; table shifted
  down accordingly (everything below is computed relative to
  `table_header_row`, so this didn't require separate row-math fixes).
- ✅ Why Couchbase column widened 95→105; row-height chars-per-line math
  recalibrated to match (90→100) so long entries don't end up
  under-estimated for height.
- ✅ Header font bumped 14→16pt to match Overview, on both this sheet and
  Full Landscape's industry table header (same shared `HEADER_FONT`
  constant covers both - no side effects elsewhere, confirmed only these
  two usages exist). Row heights bumped to match (28pt / 40pt).

## Resolved: conditional formatting colors (closes an item open since the
## very start of this project)

- ✅ Original ask was "white→yellow→red needs to be lighter/softer" for
  Full Landscape - flagged in the first working session, never fixed until
  now. Softened on **all three** color-scale rules that shared the old
  palette: Full Landscape's Avg COI column, Full Landscape's
  Actionable%/Tier1/Tier2/Tier3 columns, and the SIP/Top 20 sheet's COI
  column. New palette: `FFFFFF` (white) → `FFF3B0` (pale yellow) →
  `F2A9A5` (soft muted coral), replacing the old `FFFFFF` → `FFEB84`
  (saturated yellow) → `C00000` (dark red). Confirmed liked as-is.

## Resolved: Overview sheet

- ✅ Account Name column widened 28→34 based on real data (95th percentile
  36 chars, median 17 - a handful of ~90-char government/university names
  are genuine long-tail outliers, not the norm). Wrap-text enabled with
  real-length-based dynamic row height (same principle used elsewhere in
  this script) so the rare long name wraps instead of truncating, capped
  at 70pt so an outlier doesn't blow out the row.
- ✅ Visible border added around Account Name.
- ✅ All Overview columns widened proportionally, and font sizes bumped
  (header 14→16pt, body/link 13/14→15pt) - via new Overview-specific font
  constants (`OVERVIEW_HEADER_FONT`, `OVERVIEW_BODY_FONT`,
  `OVERVIEW_LINK_FONT`), scoped separately so this didn't resize Full
  Landscape or SIP/Top 20 as a side effect.



- **Overview sheet: Account Name column width and border.** Original ask —
  widen Account Name, add a visible box/border for better visibility. Not
  yet revisited since these notes were first written.
- **Overview sheet: confidence/verification tag — parked, not resolved.**
  Overview currently shows no confidence indicator at all, unlike Call Briefs
  (which has "Web-Verified" / "NOT COMPANY-VERIFIED" markers, driven by
  `llm_used_web_search` and `llm_narrative_caveated`). Note this is genuinely
  a 3-state signal, not 2: caveated (weakest), web-verified, or neither flag
  set (recognized from model training knowledge, no live search - Call
  Briefs shows no badge at all for this quiet middle state).
  **Filtering by confidence is not possible anywhere in the workbook today**
  — Call Briefs is a vertical one-block-per-account layout with no
  `auto_filter`, and Overview (which does have `auto_filter` and is the
  natural home for this) has no confidence column yet. Discussed on
  2026-07-29; parked without a decision on format (text column vs.
  color-coded cell) pending clarity on the actual use case — filter/sort
  across the full list vs. a quick visual scan — since those point toward
  different designs.
- **Full Landscape: second COI column.** Discussed and decided **not to build**.
  Proposal was a second "Avg COI (Tier 1–2 only)" column alongside "Avg COI
  (Actionable)," to separate "how strong are our best accounts" from "how big
  is the broader pipeline." Rejected on: several industries have only a
  handful of Tier 1+2 accounts (e.g. 5 in Technology/SaaS), so an average
  over that few accounts is dominated by whichever single account happens to
  be highest or lowest — trading a misleadingly *diluted* number for a
  misleadingly *noisy* one, in exactly the industries that prompted the
  original complaint. Showing the count alongside it was considered but
  judged not worth the added column/complexity for what it would actually
  fix. If this resurfaces, the small-n problem is the thing to re-litigate,
  not the diluted-average complaint that started it.

## Already confirmed correct (don't re-relitigate without new evidence)

- Actionable % column values are mathematically verified correct against
  real per-industry tier counts.
- The "Web-Verified" badge on Call Briefs is present and correct for 3,577
  of 3,579 accounts (99.9%).
- Insurance's Tier 3 count (46 accounts) is a real, correct result of two
  legitimate mechanisms compounding — not a bug.

## Working style — what actually works now

- **Discuss before building** when a request is genuinely ambiguous or
  affects a real design decision (e.g. narrowing the KPI row vs. widening
  the table — two valid ways to close the same gap). Don't ask when the
  target state is already unambiguous or previously confirmed.
- **Fix in the script, not the output file.** A fix living only in a
  delivered `.xlsx` disappears the next time `build_ae_call_list.py` runs.
  Every fix in this log was made in the script and verified by actually
  re-running it against the real 9,758-account source, not just inspecting
  the code.
- **Deployment routine, every drop:** clear the old file from Downloads
  *before* downloading the new one (browsers create silent numbered
  duplicates like `build_ae_call_list (1).py` otherwise, which is exactly
  how a stale version got re-run twice in this project). Verify file size
  after download, before moving anything. Compile-check before running.
  Confirm the output's timestamp is fresh, not a leftover. Full checklist
  is in README.md.
- **Verify claims against real output before stating them as fact** —
  especially "is this data still there" or "did this actually get applied."
  This bit us twice: once when a script fix was made but the old script was
  still the one sitting in the project directory, and once when an old
  output file was uploaded for review instead of a fresh one.
- **Prefer lighter, softer color palettes** for fills and conditional
  formatting generally (confirmed 2026-07-29 on the COI color scales -
  pale yellow/soft coral over saturated yellow/dark red). Default toward
  this on any future fill-color or conditional-formatting work rather than
  waiting to be asked each time.
