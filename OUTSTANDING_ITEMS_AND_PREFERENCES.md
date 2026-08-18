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

## Tried and reverted, same day: Overview confidence/verification column

- Built a "Confidence" column (G) on Overview on 2026-07-29, reusing the
  same three-state logic already on Call Briefs, filterable via the
  existing `auto_filter`. **Reverted the same day** once real data showed
  why it wasn't useful: 3,567 of 3,579 accounts (99.7%) are Web-Verified,
  since the pipeline attempts web grounding for nearly every qualifying
  account by design. A filter that doesn't meaningfully narrow the list
  isn't a real filter - it was just visual reassurance dressed up as a
  filtering feature. If this is revisited, the useful version would only
  surface the rare exception (the 11 Not Company-Verified accounts), not
  all three states with equal visual weight - see
  `caveat_marker`/`web_search_marker` in the Call Briefs section for the
  equivalent logic already working correctly on that sheet.

## Resolved: SIP/Top 20 sheet font consistency and alignment

- ✅ Body font (Rank, Account, COI, Workload, Why Couchbase, Recommended
  First Contact, plus the Top Opportunity Drivers list below the table)
  bumped 13→16pt to match the header, via new SIP-scoped font constants
  (`SIP_BODY_FONT`, `SIP_LINK_FONT`) so Full Landscape's own data-row font
  (still 13pt, untouched) wasn't affected as a side effect.
- ✅ Why Couchbase row-height chars-per-line recalibrated again (100→80) to
  account for the larger font on top of the earlier width change, so long
  entries don't end up under-estimated for height.
- ✅ COI column left-justified to match the other (text) columns - it was
  defaulting to Excel's general alignment, which right-aligns numbers,
  while every text column defaults left - hence the visual inconsistency.
- ✅ Rank column center-justified (a deliberate choice over left, since a
  short 1-20 index column reads cleaner centered and visually distinguishes
  "this is an index" from "this is data").

## Resolved: Full Landscape "Total Accounts" header clipping

- ✅ Column B widened 17→21 - the header text was fine at the old 14pt
  font but started clipping once the header font was bumped to 16pt in an
  earlier fix; the two changes needed to land together.

## Resolved: SIP subtitle, Overview borders, Full Landscape KPI/table
## alignment, and a real data-integrity bug

- ✅ SIP sheet subtitle ("🎯 Top 20 Accounts to Call") was missed in the
  earlier header-font unification pass - bumped 14→16 to match everything
  else on that sheet.
- ✅ Fixed an off-by-one in Overview (`range(2, 6)` should have been
  `range(2, 7)`) that meant Account Owner (column 6) never got the same
  border or center alignment as the other columns - a pre-existing bug,
  not something introduced today, just found while widening border
  coverage to all columns per request.
- ✅ Full Landscape KPI labels (Total Accounts Scored, Actionable %, etc.)
  were small gray text with no fill - visually weak next to everything
  else on the sheet that had been bumped to 16pt/bold this session.
  Matched to the industry table's own header treatment instead (bold
  white 16pt text on the same blue fill) - chosen specifically for
  reliable contrast regardless of color vision, not a color-based cue.
- ✅ Full Landscape table box: went through several iterations same day
  before landing correctly. The table header row's blue fill/border had
  been extended out to column J to match the title/KPI width above
  (an earlier "Option B" fix), with blank bordered filler cells in H:J
  for the data rows below it. Removing those filler borders (looked like
  an empty grid of boxes) then made the header's H:J extension look
  disconnected from anything below it. Resolved by reverting the table
  header itself back to stop at column G (its real width) - confirmed
  fine for the page title and KPI row above to stay wider at A:J on
  their own; the actual problem was specifically a table header implying
  a table below it that didn't exist past G.
- ✅ **Real bug, not a false alarm**: the Actionable % KPI box (the big
  number under the "Actionable %" label, not the industry table's own
  Actionable % column - two different things with the same name) was
  built as a literal Python string (`f"{actionable_pct}%"`, e.g. the text
  `"36.7%"`) rather than a real number. This is exactly what triggers
  Excel's genuine "Number Stored as Text" warning - confirmed via
  screenshot showing the actual warning triangle and tooltip. Fixed by
  storing the value as a true fraction (`actionable_pct_fraction`) with
  Excel's native `"0.0%"` number format, so it displays identically but
  is a real, computable number. Worth remembering: don't assume a visual
  complaint is styling-only before checking the underlying value/type -
  this one turned out to be a genuine data-integrity bug hiding behind
  what looked like a cosmetic complaint.



- Actionable % column values are mathematically verified correct against
  real per-industry tier counts.
- The "Web-Verified" badge on Call Briefs is present and correct for 3,577
  of 3,579 accounts (99.9%).
- Insurance's Tier 3 count (46 accounts) is a real, correct result of two
  legitimate mechanisms compounding — not a bug.

## Real-cost lesson: rerun_qualified_with_search.py is now redundant for
## brand-new runs (confirmed 2026-07-29, Enterprise_East run)

- `rerun_qualified_with_search.py` was built to add web search grounding to
  accounts that were validated **before Serper existed** in this codebase.
  For any brand-new account list processed **now**, `main.py`'s own first
  LLM pass already performs web search grounding automatically, since
  `SERPER_API_KEY` is configured in the environment permanently, not just
  for that one historical rerun.
- Confirmed directly on the Enterprise_East run (485 qualified accounts):
  running `rerun_qualified_with_search.py` afterward produced a
  byte-identical result to `main.py`'s own output - same token counts to
  the exact penny, same `llm_used_web_search` distribution (459 true / 26
  false, matching the README's documented ~6% no-location skip rate),
  confirmed by comparing `enterprise_east_Scored.xlsx` (before) against
  `enterprise_east_Scored_FINAL.xlsx` (after) directly. No new work was
  done - the "reset to needs processing" step had nothing meaningful to
  reset, since these accounts were never un-grounded in the first place.
- **Real cost of this mistake**: ~$1.42 spent re-validating already-correct
  data. Not data corruption, not lost work - just money that didn't need
  to be spent.
- **Going forward**: for any brand-new account list, skip
  `rerun_qualified_with_search.py` entirely - go straight from `main.py`
  to `build_ae_call_list.py`. Only use the rerun script if genuinely
  reprocessing a batch known to predate Serper's introduction. Warning
  added directly to the script's own docstring so this is visible at the
  point someone would actually consider running it, not just documented
  here.

## Universal Serper grounding project (2026-07-29/30) - major capability
## addition, three rounds of real bug-finding, real spend

**The problem this solved**: an account's entire fate in this pipeline - Tier
1 vs. buried in Tier 4, LLM-eligible or not - was decided entirely by whether
its NAME happened to match a hardcoded keyword/pattern list. A genuinely
strong prospect with an unrecognizable name got zero deterministic signal at
all (`workload_profile` empty, `database_intensity` 0), landing in Tier 4 by
default - not because it was a weak prospect, but because the pipeline had
no information about it whatsoever.

**What was built:**
- `serper_enrichment_pass.py` - new standalone script, runs a real Serper.dev
  search for EVERY account (not just name-matched ones), caches raw
  snippets in `output/serper_search_cache.xlsx` keyed by Account Name.
  Per-row checkpointed (every 100), fully resumable - re-running against
  the same account list costs nothing for already-cached accounts, only
  the delta gets searched. Verified 3 ways in a sandbox before running for
  real: fresh run searches everyone, immediate re-run costs nothing, adding
  new accounts to the list only searches the new ones.
- `main.py` / `precursor_review.py` both patched identically - merge the
  cached `search_snippets` into the accounts DataFrame as
  `web_search_snippets`, right after load, before any classification runs.
  Gracefully degrades to an empty column if the cache doesn't exist yet.
  `precursor_review.py` needed the SAME patch as `main.py` since its whole
  purpose is previewing real impact before spending anything - without the
  matching patch it would have given a misleading "nothing changed"
  reading.
- `modules/industry_classifier.py` and `modules/company_intelligence.py`
  restructured: existing name-only matching completely unchanged (verified
  via explicit precedence tests - a name match is NEVER overridden by
  snippet content), NEW fallback only tried when name-alone finds nothing.
  Real known-company/business-pattern identity matching (Pass 1/2) stays
  untouched - only business-pattern KEYWORD matching (Pass 3) gets the
  fallback, since identity matching on a snippet (which can mention other
  companies in passing) was never a safe idea.

**Real, measured impact** (confirmed via `precursor_review.py`, zero cost):
LLM candidates went 485 (original, name-only) -> 2,327 (universal
grounding, before any cleanup) -> 2,038 -> 2,022 -> 2,012 (three rounds of
false-positive fixing). Net effect: roughly 4x more accounts now get real
consideration than before grounding existed, at a real but modest
~$3.89 estimated LLM cost for the genuinely new candidates. Tier 4 dropped
from 6,216 to ~4,684 - about 1,850 accounts recovered from "no signal at
all" into a real tier.

**Real bugs found via stratified audits of the newly-qualified population,
fixed and verified before spending real money on them:**
- `care` colliding with `career`/`careers` (near-universal company-profile
  boilerplate) - the single biggest false-positive source, explained ~289
  of the ~2,327 candidates on its own.
- `media@` colliding with press-contact email addresses.
- `cardiac`/`piccard`, `contextmedia`, `directed energy` - narrower keyword
  substring collisions, same class as pre-existing exclusions (card/media/
  energy/api), found via direct spot-check of real cached snippets.
- `power` needed a co-occurrence rule, not just an exclusion list - generic
  marketing language ("AI-powered", "powering healthcare data exchange")
  outnumbered genuine utility signal ~8x in real data. Now requires a real
  utility-specific term (electric/grid/utility/etc.) to co-occur.
- Institution-type mismatches (a law firm mentioning "health care" as its
  practice area, a municipal government, care-delivery nonprofits) -
  ported and extended `NON_FIT_INSTITUTION_KEYWORDS` from
  `sales_intelligence_pipeline.py`'s classification-prepass guard into the
  main matching path too.
- Nonprofit/charity signals now explicitly ROUTE to a real "Non-Profit /
  Charity" category instead of collapsing into blank "Unknown" - a rep can
  now tell "we found nothing" apart from "we found a nonprofit and
  correctly deprioritized it". Confirmed via real data: 190 accounts now
  carry this label, though ~180 of those were already correctly excluded
  under the round-2 fixes (a labeling/data-quality win, not a new cost
  reduction) - only ~10 were genuinely NEW exclusions this round. Verified
  this distinction directly rather than assume it: all 190 show
  `gate_decision == SKIP` and blank `workload_profile`, confirming none of
  them were ever going to reach the LLM regardless of the label.
- `health & wellness` / `medical, dental` - generic corporate benefits-page
  boilerplate, same danger class as `careers`.

**A real regression caught and reverted before shipping** (not after): an
early version of the institution-exclusion fix applied
`PROVIDER_EXCLUDE_KEYWORDS` to web-search snippet text broadly, which broke
a genuine match (EqualizeRCM Services, whose snippet legitimately says
"community health providers, hospitals" - its CLIENTS, not itself). Found
via the standard test suite before it ever reached a real account.

**A real duplicate-dict-key bug caught and fixed**: an edit accidentally
created two `"energy"` keys in the same dict literal - Python silently lets
the later one win, which would have discarded the `directed energy`
exclusion entirely with no error. Caught via a direct `grep -c` check
before shipping, not assumed fixed.

**Known, deliberately NOT fixed - documented directly in
`company_intelligence.py`'s own comments, not just here:**
- **"Vendor serves an industry" mismatch** (general case) - a company that
  SELLS TO an industry (GE Smallworld selling GIS software to utilities,
  ParkOps serving retail/hospitality clients, Affinity Solutions serving
  insurance companies) gets tagged as if it WERE that industry. A narrow,
  evidenced fix exists for the Utilities-specific instance (a
  third-person-possessive phrasing check: "a utility's electric, gas,
  water networks"), but the same GE Smallworld sentence also lists
  "telecom networks", which still incorrectly matches the separate Telecom
  pattern - confirmed this is genuinely the same problem resurfacing
  through a different pattern, not a new bug. Chasing this pattern-by-
  pattern has real diminishing returns; a general rule risks blocking
  genuine matches (EqualizeRCM genuinely says "community health
  providers" and must keep matching Healthcare). Not generalized until
  more real examples are gathered.
- **`care` as a bare keyword, structurally** - beyond the `careers`
  fix, real data keeps surfacing new "___care" compounds across unrelated
  industries (Massey Services/pest control matched via "lawn care",
  Cambridge Air Solutions/HVAC matched via "Client Care"). This deserves
  the same co-occurrence treatment `power` got (require a real healthcare-
  specific term to co-occur), not more one-off exclusions - identified,
  not yet built.
- **Exact-phrasing gaps in the institution/nonprofit exclusion lists** -
  "Goodwill Industries" (a well-known specific brand), "human-rights
  organization" (Heartland Alliance), reversed county-name phrasing
  ("Hamilton County" vs. the existing "county of" pattern), and
  "professional services firm"/"Global Consulting" (Huron Consulting Group
  vs. the existing "consulting firm" exact phrase) - same lesson as
  Kaufman Hall earlier: these lists need real phrasing variants, not just
  the concept once. Identified, not yet built.
- **Ambiguous-name search collisions** (Zapata AI/Quantum vs. an unrelated
  real estate developer sharing the surname; "Venus" the account vs. an
  unrelated auto-transport company in the town of Venus, FL) - genuine
  search-content ambiguity for common names, not a keyword-matching bug.
  No exclusion list fixes this; accepted as a residual risk of using
  web-search grounding at all.

**Infrastructure fix alongside this work**: `SERPER_API_KEY` had no
persistence mechanism at all (confirmed: caused two separate silent
all-`None` search failures this session, once costing a real, if small,
redundant spend). Added `python-dotenv` + a real `.env` file, wired
`load_dotenv()` into every script that needs it, verified with a genuine
fresh-shell test (`env -u SERPER_API_KEY python3 -c "..."`) that it works
without any variable manually exported. `.env` added to `.gitignore`
BEFORE the file was ever created, not after - same discipline as the
`Closed Won` lesson. Also fixed a separate, real gap: `requests` was used
directly by `web_search_client.py` but never declared in
`requirements.txt` - would have caused `ModuleNotFoundError` on a
genuinely fresh venv.

## The LLM-stage grounding bug - a real, more serious finding than the
## classification false-positives above (2026-07-30/31)

**Discovered while reviewing Tier 2 accounts for web-verification status**:
a real production run showed `llm_used_web_search = False` for 100% of
1,524 newly-qualified accounts - not a partial miss, a complete, silent
failure. Root cause chased through two wrong hypotheses before the real
one: first suspected a Serper rate-limit during the heavy concurrent
run (plausible, but a live test immediately after the run succeeded on
the first try, ruling this out). The actual bug: `location = row.get(
"Account State/Province (text only)", "")` in
`modules/sales_intelligence_pipeline.py` - the real column is
`"Account State/Province"`, no `"(text only)"` suffix. Since the key
never existed, `row.get()` silently returned `""` every time, `if
location:` was never true, and `search_company()` (the LIVE, per-account
search - a completely different thing from the classification-stage
cache) was never called at all, for anyone, through this code path.

**Fixed with a one-line change**, then deliberately NOT trusted on faith:
verified with 10 real, live, diverse Bedrock+Serper calls (10/10 success)
before spending real money re-running the affected batch. A retry/backoff
mechanism was also added to `modules/web_search_client.py` around this
same time (transient rate-limit/timeout handling) - a real, separate
hardening, though it turned out NOT to be the actual root cause of this
specific incident.

**New, permanent safeguard**: `main.py` now prints an automatic summary
at the end of every run - `"Web search grounding: X / Y validated
accounts used a real search result"` - with a built-in warning if the
rate drops below 10%. This is the exact signal that would have caught
this bug immediately, instead of requiring a multi-step manual
investigation (spot-checks, a live re-test, tracing the actual code)
well after the run had already finished and money had already been spent.

**Real financial nuance worth remembering**: re-grounding an
already-validated account costs real money again. The fix targeted
specifically the accounts where it mattered most - those the model
couldn't already recognize from memory alone (571, later refined to 528
using fresher data) - not the full population, since accounts the model
already recognized correctly wouldn't meaningfully benefit from
grounding. Confirmed via real numbers before deciding: 953/1,524 already
showed `llm_recognition_verified = True` (grounding wouldn't change
much); 571 showed `False` (grounding could genuinely help) - that 571
was the real, targeted spend, not the full 1,524.

## business_model was silently broken for ~all pattern-matched accounts

**Found while investigating "why does business model say Unknown for
most 6k-sheet accounts"**: confirmed via direct inspection of
`data/company_patterns.json` that all 12 business_patterns entries were
completely missing a `business_model` field - meaning ANY account
classified by pattern (whether by name or by the web-search fallback)
always produced `business_model = "Unknown"`, even with a perfectly real
`industry` match sitting right next to it. This also silently meant 3 of
5 AI-capability messages in `modules/account_enrichment.py`
("Integration Platform", "HR SaaS", "Travel Technology") were reachable
only through a handful of individually-curated `known_companies` entries
(5 total), never through the broader pattern-matching path most accounts
actually go through.

**Fixed**: populated all 12 patterns with real business_model values,
mapping to existing messaging where a sensible match already existed
(API Platform → "Integration Platform", reusing/extending messaging that
previously only reached one company) and writing new AI-initiatives
messaging for the other 9 categories. Confirmed via real, fresh data on
Enterprise East: Unknown rate dropped from 97.0% to 57.4% (2,857
accounts gained a real value that had nothing before) - verified via a
small, deliberately-built 100-account stratified test set BEFORE
touching the full dataset, then confirmed again on the real, full re-run.

**Real, still-open limitation, distinct from the above**: a separate
~2,550-account population where `industry_classifier.py` succeeded
independently (via its own broader keyword system) but
`company_intelligence.py`'s own pattern-matching found nothing at all -
for these, `business_model` has no equivalent fallback the way
`industry` does (industry has a `.where(!= "Unknown", ...)` safety net;
business_model does not, yet). Identified, not yet built.

## Real dataset relationship discovered - the two account lists overlap
## almost completely

Confirmed via direct set-intersection of both raw input files: of
Enterprise East's 6,690 unique account names, 6,680 (99.85%) also appear
in the original 9,758-account file. Enterprise East is effectively a
filtered subset of the larger file, not an independent territory list -
only 10 accounts exist in Enterprise East alone. This is why the shared,
global Serper cache (not per-dataset) paid off concretely: running
`serper_enrichment_pass.py` against the original file found 6,690
already-cached (zero new cost) and only ~3,064 genuinely new searches
needed.

## `--input` CLI flag added to all 6 pipeline scripts

Replaced manual text-patching of `INPUT_FILE`/`OUTPUT_FILE` constants
(the workflow used earlier this session) with real `argparse` support:
`main.py`, `precursor_review.py`, `serper_enrichment_pass.py`,
`build_ae_call_list.py`, `classification_prepass.py`, and
`rerun_qualified_with_search.py` all now accept `--input <path>`.
`main.py`'s `OUTPUT_FILE` auto-derives from the input filename's stem
(confirmed backward-compatible: `report1784905185024.xls` still produces
`report1784905185024_Scored.xlsx`, matching the original historical
naming exactly). The shared Serper cache and the LLM validation
checkpoint deliberately stay as fixed, global filenames, NOT
parameterized per input - both are meant to be reused across every
dataset, not reset per run.

**One real naming consequence to remember**: since `main.py` now derives
its output name from the input filename automatically,
`build_ae_call_list.py`'s `--input` must be updated to match whatever
`main.py` actually produced, rather than assuming a fixed historical
filename.

## Ownership/rebrand signal detection - new, free capability

Built after noticing genuine rebrand/acquisition language showing up
repeatedly in real cached search snippets during spot-checks (Cardtronics
→ NCR Atleos, PrimePay → CoAd, GroupM → WPP Media, and others found
across both datasets). Measured the real scale BEFORE building anything,
per the standing "don't chase 4-5, only chase real scale" rule: 511 of
9,750 cached accounts (5.2%) already contain a real signal phrase - well
above the threshold worth the effort.

New standalone module (`modules/ownership_signal_detector.py`, kept
separate from the already-large `company_intelligence.py`) does a free,
deterministic text-scan over data already paid for by the Serper cache -
no new search, no new LLM cost. Wired into `main.py` right after the
grounding merge, and surfaced on the actual Call Brief in
`build_ae_call_list.py`: a title-row marker ("🏢 Possible Ownership
Change") plus full detail in the Technical Opportunity Canvas section.
Confirmed on a real 100-account test: 5/5 flagged accounts were genuine,
correct signals, zero false positives.

## Second dataset audit (original 9,758-account file) - 2 more real,
## narrow collisions found and fixed

Running the same, already-proven classification code against a second,
different dataset surfaced dataset-specific false positives the first
dataset's audits never hit:
- `"retail banking"` (a standard finance term for consumer banking)
  colliding with the Retail pattern's `"retail"` keyword - GFNorte (a
  real Mexican bank) was misclassified as Retail.
- `"merchant bar"` (a real structural-steel product shape) colliding
  with FinTech's `"merchant"` (payment-processing) keyword - Gerdau
  S.A. (a real global steel producer) was misclassified as FinTech.

Both fixed as narrow, evidenced exclusions, same pattern as earlier
fixes. Also, `"care"` colliding with unrelated "___care" compounds
(confirmed via this second audit: Philadelphia Eagles/"NovaCare Way",
Cambridge Air Solutions/"Client Care", Massey Services/"lawn care") was
finally given the same co-occurrence treatment `"power"` already had,
rather than another one-off exclusion - `"care"` now requires one of its
own pattern's sibling keywords (`health`/`medical`/`patient`) to
co-occur before counting alone. Two smaller, measured-and-rejected
findings from this same audit (a `"cardio"`/FinTech collision at 8
accounts, a fitness-marketing/`"health"` collision at 11 accounts) were
deliberately NOT fixed - both fall well under the standing 100-account
threshold for whether a fix is worth the effort.

## Architecture diagrams rebuilt (docs/sip_architecture.html /
## .mermaid)

Rebuilt from scratch to reflect the whole day's changes (universal
grounding, the two-searches distinction, the location bug, business_model
fix, ownership detection) - then rebuilt AGAIN, deliberately stripped of
all "found today"/dated/session-narrative framing per explicit request,
since the intended audience (SEs presenting to prospects/partners) needs
a timeless explanation of what the system does and when each part runs,
not a changelog. The two-searches distinction (cached/classification vs.
live/per-account) is kept as the single most emphasized point in both
versions, since confusing the two is the easiest way to misexplain this
architecture out loud - confirmed firsthand this session, when
explaining it conversationally took several attempts before landing
clearly, eventually settled by looking at the real code's line numbers
together rather than more prose description.

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
- **A file's modification timestamp is only meaningful next to the actual
  current time** - checked `date` directly against a file's `ls -la`
  output before trusting whether it was fresh or stale (2026-07-30), since
  eyeballing a bare timestamp without a reference point led to real
  confusion mid-run.
- **When a long-running script writes its final output only at the very
  end, checking that output file mid-run will always look stale** - not a
  bug. Check a script's own incremental checkpoint file instead for live
  progress (confirmed on `main.py`: the final `enterprise_east_Scored.xlsx`
  only updates once everything completes; `output/llm_validation_results.xlsx`
  updates every 25 accounts and is the real live-progress signal).
- **After adding a new key to an existing Python dict literal, grep for
  duplicates of that exact key before trusting it** - a duplicate key is
  silently resolved (the later one wins, no error) and can invisibly
  discard a working exclusion. Caught real via `grep -c '"energy":'`
  before shipping, not assumed safe because the file compiled.
- **A fresh test failure is worth checking for a test-fixture mistake
  before assuming a code bug** - repeatedly found the *test* was flawed
  (an account name accidentally containing the very keyword being tested
  for exclusion), not the code under test. Fix the fixture, re-run, only
  conclude a real bug if it still fails with a properly isolated case.

## Parking lot - real feedback received on the 9,758-account report,
## prioritized but deliberately not started yet

Real, substantive review feedback came in on the actual `AE_Call_List.xlsx`
output (2026-08-01). Every specific, checkable factual claim in it was
verified against real data and confirmed accurate before any of this was
taken at face value: correlation between `overall_coi` and
`llm_total_score` is genuinely 0.273 (matches the "~0.27" claim exactly);
2,844 validated accounts, 2,836 unique names, exactly 8 duplicates;
industry distribution (Healthcare 940, Logistics & Transportation 459,
Retail 434, ...) matches exactly. Prioritized, in order, for whenever
this gets picked back up:

1. **8 duplicate accounts in Call Briefs** - quick, cheap, do first.
   Likely explained by the already-documented Account Name-is-not-a-
   unique-key limitation; probably a simple dedup-on-export fix. Not yet
   confirmed or fixed.
2. **Investigate the high-divergence COI/LLM cases directly** (e.g. COI
   68 / LLM 87) before building anything else - informs whether the
   0.27 correlation reflects healthy independent judgment or the LLM
   rewarding a plausible-sounding story over real evidence. Note: a LOW
   correlation isn't inherently a problem, since the two scores are
   DELIBERATELY computed blind to each other on purpose (agreement is a
   signal precisely because it isn't forced) - pushed back on the
   feedback's framing that low correlation itself is the concern, rather
   than assuming the critique is correct as stated.
3. **Evidence / Inference / Hypothesis / Unknown labeling on the Call
   Brief** - the one substantial idea here worth actually committing to
   build soon. Moderate effort (schema + prompt + Call Brief formatting
   changes), no new data sources needed, addresses a real, legitimate
   gap: the Call Brief currently blends "what we know" with "what we're
   guessing" without a clear line between them.
4. **"NOW Score" (hiring, tech announcements, modernization, M&A,
   funding, leadership changes) and the fully redesigned Call Brief
   output format** - genuinely compelling direction, and today's
   ownership/rebrand detector is already a small, real piece of exactly
   this idea - but this is multi-week scope needing its own scoping
   conversation (what signals are realistically detectable, what data
   sources, how it combines with COI), not something to start without
   a dedicated planning pass first.

Separately, the "discovery questions are templated/generic" critique in
this same feedback is NOT a new finding - already investigated directly
(11 real accounts, multiple industries) and concluded the sentence
STRUCTURE converges regardless of further prompt wording changes; more
prompt engineering alone already proved insufficient. If revisited, the
lever is likely more grounded, account-specific facts feeding the prompt
(which today's grounding project was already building toward), not
another round of prompt tweaking.

## Critical checkpoint bug - the LLM validation checkpoint was silently
## dropping other datasets on every run (2026-08-01)

**Discovered while re-running Enterprise East** to pick up recent fixes:
a run that should have cost close to nothing (checkpoint reuse) instead
showed 1,928/1,928 accounts as freshly billed - a real, unexpected
$5.39 charge. Root cause, confirmed by reading the actual code (not
inferred from `grep` line numbers alone, which produced an incomplete,
overconfident explanation at one point before the real code was checked):
`pipeline/llm_validation_pipeline.py` correctly LOADS the full existing
checkpoint (`existing_results`) to look up which of the CURRENT run's
accounts are already validated - but the final write, and a SEPARATE
periodic every-25-accounts checkpoint save, both only wrote back
`kept_df + new_df` - i.e., only accounts belonging to the CURRENT
dataset. Anything in the checkpoint from a DIFFERENT dataset was read in
for the lookup but never carried through to the write, so it silently
vanished.

**Real, confirmed consequence**: switching between the two real datasets
(Enterprise East and the original 9,758-account file) repeatedly caused
each one to erase the other's validated history. Every switch back to a
previously-run dataset forced a full, unnecessary re-validation - real,
avoidable money spent purely because of this bug, more than once today.

**Fixed in both places** (the periodic save required passing the full
`existing_results` into `_run_llm_batch`, which didn't have access to it
before): update the full existing checkpoint in place (matching by
Account Name, updating existing rows, adding genuinely new ones) instead
of overwriting the file with a subset. Verified with a synthetic
simulation of the exact real scenario (two datasets, one shared account,
two dataset-specific accounts) BEFORE touching the real file - confirmed
both that Dataset A survives Dataset B's run, AND that re-running Dataset
A afterward correctly shows 0 new cost while Dataset B's data also
survives.

**A real, separate data-loss incident happened alongside this
investigation**: `output/report1784905185024_Scored.xlsx` (today's fully
corrected version of the original file, with the location-bug fix and
all classification fixes baked in) was lost - traced to a manual trash
restore that brought back an OLDER file
(`report1784905185024_Scored_FINAL.xlsx`, dated Jul 28) instead. Checked
the Trash directly for a more recent copy before accepting the loss -
confirmed genuinely gone, not recoverable. What WAS NOT lost and needed
no rework: the Serper cache (`serper_search_cache.xlsx`, all 9,750
accounts including the corrected location data), Enterprise East's own
data, and every code fix (all safely committed to git throughout the
day). Rebuilt via a fresh `main.py` run - which, thanks to the
checkpoint fix landing just before this rebuild, correctly reused 1,926
of 2,805 candidates for free (the real overlap with Enterprise East's
already-validated accounts) rather than needing a full re-spend.

**Working-style lesson from this specific exchange**: when asked to
explain unfamiliar code, `grep` output showing WHERE a keyword appears
is not the same as knowing what the code DOES - stated a specific,
detailed technical explanation once based only on line-number
groupings, which the user correctly caught and pushed back on. Only
after being shown the real code between those lines was the explanation
actually correct. Confirming certainty ("here's exactly what's
happening") should be reserved for cases where the actual logic has
been seen, not inferred from where a variable name happens to appear.

## Session summary (2026-08-17 / 2026-08-18) - Account ID/Salesforce ID,
## real Employee/Revenue scoring gaps, the workloads bug, a score guide,
## and a new Salesforce report-metadata header issue

**Account ID, Salesforce ID, ICP Grade added to the AE report.**
Confirmed `CB Account Number` (Enterprise East's field) and a genuine
Salesforce record ID (`Account ID`/`ID (Long)`, seen in newer exports)
are NOT the same kind of identifier - `CB Account Number` couldn't be
found anywhere in the actual Salesforce UI. Built as two separate,
honestly-labeled columns rather than merging them, since a downstream
integration needs the real 18-character Salesforce ID specifically
(the 15-character version is case-sensitive and unsafe for external
joins - Salesforce's own guidance is to always use the 18-char form).
ICP Grade added beside COI Score for direct comparison, per the
person's request.

**Real Employee/Annual Revenue data was never being used at all -
now fixed, two separate gaps.** `company_size` (`enrich_account()`,
modules/account_enrichment.py) previously came ONLY from an
industry-list + name-keyword guess - Wawa ($18.9B revenue, 36,000
employees) and Total Wine & More ($2.3B revenue, 4,000 employees)
both scored `company_size=Unknown` because Retail isn't on the
enterprise-industry list and neither name matches a keyword, despite
real Employees/Annual Revenue data sitting unused in the same row.
Separately, `revenue_signal` - the field that actually reaches the
LLM prompt, unlike `company_size` - had the same class of gap.  Both
fixed: real data takes priority when available, falling back to the
existing heuristics otherwise. Confirmed real, broad impact on a
58-account file: 26 of 58 accounts gained a real +5 COI point
increase, one crossed the LLM-qualification threshold as a direct
result, and Wawa/Total Wine both moved from COI 40 to 45 (this part)
then to 60 (see workloads bug below).

**Confirmed and fixed the magnitude-detection regex bug** - five
unrelated real companies (PVH, TuneCore, Hess Midstream, PowerReviews,
Tradeweb) shared an identical LLM score of 87, traced to a fixed
score-floor override (35+27+25=87) meant only for genuine $1B+ dollar
evidence. The regex had an optional `$` sign, so ANY large number
(TuneCore's "10 billion tracks" - a track count, not money) could
trigger it. Fixed to require a real dollar sign or dollar-context
word nearby. Confirmed 11 unique accounts across two datasets were
genuinely affected (2 false positives: TuneCore, PowerReviews),
corrected via targeted re-run.

**The biggest fix of the session: `workloads` was silently empty for
96.5% of ALL scored accounts, across every workload type, not just
one industry.** `apply_intelligence()` read `"workloads"` from the
business_pattern dict, which never contains that key at all - the
real list only exists in `WORKLOAD_PROFILES`, keyed by
`workload_profile`. Since `workload_text` (used for keyword-based
`workload_fit_points` scoring, the single largest COI component at
40 points) is built by joining this list, it was always empty for
everyone, meaning that half of the workload-fit score never had
anything to match against, for any account, in any dataset scored
before this fix. Confirmed real impact: Wawa and Total Wine both
moved from COI 45 to 60 once corrected, and re-running a 58-account
file surfaced 4 new accounts crossing the LLM-qualification
threshold as a direct result. This affects Enterprise East and the
original 9,758-account file too, not yet re-run for it as of this
writing.

**"HOW TO READ THE SIP SCORES" guide added to the Overview sheet** -
plain-language ICP/COI/LLM/SIP definitions, since a rep has no way to
know these are four deliberately independent signals otherwise (a
company can be a poor ICP fit with strong technical signals, or vice
versa - not a scoring flaw, the design). Took several real, genuine
mistakes to get right, worth recording so they aren't repeated:
merging a row only preserves the first cell's value, so combining
label+definition text into one string BEFORE merging is required, not
after; setting a border only on a merged range's first/last cell
leaves the middle columns unbordered, silently breaking the visible
line - every column in the range needs the border set explicitly, not
just the endpoints; and a border fix isn't real until it's actually
been rebuilt into the output file and looked at directly - confirming
a patch script printed "Applied" is not the same as confirming the
resulting Excel file looks right. Final version: one single merged
cell (not five), positioned beside the data starting at column J
(not above it, so it doesn't require scrolling past to reach
accounts), with one continuous outer border and no internal lines.

**New Salesforce report-metadata header issue, found on Gary
Peterson's export (same report template as previously-working
files).** Some exports include a title, generation timestamp, and a
"Filtered By" section with filter criteria above the real header row
- confirmed 9 such rows in this specific case. `load_accounts()` now
detects this (checks if most columns came back as `Unnamed:`) and
re-scans for the row containing `"Account Name"` rather than assuming
a fixed number of rows to skip, since that count varies by export
even from the same report template. Fully backward-compatible - only
activates when needed, tested against the real file plus edge cases
(normal file, and a file where "Account Name" can't be found at all)
before shipping.

**Working-style note from this session, worth remembering**: patch
scripts that fail to match their target text can fail SILENTLY if the
`rm`/compile-check steps that follow don't depend on the patch having
actually succeeded - a "Syntax OK" print only confirms the file is
still valid Python, not that the intended change is actually in it.
Several real rounds of confusion this session traced back to exactly
this - assuming a patch worked because later steps in the same
command block completed without error, rather than directly
confirming the specific new code is present.

## Session continuation (2026-08-18, later) - real Industry override,
## the media_platform under-scoring discovery, a new "card" false
## positive, and a genuinely long chart-debugging saga

**Business Model column removed from the Overview sheet.** Confirmed
redundant with Industry for 7 of 12 patterns (identical string in
both fields) - kept Industry, widened the ICP Grade/COI Score columns
to compensate for lost visual space.

**Real Salesforce Industry override added**, same "real data beats
keyword guess" pattern as Employees/Revenue. Confirmed real
misclassifications this fixes: Wegmans Food Markets (tagged
"Healthcare" via a "healthier" substring match in ordinary grocery-
store marketing copy - real Salesforce Industry: "Retail"), Envestnet
and Interactive Brokers Group (also tagged "Healthcare", real
Industry: "Financial Software"/"Finance"). Verbose real industry
labels ("Customer Relationship Management (CRM) Software") also
shortened for display via a small mapping dict, applied after the
override.

**Full Landscape chart - a long, genuinely difficult debugging
saga.** The original native bar chart never rendered category labels
correctly - traced through several real, confirmed causes (a numRef
vs strRef mismatch, a missing tickLblPos setting on both axes) but
each fix, though individually verified correct via direct XML
inspection, didn't resolve the actual visual rendering. Tried, in
order: horizontal bar (broken), Data Bars conditional formatting
(worked but felt cluttered combined with existing color scales,
rejected), vertical column chart (same broken-label problem,
different orientation). What actually worked: a **pie chart** -
pie charts use a legend rather than a category axis to show names,
and the legend mechanism was already confirmed working elsewhere in
the same workbook. Real lesson from this stretch: a "correct-looking"
XML inspection is not the same as confirming the actual visual
result - several rounds of back-and-forth happened specifically
because a structurally-verified fix was presented with more
confidence than warranted before the person had actually looked at
the rendered file.

**Contact recommendation logic improved** - previously a flat
workload_profile-only lookup meant StockX (auctions/resale), AppCard
(loyalty marketing), and Quantic (retail POS) all got the identical
"Director of Payments / Head of Fraud Engineering" suggestion purely
because they shared a workload_profile, despite being genuinely
different businesses. Added a more specific (workload_profile,
industry) lookup, checked first, falling back to the original
broader mapping when no specific pair is covered.

**The `media_platform` under-scoring discovery - found through the
user's own careful analysis, not a routine audit.** The user
independently noticed Tier 3 (Nurture) accounts showing a *higher*
average LLM score than Tier 1 in a real 22-account sample, flagged
Index Exchange (COI 42, LLM 75, a +33 gap) as the standout anomaly,
and asked whether COI was undervaluing real-time media/ad-tech
platforms. Verified directly: `media_platform`'s ratings are a flat
"3, 3, 3" across every dimension, versus `payment_platform`'s "5, 5,
5" - and checking every media_platform account across every dataset
built this session (59 total) found 57 of 59 showed a positive
COI-vs-LLM gap, several by +45. Index Exchange's real cached search
text confirmed "global supply-side platform" - a genuine real-time ad
exchange, not a generic media company. Fixed by adding a new, more
specific pattern ("Ad Exchange / Real-Time Advertising Platform",
keywords: supply-side platform, demand-side platform, ad exchange,
programmatic advertising) checked before the generic Media/Advertising
pattern, using payment_platform-level ratings. Verified: Index
Exchange moved from COI 42 (Tier 3 Nurture) to COI 83 (Tier 1
Strategic), LLM unchanged at 75 - the gap didn't just shrink, it
flipped direction entirely, correctly reflecting genuine technical
strength rather than an artifact of a flat rating.

**A new "card" false positive, found while checking a second high
COI in the same review.** AppCard (COI 93, `payment_platform`) is
actually a loyalty/shopper-analytics platform for grocers, per its
own real description - nothing about payment processing. The `card`
keyword in the FinTech pattern is bare/unguarded, matching anywhere
it appears as a substring - including inside the account's own name,
"App**Card**". Important context checked before fixing this: `card`
already has a real, working exclusion list (`cardinal`, `wildcard`,
`cardiology`, `cardiac`, `piccard`), documented earlier this session
- so this wasn't an overlooked keyword, just a not-yet-discovered
specific case, exactly the same incremental process that built the
existing list. Added `appcard` to it. Verified: AppCard now correctly
shows `retail_platform`, industry "Advertising", COI 55 (down from
93).

**Working-style note, directly prompted by this stretch**: the
person pointed out this documentation file itself had not been kept
current through a long, busy stretch of work - and the very next
task (checking whether "card" had ever been considered before) proved
exactly why that matters. Finding the existing `card` exclusion list
in this doc meant building on established precedent instead of either
re-solving something already solved, or - worse - building a
redundant, inconsistent second mechanism alongside it. This file is
only as useful as it is current.

## SIC Code and Ownership added (2026-08-18, later still)

**SIC Code fallback for industry classification** - a third-tier
signal, used only when both the real Salesforce Industry field AND
keyword-matching leave an account as "Unknown". Real Industry still
wins whenever present; SIC only fills a gap neither of the stronger
signals could. Built from a hand-made code-to-industry map covering
codes actually observed in real data so far (602/603 banking,
609/631 financial services/insurance, 421/422 trucking, 541/531/596
retail, 737/738 software/business services, 873 professional
services, 801/806 healthcare, 283 pharma, 384 medical devices,
481/482 telecom, 491/492 utilities, 731 advertising, 781 media) -
explicitly not an exhaustive SIC reference, and one real mapping
error was caught before shipping: 679 was initially mapped to
"Insurance," but it's actually the generic "Offices of Holding
Companies, Not Elsewhere Classified" code - removed rather than left
in, since a holding company's SIC code says nothing reliable about
its actual industry. Tested against 3 real accounts with a SIC Code
but no Salesforce Industry (MarketAxess, OTR Solutions, Transcard
Payments) - all three already had industry resolved via
keyword-matching before the SIC fallback got a chance to apply, so
the mechanism remains logically tested but not yet proven against a
genuine real-world trigger case. Low risk either way - purely
additive, never overrides a working classification.

**Ownership (Public/Private) added to the LLM prompt** as additional
context, same pattern as revenue_signal. Deliberately narrower in
scope than it might first appear - discussed directly with the user
before building: this doesn't feed industry classification or COI
scoring at all, its only real value is giving the model explicit
context for why a company might genuinely lack public financial
disclosures (the same class of problem Wawa/Total Wine hit earlier
this session, already solved for scoring via real Employee/Revenue
data). Its marginal value here is narrower than SIC Code's, since the
core problem it might have helped with was already fixed - noted
honestly rather than oversold.

**Real process note**: the code for both of these was written,
tested, and verified working - but the actual `git commit` was never
run, and this went unnoticed through several follow-up messages
until a direct question ("did we do a full update of design doc")
prompted a check. `git status` remains the one place a slipped
commit can't hide - worth checking it explicitly rather than
assuming a fix landed just because it was verified working.


