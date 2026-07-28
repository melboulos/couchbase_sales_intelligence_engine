# Couchbase Sales Intelligence Engine (SIP)
## Design Status Update — July 24, 2026

This update covers a same-day follow-up session, building on the July 20, 2026 update (`Couchbase_SIP_Design_Doc_Update_2026-07-20.md`). That document remains the source of truth for the core architecture, mission, and philosophy — nothing there has changed. This document covers what happened since.

---

## Mission (Unchanged)

Help Couchbase sales reps identify the right accounts to call, have more meaningful technical discovery conversations, shorten sales cycles, and prioritize accounts with strong Couchbase opportunity signals. The COI score is a prioritization mechanism, not the product. The LLM never qualifies or scores accounts as part of the deterministic pipeline — it generates seller intelligence for accounts the deterministic engine has already selected.

---

## What Prompted This Session

The previous session ended with a production run (350 accounts routed to the LLM, 320 validated) and a working AE call list export. This session began with a request to validate the underlying scoring heuristics against real-world data — first a hand-picked prospecting list, then, critically, Couchbase's actual closed-won deal history.

---

## Key Findings and Changes This Session

### 1. Confirmed keyword false-positive bugs

Testing against a 24-account prospecting sample surfaced two confirmed bugs in `company_intelligence.py`'s substring keyword matching:

- `"power"` matched inside unrelated company names (PlayPower, CK Power, Berendsen Fluid Power, Powers Data Resources) — only ~30% of "power" matches in the real dataset were genuine utilities.
- `"card"` matched inside unrelated names (Cardinal Logistics, Cardinal Innovations Healthcare, Wildcard Corp.).
- Later in the session, a related bug was found: `"api"` matching inside "Capital" (e.g., "Networld Capital Ventures, Inc." incorrectly matched as API Platform).

**Fix:** added `KEYWORD_FALSE_POSITIVE_EXCLUSIONS` to `modules/company_intelligence.py` — an explicit exclusion list per keyword (e.g., `"card"` excludes `"cardinal"`, `"wildcard"`). Word-boundary regex was considered and rejected: most genuine `"card"` matches are compound words with no separator (Cardtronics, Datacard, Cardcash), so boundary matching would have removed more true positives than false positives.

### 2. Validated scoring against real closed-won revenue data — this was the major finding

The user provided the actual Salesforce Closed Won export (`Closed Won-2026-07-24-08-25-11.xlsx` — contains real customer/revenue data, gitignored, never committed to the repository).

**Data cleaning required:** the raw export mixed real sales-assisted deals with self-serve Couchbase Capella signups and usage-based billing adjustments ("CBC OD" line items). After filtering these out, **139 unique accounts represented genuine, sales-assisted closed-won deals.**

**Result: only 7 of 139 real closed-won accounts (5%) matched anything in `company_patterns.json`.** This confirmed, with real revenue data rather than a hypothetical sample, that the scoring model was missing the large majority of Couchbase's actual customer base.

**Notable gaps found:** American Express AZ ($41M — the single largest deal in the dataset), Mavenir Systems ($19.4M), Sabre GLBL ($16.5M combined), and entire verticals with zero coverage (telecom, media/entertainment, travel/hospitality, gaming, CCaaS, cybersecurity, aerospace/defense, government) were all invisible to the scoring engine.

### 3. Expanded pattern coverage, all changes verified against real data

- **Two new business_patterns added:** Telecom (keywords: telecom, telecommunications, wireless, communications, cellular) and Media/Entertainment (keywords: entertainment, broadcasting, studios, pictures, animation) — kept deliberately separate from the existing Media/Advertising pattern, since ad-tech/agencies and streaming/entertainment studios have different technical profiles. Corresponding `workload_profiles` added (both scored 4/4/4 across database intensity, operational complexity, and real-time requirement).
- **~30 new `known_companies` entries added**, each individually verified via research rather than assumed:
  - **Banking:** only "elephant"-scale banks per explicit direction (Bradesco, BTG Pactual, State Street Bank, Australia and New Zealand Banking Group) — smaller banks and credit unions remain excluded, since they are confirmed not to be a target segment regardless of technical fit.
  - **Travel/Hospitality:** American Airlines, United Airlines, Royal Caribbean Cruises, Virgin Voyages, Sandals Resorts, Marriott International, Arrivia, Klook Travel Technology.
  - **CCaaS:** Five9, LivePerson (scored highest of the new batch — 5/5/5 — since their entire business is real-time customer interaction data at scale).
  - **Cybersecurity:** Zerofox.
  - **Industrial/Aerospace/Defense:** Northrop Grumman, Motorola Solutions, BNSF Railway, TTX Company, AGCO Corporation, Baker Hughes, NOV Inc.
  - **Government:** National Oceanic and Atmospheric Administration, Florida Department of Highway Safety and Motor Vehicles, NSA, Defence Science & Technology Agency DSTA. Government confirmed in scope despite long sales cycles — "some govt is ok, can't eliminate totally."
  - **Gaming:** Crowdstar, Playgon Games, FBM Gaming, Snapser — each confirmed via web research as genuine technical fits, not assumed from the category alone (Snapser in particular is literally a backend-as-a-service platform built for games, arguably one of the strongest conceptual fits added this session).

**Result after these additions: match rate against the same 139 real closed-won accounts improved from 7 to 41** — a measured 5.8x improvement, verified by re-running the actual matching code, not estimated.

### 4. Important scope correction from the user, worth preserving as project guidance

After the known_companies additions, the user explicitly flagged that this approach has a hard ceiling: **`known_companies` entries only help when that exact company name reappears — they do nothing for the thousands of other accounts in the full list that haven't been individually identified.** The stated goal is a system that can recognize the *next* unknown account with a similar profile, not just memorize names already known. This is the correct framing for evaluating any future scoring work — coverage of named accounts is not the same as generalization.

### 5. New feature attempted this session: independent LLM scoring — NOT YET WORKING

**Design intent:** in addition to the deterministic COI (unchanged, fully separate), have the LLM enrichment call also produce its own independent 0–100 score, using the same 3-dimension rubric as `scoring_engine.py` (workload/operational fit 0–40, real-time requirement 0–30, technical/architectural complexity 0–30) — but **deliberately never shown the deterministic COI, Priority Tier, or the underlying `database_intensity`/`operational_complexity`/`realtime_requirement` values.** The two scores are meant to sit side-by-side in the output purely so a human can compare them and find gaps in `company_patterns.json` coverage — they are never merged, blended, or used to adjust each other.

**What was built:**
- `modules/llm_prompt_builder.py` — new `INDEPENDENT SCORE` section with the rubric above; COI/Tier/intensity values removed from `ACCOUNT DATA`; schema extended with `llm_workload_score`, `llm_realtime_score`, `llm_complexity_score`, `llm_total_score`, `llm_score_reasoning`.
- `modules/sales_intelligence_pipeline.py` — new `validate_independent_score()` confirms each sub-score is in range and the three sum correctly to the total.
- `main.py` — new score columns added to the merge step.

**Confirmed bug, not yet fixed:** `llm_total_score` converged to the identical value (75) across three different accounts with different business models — Paytronix Systems (COI 89), Cleo (COI 87), and OpenKey (COI 87, sub-scores 30+25+20=75). This is not plausible coincidence across three different reasoning chains landing on the same number.

**Root cause hypothesis, not yet tested:** the prompt still shows the LLM `Business Model` and `Observed Workloads` — both derived directly from whichever `company_patterns.json` entry already matched the account. The theory is the model is anchoring on these pre-interpreted category labels even though the raw numeric fields were successfully hidden.

**Proposed fix, not yet built:** split `ACCOUNT DATA` into two blocks — the existing one (with `Business Model`/`Observed Workloads`) continues feeding the qualitative sections (`ENGINEERING INTERPRETATION`, `COUCHBASE POINT OF VIEW`), which are working well and should not be touched. A new, deliberately minimal block (Account Name + Industry only, pending confirmation that `Industry` itself isn't also pattern-derived) would feed only the `INDEPENDENT SCORE` section.

This feature is committed with the bug openly documented in the commit message. It should not be trusted or used for any real decision until the anchoring problem is resolved and re-tested against both a known high-COI account and a forced-through low-COI/excluded account.

---

## Current State Summary

| Item | Status |
|---|---|
| Keyword false-positive fixes (`power`, `card`, `capital`) | Done |
| Telecom business_pattern | Done |
| Media/Entertainment business_pattern | Done |
| ~30 new known_companies entries (verified via research) | Done |
| Match rate vs. real closed-won accounts | Improved 7 → 41 of 139 (verified) |
| Independent LLM scoring — prompt/validator/merge built | Done |
| Independent LLM scoring — actually discriminating by account | **Not working — confirmed convergence bug** |
| Classification pre-pass for unmatched accounts (cheap LLM call → workload_profile/exclusion/confidence) | **Not yet built** |
| Real Bedrock pricing vs. hardcoded `$0.99/1K` constant in `pipeline/llm_validation_pipeline.py` | **Unconfirmed — public pricing data suggests the hardcoded constant may overstate real cost by ~1000x, but this could not be verified against an actual bill this session** |

---

## Immediate Next Steps

1. **Fix the independent-score anchoring bug** — restructure `ACCOUNT DATA` into two blocks as described above, then re-test against both a Tier 1 account and a forced-through low-COI/excluded account (a test harness that monkey-patches `deterministic_gate` for this purpose only, without touching the real gate file, was partially drafted this session).
2. **Build the classification pre-pass**, once the independent scoring is trustworthy — a cheap LLM call for the ~6,000 currently-unmatched accounts, returning `workload_profile` guess, `excluded_category` flag, and `confidence`, feeding the existing deterministic scoring exactly as a real pattern match would. Confidence gating is essential here: a low-confidence guess should leave the account unmatched (current default behavior), not introduce a false signal.
3. **Confirm real Bedrock pricing** against an actual bill or AWS console access, and correct the hardcoded `$0.99/1K` constant in `pipeline/llm_validation_pipeline.py` if it's confirmed inaccurate — this affects the trustworthiness of every cost figure the system has reported.
4. **Re-run the full 6,701-account production pipeline** once the above are resolved, to see the real, current match rate and cost at scale — not yet done this session.

---

## Follow-up (new session, same date)

A prior version of this document/session believed a second fix — removing
`Business Model`/`Observed Workloads` from the scoring section and adding
contrastive calibration examples plus an `llm_company_recognized` flag —
had already been saved to `modules/llm_prompt_builder.py`. On starting a
fresh session and cloning the repo directly from GitHub, that fix was
**not actually present** in the committed file; only the first (already
confirmed-failed) fix was there. The likely cause is an edit that was
never saved/committed before a test was run against it, not `__pycache__`
staleness (no `__pycache__` directories exist in a fresh clone anyway).

That fix has now been implemented for real, in this session, in
`modules/llm_prompt_builder.py`:
- `INDEPENDENT SCORE` now uses ONLY the Account Name — Industry, Business
  Model, and Observed Workloads are explicitly excluded from this section
  (they remain used by the other, unaffected qualitative sections).
- Added contrastive calibration examples (small regional bank vs. global
  real-time trading platform, both "financial services").
- Added a required `llm_company_recognized` boolean — the model must
  name a concrete fact about the specific company to set this true, and
  is instructed to score conservatively/low (5-15 / 0-10 / 0-10) if it
  cannot.
- `modules/sales_intelligence_pipeline.py` now validates
  `llm_company_recognized` is present and boolean-typed as part of
  `validate_independent_score()`.
- `modules/llm_client.py` `max_gen_len` increased from 700 to 1500,
  since the longer prompt/schema is a plausible contributor to the
  Netspend JSON truncation error observed earlier this session.
- `test_llm_validation.py` now includes the `FORCE_LLM_OVERRIDE`
  monkeypatch of `deterministic_gate.deterministic_gate` (test-process
  only, real gate file untouched) so United Community Bank, Members 1st
  Federal Credit Union, and Trumid Financial are forced through the LLM
  regardless of gate outcome, for calibration testing.

**This has NOT been tested against the live model** — this session's
sandbox has no AWS credentials/`boto3` and cannot call Bedrock. Someone
needs to pull this branch and run `test_llm_validation.py` locally to
confirm whether `llm_total_score` actually discriminates now (in
particular, whether United Community Bank drops out of the ~70-80 band
it previously converged into). If it still doesn't discriminate even
confirmed running against this exact code, treat it as a likely model
capability limit (Llama 3 70B may not reliably self-report "I don't
recognize this company") rather than a prompt-wording problem, and
move to enforcing the conservative cap in code — e.g., in
`validate_independent_score()`, raise or clamp when
`llm_company_recognized` is `false` but sub-scores exceed the
conservative band — rather than relying on the prompt alone.

---

## Session: July 25, 2026 — Calibration confirmed, cap enforcement added, real production run, five real bugs found

### Independent LLM scoring: confirmed fixed, then hardened further

Ran `test_llm_validation.py` live against Bedrock. The July 24 fix
worked partially — Netspend/Trumid/UCB stopped converging to identical
scores, but `llm_company_recognized` was still not trustworthy: Trumid
claimed `false` and said "I score conservatively" in its own reasoning,
then returned 60/100 anyway — well above the mandated <30 ceiling. The
model can articulate the calibration rule but doesn't reliably act on
it numerically, confirming the design doc's own predicted fallback.

**Two structural (code-enforced, not prompt-only) fixes added:**

1. **`enforce_company_recognition_cap()`** in
   `sales_intelligence_pipeline.py` — when recognition isn't verified,
   sub-scores are clamped in code to workload≤15/realtime≤10/
   complexity≤10 and `llm_total_score` is recomputed, regardless of
   what the model returned. Sets `llm_score_capped` so capped rows are
   visible, not silently rewritten.

2. **`llm_specific_fact` + `validate_recognition_evidence()`** — the
   model must now state one concrete, checkable fact about the named
   company (with explicit good/bad examples in the prompt); a stoplist
   of generic phrases (`"as a fintech company"`, `"based on my
   knowledge of"`, `"typically"`, etc.) determines
   `llm_recognition_verified`, which is what the cap actually keys off
   — not the model's raw self-report. Confirmed via live test: Netspend
   went from "as a FinTech company, X typically has..." (unverified,
   would now be capped) to a real fact ("prepaid card platform owned by
   Global Payments, several million cardholders" — verified, scored on
   its own merit).

**Known remaining limitation, not fixed:** `llm_specific_fact` passing
the generic-phrase check doesn't mean it's *true*. Live production run
caught BayMark Health Services (a real opioid-treatment provider)
described as "a healthcare technology company providing patient
engagement and data analytics solutions" — a confident, specific,
completely fabricated fact. A cluster of ~12 regional healthcare
systems (Beaumont Health, Spectrum Health, Palmetto Health, etc.) also
converged to an identical 25/20/20=65, this time using real facts
worded distinctly per account — the model found a new way to satisfy
the fact-check without actually differentiating. Neither is currently
catchable in code without external fact verification. Mitigated in
practice by `build_ae_call_list.py` never surfacing these fields to
reps — they exist for internal COI-comparison/gap-finding only.

### Real Bedrock pricing corrected

`LLM_INPUT_COST_PER_1K` / `LLM_OUTPUT_COST_PER_1K` in
`pipeline/llm_validation_pipeline.py` were `0.99` (i.e. $990/million
tokens) — off by ~1,375x versus the real on-demand rate for Llama
70B-class models (~$0.72/million, confirmed via web search against
AWS's pricing page and independent trackers). Corrected to `0.00072`.
The README's previous "~$463 for 350 accounts" cost claim was itself a
symptom of this bug and is corrected below.

### HTML-disguised-as-.xls loader fix

The real account export (`report<timestamp>.xls`, a Salesforce report
download) is not a real Excel binary — it's an HTML `<table>` saved
with a `.xls` extension, a common export quirk. `pipeline/loader.py`
now falls back from `pd.read_excel` to `pd.read_html` automatically
when the content looks like HTML, rather than raising an unhelpful
"Excel file format cannot be determined" error. Added `lxml` to
`requirements.txt` for the HTML parser.

### company_patterns.json coverage gaps found via the real 9,758-account file

Built `precursor_review.py` (free, no LLM calls — runs enrichment/
scoring/gate only) to see how many accounts would qualify before
spending anything. Result on the real file: 513/9,758 (5.2%) would go
to the LLM; 92.6% landed in Tier 4 Monitor. Sampling Tier 4 (via
`review_tier4_full.py`, `review_tier4_sample.py`,
`analyze_partial_signal_distribution.py`,
`near_threshold_differential.py`, `vertical_laggard_check.py`, all new
this session) surfaced real, concrete misses:

- **Elephant-company gap**, same failure mode as the LLM calibration
  bug, just on the deterministic side: `insurance_platform`,
  `pharma_device_platform`, and `utilities_platform` apply a single
  flat rating regardless of company scale. New York Life, HCC
  Insurance Holdings, Novartis, Teva, Alexion, Westar Energy, and
  Mitsubishi Electric Power Products (verified via web research) were
  scoring identically to small regional/long-tail companies in the
  same vertical. Added as `known_companies` overrides — the long-tail
  default is left untouched since it may be genuinely correct for most
  of that population.
- **Keyword false positives** in `company_intelligence.py`'s
  `KEYWORD_FALSE_POSITIVE_EXCLUSIONS` (the same mechanism added July 24
  for "card"/"capital"): `"media"` was matching inside "Remedial
  Construction Services," "National Mediation Board," "Allegheny
  Intermediate Unit," and "Immedia Semiconductor" — none are media
  companies. `"energy"` was matching "Department of Energy" and
  "National Lab(oratory)" entities, incorrectly giving federal
  government/research organizations a utilities score boost. Both
  fixed; real energy/media companies confirmed still match correctly.

### Real production run: 9,758 accounts, three more bugs found live

Ran the real file end to end. Final numbers: 513/513 LLM-validated,
$0.9839 actual cost (matches the corrected pricing estimate almost
exactly), 15 industries, 9,755 accounts after removing 3 genuine
source-data duplicate rows. Three additional bugs were found and fixed
mid-run, all from real data, not theoretical:

1. **Sequential LLM calls → threaded.** `validate_accounts()` in
   `pipeline/llm_validation_pipeline.py` ran one account at a time;
   ~513 accounts would have taken over an hour. Rewritten with
   `ThreadPoolExecutor` (5 concurrent), cutting the real run to ~28
   minutes. Added incremental checkpointing (every 25 completions
   instead of only at the very end) so a crash or dropped connection
   mid-run doesn't lose completed work — this mattered in practice,
   since the first full run did crash (see #2 below) after all 513
   calls had already succeeded.
2. **Merge crash on duplicate Account Name.**
   `llm_results.set_index("Account Name").map(...)` requires a unique
   index; this file has genuine duplicate names for different accounts
   (confirmed earlier: two different "United Community Bank" entries
   with different CB Account Numbers). Fixed by deduplicating before
   building the lookup index. Same root cause independently caused a
   **second** bug in `main.py`'s own final merge
   (`accounts.merge(..., on="Account Name", how="left")`) — a
   many-to-many join on a repeated key was silently inflating row
   count (9758 → 9760, confirmed and reproduced exactly). Both fixed
   the same way: dedupe the right side before merging. Known
   accepted limitation either way: two different accounts sharing an
   exact name will receive the same merged LLM result.
3. **Two real, over-strict validation rules rejected correct LLM
   output** for 10/513 accounts on the first full run:
   - `validate_account_identity()` was comparing account names
     case-and-whitespace-normalized but NOT punctuation-normalized;
     the model consistently drops the trailing period after
     abbreviations ("Inc." → "inc", "Limited." → "limited"), which was
     being treated as a hallucinated identity mismatch rather than a
     formatting difference. Fixed with a dedicated
     `normalize_for_identity_match()` that also strips trailing
     `.`/`,`.
   - `validate_evidence_quality()`'s forbidden-buzzword list banned
     the bare word `"enterprise"` — a single common word with
     legitimate technical uses ("enterprise architecture,"
     "enterprise-grade consistency"), unlike the other multi-word
     phrases in the list (`"market leader"`, `"growth opportunity"`,
     etc.). This was rejecting real, correct intelligence for
     genuinely large accounts (NSA, Northrop Grumman) purely for using
     an accurate word. Removed; the other seven items remain.
   All 10 originally-rejected accounts were confirmed to pass after
   the fixes and re-ran clean.

### New files this session (all committed)

`precursor_review.py`, `review_tier4_full.py`,
`review_tier4_sample.py`, `analyze_partial_signal_distribution.py`,
`near_threshold_differential.py`, `vertical_laggard_check.py` — none
are part of the production pipeline; all are one-off analysis tools
used to find the issues documented above, kept in the repo since
they're reusable against any future account list.

### What's safe

Everything above is committed and pushed to `main`. The real
9,758-account run completed successfully end to end:
`output/report1784905185024_Scored.xlsx` (9,755 rows, deduplicated,
verified no row-count drift from the original 9,758 load) and
`output/AE_Call_List.xlsx` (513 qualified accounts, correct numbers
confirmed) are both real, correct deliverables — not the stale
6,701-account/320-account version that was accidentally rebuilt once
mid-session from an un-updated `build_ae_call_list.py` before being
caught and corrected.

---

## Same-day follow-up: classification pre-pass for the 7,732 Unknown accounts

### The gap

79% of the real file (7,732 of 9,758 accounts) had `industry ==
"Unknown"` - genuinely no signal at all, since this lean export has
no raw Industry/revenue/employee-count field, only the account name.
Given real Bedrock cost was confirmed at ~$0.98 for 513 full
intelligence calls, a much cheaper classification-only call became
worth trying at this scale.

### Design

`modules/classification_prompt_builder.py` builds a deliberately
narrow prompt: classify one company into one of the 13 existing
`workload_profile` categories, or say "none" - not a scoring prompt,
no engineering narrative. Same fact-verification discipline as the
independent score (a genuine, checkable fact required before
`llm_company_recognized` can be trusted). A verified classification
gets folded into the row's `database_intensity`/
`operational_complexity`/`realtime_requirement` via the SAME
`workload_profiles.json` join `company_intelligence.py` already uses,
then `calculate_coi()` - the same, unmodified scoring function
everything else runs through - recomputes the score. No parallel
scoring path.

**Scale-tier adjustment**, added after the user asked for a way to
get more accurate scoring beyond just classification: rather than
trusting raw LLM-generated intensity numbers (already proven
unreliable for the independent score), the model is asked a bounded,
discrete question - is this SPECIFIC company above, below, or
typical for its category - and `apply_scale_adjustment()` in
`sales_intelligence_pipeline.py` applies a code-enforced +/-1 nudge
(capped 1-5), only when recognition is verified. Confirmed via
testing: Novartis (above_typical, verified) -> 43 vs. a generic
regional pharmacy (typical) -> 34, a real 9-point differentiation
from genuine evidence instead of a flat category default.

`classification_prepass.py` runs this threaded (5 concurrent,
checkpointed every 100) against all Unknown accounts, writing to a
NEW file rather than overwriting the existing scored output.

### Real run results

7,732 accounts classified in 2,449s (~41 min). 5,032 (65%) genuinely
verified. 3,761 (48.6%) upgraded from Unknown to a real category -
of those, 2,963 (79%) actually cleared into Tier 2/3, not just got
relabeled while staying Tier 4. Full-file tier shift: Tier 4 dropped
9,035 -> 6,069, Tier 3 jumped 676 -> 3,638. Real cost: $2.60 (higher
than the ~$1-2 rough estimate given going in, but still trivial in
absolute terms).

### Accuracy spot-check found real problems - documented, not hidden

A 26-account stratified sample (weighted toward Tier 2/3, the
higher-stakes population that actually reaches a seller) surfaced,
in order of severity:

- **Two confident fabrications**, same failure mode as BayMark
  Health Services from the earlier production run: Pfizer described
  as producing "the popular pain relief medication Advil" (wrong -
  not a current Pfizer product), and Microvast described as "a
  Chinese biotech company" with an invented-sounding product name
  (Microvast is actually an EV battery company). **No code fix
  exists for this** - a specific-sounding fact passing the
  generic-phrase stoplist does not mean it's true, and this requires
  an external lookup to catch, which is out of scope for this
  pipeline. Documented as a standing, unresolved limitation.
- **A data-hygiene bug unrelated to the LLM**: an account literally
  named "TELEFONICA BRASIL S/A - DUPLICATED - TO BE DELETED" went
  through the full pipeline and landed in Tier 3 as a live prospect.
- **A defunct-company bug**: "Tier 3, Inc." scored as an active
  telecom account, despite the model's own fact correctly stating in
  the past tense that it "was... acquired by CenturyLink in 2014."
- **Category-fit mismatches where the fact was accurate but the
  category was wrong**: Strayer University -> `saas_platform`,
  Marfrig Global Foods (meatpacking) -> `retail_platform`. A second,
  larger sample (20 more accounts, mid-run) surfaced the same pattern
  in different phrasing: CLEAResult Consulting -> `utilities_platform`,
  CRA International (a consulting firm) -> `saas_platform`, PageGroup
  ("recruitment consultancy") -> `saas_platform`, the Defense Contract
  Management Agency -> `logistics_platform`, 3D Systems (a 3D printer
  *manufacturer*) -> `saas_platform`, Corsicana Mattress (a mattress
  *manufacturer*) -> `retail_platform`.

### Guardrails added, all in `validate_classification()`

- `HOUSEKEEPING_MARKERS` in `classification_prepass.py` - skips
  accounts whose own name flags them for deletion (checked BEFORE
  the LLM call, so it also saves cost, not just accuracy).
- `DEFUNCT_FACT_PATTERNS` - past-tense corporate-existence phrasing
  ("was a", "was acquired by", "no longer operates", etc.) forces
  the classification to "none" regardless of what category was
  claimed.
- `NON_FIT_INSTITUTION_KEYWORDS` - broadened twice this session as
  new phrasing patterns were found: universities, law/accounting/
  engineering/architecture firms, consulting firms and consultancies,
  recruitment agencies, government/defense agencies, meatpacking.
  These institution TYPES are treated as never a fit for any tracked
  category, regardless of which one the model picked.
- `CATEGORY_SPECIFIC_MISMATCH_KEYWORDS` - a physical-goods
  manufacturer doesn't fit `saas_platform` (deliberately does NOT
  use a bare "machines" keyword, since that would false-positive on
  legitimate terms like "virtual machines" - uses "3d printing"
  specifically instead) and is questionable for `retail_platform`.
- The classification prompt itself was also updated to instruct the
  model to avoid institution-type mismatches directly, as a
  belt-and-suspenders measure alongside the code-level checks.

`revalidate_classifications.py` re-applies improved validation rules
to already-collected answers with **zero new LLM calls** - lets
guardrail improvements benefit data that was already paid for,
rather than needing a full re-run every time a new mismatch pattern
is found. Confirmed via testing that blocking is monotonic (new
keyword lists are strict supersets of old ones), so re-validation
never accidentally un-blocks something correctly blocked before.

### Known limitations, explicitly not fixed

- Pure fabrication (Pfizer/Microvast) has no code-level fix without
  an external lookup.
- The institution/category mismatch guardrails are a curated,
  evidence-based list, not an exhaustive or principled taxonomy -
  new phrasing patterns will likely keep surfacing and need adding
  as found, the same way this session's list grew from one sample to
  the next.
- Company size/revenue as a separate structured field (asked about,
  not built) was judged to add only modest scoring value (the
  existing `company_context_points` bonus caps at 5/100) compared to
  the scale-tier mechanism actually built, which adjusts the
  dimensions that already drive the bulk of the score.

### Also fixed same day: insurance_platform / pharma_device_platform base ratings

Full-file data (not just a sample) showed Insurance (103 accounts)
and Pharma & Medical Device (32 accounts) at exactly 100% Tier 4,
zero accounts in any higher tier, for either entire vertical. Root
cause, confirmed via the actual scoring formula: their flat rating
(`database_intensity: 2, operational_complexity: 2,
realtime_requirement: 1`) produces a hard ceiling of exactly 40
points - reaching Tier 3 required literally every other bonus
(engineering signal, tech maturity, company size) maxed
simultaneously, an unrealistic combination. Raised both to `(3, 3,
2)`, matching `utilities_platform`'s existing, precedented rating
(not an invented number) - new ceiling 49, with real margin. Verified
via test cases: an account with zero or one positive signal still
correctly stays Tier 4 (34, 39); two positive signals now correctly
cross into Tier 3 (44) where previously the same account would have
scored only 35.

---

## Same-day follow-up: LLM_THRESHOLD recalibration and the second real intelligence run

### Finding: classification-upgraded accounts almost never reached the LLM, despite qualifying by tier

User asked directly: "is there a way to get more accurate scoring."
After the classification pre-pass and scale-tier work above, a check
of how many newly-classified accounts now qualify for the full
intelligence call turned up 0 - despite thousands landing in Tier
2/3. Root cause, found by reading `modules/deterministic_gate.py`
directly rather than guessing: the gate requires `gate_score >= 50`
(`LLM_THRESHOLD`), a HIGHER bar than Tier 3's own `overall_coi >= 40`
(`scoring_engine.py`) - a mismatch that predates this session
entirely (the constant already carried a `# <-- NEEDS
RECALIBRATION` comment with no further note attached). For
classification-pre-pass accounts specifically, `gate_score` is
essentially just `overall_coi` (no keyword-match bonus, since a bare
company name never contains literal strings like "cassandra" or
"mongodb"), and their COI itself is capped low because the pre-pass
never touches `engineering_signal`/`technology_score`/`company_size`
- so they cluster tightly at 40-49, just under the old 50-point gate.

Confirmed via `check_threshold_gap.py`: 3,537 accounts were Tier 3+
by COI; 2,709-3,018 of those (depending on exact threshold/dedup
pass) sat below the gate, unable to ever reach the LLM. Of those,
**210 predate the classification pre-pass and this session
entirely** - a real, pre-existing gap, not something introduced
today. `LLM_THRESHOLD` lowered from 50 to 40 to match Tier 3
exactly. Confirmed safe: `LOW_PRIORITY_TIERS` hard-stops Tier 4
regardless of score, so this change cannot pull in low-quality
accounts - it only affects Tier 1/2/3, which were already meant to
be eligible.

### A real bug found while building the verification scripts

`check_new_llm_candidates.py` and `check_threshold_gap.py` both
initially produced nonsensical results (a `gate_score` distribution
of median 0, min -30, for accounts with `overall_coi >= 40` - a
result that's mathematically impossible under the gate's own
`score = coi + bonuses` formula). Root cause: the scored file already
had `gate_score`/`run_llm` columns from the ORIGINAL `main.py` run.
`pd.concat()` + `columns.duplicated()` keeps the FIRST occurrence
when dropping duplicate column names - meaning the STALE value
survived and the freshly-computed one was silently discarded, in
both scripts. Fixed by dropping any pre-existing gate-result columns
from the loaded dataframe before merging in the fresh computation,
in both scripts. Confirmed via a minimal reproduction before and
after the fix.

### A concurrency-related crash, not a code bug

At the user's request, `MAX_WORKERS` in
`pipeline/llm_validation_pipeline.py` was raised from 5 to 8 for the
new ~3,018-account run. This produced an immediate `zsh: segmentation
fault` right as the thread pool started - not a Python exception,
which points to the underlying `boto3`/SSL networking layer under
concurrency rather than a bug in this codebase's own logic (5
workers has now run cleanly across two full production runs, ~4,200
real accounts combined, with zero crashes). Reverted to 5. Nothing
was lost - the crash occurred before any new completions, so the
checkpoint was untouched and the run resumed cleanly from the same
point.

### Workflow lesson: re-running classification_prepass.py is not the same as revalidating

Mid-session, `classification_prepass.py` (the real, costly script)
was run a second and third time to pick up improved guardrails,
instead of the free `revalidate_classifications.py` built
specifically for that purpose. This cost an additional real ~$3.59
for a run that produced a WORSE (less-filtered) result than the free
revalidation already sitting in the checkpoint, since the fresh run's
own `validate_classification()` call only reflected whatever
guardrail code was on disk AT THAT MOMENT - and overwrote the more
current, already-revalidated checkpoint. Recovered for free by
running `revalidate_classifications.py` again against the newest
data. Documented here as a real, easy-to-make mistake: **only run
`classification_prepass.py` again if the classification PROMPT
itself changes (a genuinely new question to the LLM); if only the
VALIDATION rules changed, `revalidate_classifications.py` gets the
same benefit for free.**

### Files added this stretch

- `check_new_llm_candidates.py` - free, no-LLM-call check of exactly
  how many accounts newly qualify for the full intelligence call,
  beyond whatever is already in `llm_validation_results.xlsx`.
- `check_threshold_gap.py` - free, broader check of the Tier-3-vs-
  LLM_THRESHOLD gap across the whole file, used to find and size the
  recalibration issue above before making the change.
- `run_new_llm_candidates.py` - runs the real, full intelligence call
  for newly-qualifying accounts, reusing `validate_accounts()`
  directly (the same threaded/checkpointed function `main.py` uses)
  so already-validated accounts are automatically skipped at zero
  additional cost.

### Second real intelligence run

3,018 new accounts (2,808 from the classification pre-pass, 210
pre-existing) qualified under the corrected threshold. Real
confirmed cost estimate: ~$5.79 (consistent with the ~$0.72/million
token real Bedrock rate). Run in progress at time of writing;
spot-checked mid-run and showed the same healthy pattern as before -
genuine "I don't recognize this company" conservative scores (Sqrrl
Data LLC, ELOQUII, Wireless Environment LLC all scored 10/100 with
no fabrication attempted) alongside accurate, specific recognized
facts (Servicios Comerciales Amazon Mexico correctly identified as
an Amazon subsidiary, Klarna's "$35 billion in transactions" figure).

---

## July 27: narrative genericness, a prompt-leakage bug, and web search grounding (RAG)

### Quantifying the "vanilla" complaint

The second real run completed: 3,531 total LLM-processed accounts,
$6.80 real cumulative cost. Manual sampling of the output surfaced a
user complaint that responses "look the same" - confirmed directly
rather than dismissed. `quantify_narrative_genericness.py` measured
it precisely: across 2,532 genuinely different, verified accounts,
`couchbase_point_of_view` collapsed into just 102 distinct opening
styles. The top 15 templates covered 81.5% of all accounts, and the
single most common opening alone covered 24.3%. Critically, all 15
top templates shared the identical literal prefix "a distributed
database" - only the adjective that followed varied (availability,
scalability, consistency, flexible data model, throughput). This
ruled out banning individual phrases (a losing, whack-a-mole
approach) in favor of banning the shared structure itself.

### Three prompt-only fixes, in order, each showing the same pattern

1. Banned the specific phrase "a distributed database with high
   availability/high-performance" - model complied, relocated the
   same words to other adjective combinations not yet banned.
2. Broadened to a structural ban on the opening words "A distributed
   database" - model complied literally (technically never started
   with those words) while burying the identical product mention a
   few words into the sentence instead (confirmed: Netspend/UCB
   retest both said "...requires a distributed database that can
   scale horizontally" mid-sentence).
3. This is the same pattern seen throughout this session with every
   purely-instructional fix (score conservatively if unrecognized,
   don't reuse phrasing) - the model reliably satisfies the LETTER of
   a narrow rule while sidestepping its intent. Word-level and
   structure-level prompt constraints only limit the SURFACE of an
   answer; they can't manufacture real content where none exists.

### A schema-level fix: split one field into two, code-validate the whole sentence

Instead of another word ban, `couchbase_point_of_view` was removed
as a model-supplied field entirely. The model must now fill two
SEPARATE required fields: `specific_constraint` (banned, in code,
from containing "database"/"distributed"/"couchbase"/"data
layer"/"data platform" ANYWHERE in the sentence, not just at the
start) and `distributed_solution` (where those terms are expected).
`build_couchbase_pov_from_parts()` in
`modules/sales_intelligence_pipeline.py` constructs the final
`couchbase_point_of_view` field in code from these two parts, so
every existing downstream consumer of that field name keeps working
unchanged. Confirmed via retest: the exact prior failure case
(product name buried mid-sentence) is now caught -
`llm_constraint_violated` correctly flags it, which the old
prefix-only check completely missed.

### A serious bug found while testing the fix: prompt leakage

An early version of the schema-split prompt included a fully-written
"GOOD example" sentence to demonstrate the desired pattern. Testing
against real accounts found the model had copied that example nearly
verbatim onto United Community Bank, presenting fabricated content
as genuine analysis of a real bank - a materially worse failure than
generic templating, since it's confidently specific-sounding and
false. `detect_generic_narrative()` (built for the templating
problem) did not catch this, because it's a different failure mode
entirely - a lesson in itself: a detector built for one measured
problem does not automatically catch an adjacent one. Fixed by
removing the copyable example entirely (replaced with abstract
structural guidance - no complete sentence available to lift whole)
and adding a permanent tripwire, `detect_prompt_leakage()`, checking
for the specific leaked phrases as a safety net. Retest confirmed
zero leakage across the retest accounts, with the schema-level fix's
gains fully retained.

### Even after the schema fix: real content, same skeleton

Retesting across 11 real accounts (banking, healthcare, hospitality,
fintech, credit union) showed `llm_constraint_violated: false`
across the board - the vocabulary-level leak is genuinely fixed.
But laid side by side, every `specific_constraint` sentence still
follows the identical skeleton: "[concurrency word] updates to
[domain noun] during peak [domain] period(s)." The NOUNS are now
genuinely specific and different per account (patient profiles,
mobile key requests, member accounts, trade positions) - real
progress - but the underlying sentence shape is apparently a
structural habit of the model, not something further word-level
constraints can reach. Documented as an accepted limitation rather
than pursued further, given diminishing returns from three
successive prompt-only attempts.

### The actual root cause, and the real fix: give the model real information

User's framing, and the right one: "every fix we've built moves the
compliance goalpost narrower; none of them give the model something
real to say instead." For a large share of accounts, the model
genuinely has nothing beyond a bare company name - no amount of
output-side constraint can manufacture facts that don't exist in
training data. Checked whether the raw Salesforce export had unused
fields that could help first (Website, Revenue, Employee Count) -
confirmed via direct inspection it does not; the export truly only
has Last Activity/Account Owner/Account Name/State/Type/Last
Modified Date, and `Type` is 99% "Prospect Account" with no
differentiating value. This ruled out a cheap fix and confirmed a
real one was needed: Retrieval-Augmented Generation (RAG) - give the
model real, retrieved information instead of asking it to recall
from memory.

### Building the web search integration

`modules/web_search_client.py` calls Serper.dev (a Google Search API
wrapper), reading `SERPER_API_KEY` from an environment variable -
never hardcoded, never logged, never passed through code that might
print it. Fails soft on any error (missing key, network failure,
rate limit, empty results) - returns `None`, falling back to
memory-only generation exactly as before this feature existed.
Tested first standalone (`test_web_search.py`), against a
deliberate mix: a well-known company (Netspend, control case), a
thinly-recognized one (United Community Bank), and three the LLM
had explicitly failed to recognize in real production output (Sqrrl
Data LLC, ELOQUII, Zup IT Innovation). All three previously-blank
accounts got back real, accurate, specific information - confirming
the core hypothesis before any pipeline integration was attempted.

### Two real problems found by actually reading the search results, not just trusting them

1. **Name collision.** United Community Bank's search results
   included a snippet for an entirely different, unrelated small
   Louisiana bank sharing the same generic name. Fixed by passing
   the account's own `Account State/Province (text only)` field
   (present in the raw data, previously unused) into the search
   query to disambiguate - confirmed via direct before/after
   testing: without location, a wrong-bank snippet appears; with
   "Georgia" added, only the correct ~200-location regional bank
   shows up, with MORE specific detail ("top 100 U.S. bank... 200+
   locations across six states") than the model's own memory-based
   fact had ("over 100 branches").
2. **Defunct-detection over-triggering.** The existing
   `DEFUNCT_FACT_PATTERNS` check (built earlier to catch "Tier 3,
   Inc." - genuinely dissolved into CenturyLink) treated bare
   "was acquired by" language as sufficient to mark an account
   defunct. Real acquisition news shows up constantly in search
   results, far more often than the LLM's own memory ever
   volunteered it - Zup Innovation (a real, active subsidiary of
   Itau Unibanco, same situation as Alexion/AstraZeneca) would have
   been incorrectly suppressed. Fixed by splitting into
   `DEFUNCT_STRONG_PATTERNS` (genuinely sufficient alone: "no longer
   exists," "ceased operations," "went out of business," etc.) and
   `DEFUNCT_ACQUISITION_PATTERNS` (ambiguous alone - only treated as
   defunct when co-occurring with `PAST_TENSE_SELF_PATTERNS`, i.e.
   the company describing its OWN nature in the past tense: "Tier 3,
   Inc. WAS a cloud computing company that was acquired..." vs.
   "Alexion IS a biopharmaceutical company... that was acquired...").
   Confirmed via testing all four real cases: the original Tier 3
   Inc bug still caught, Alexion and Zup both correctly excluded,
   and a genuinely-dissolved case (Sqrrl) still correctly caught via
   the strong-pattern path alone.

### Wiring search into the actual pipeline

`build_intelligence_prompt()` gained an optional `web_context`
parameter, inserted right after the ACCOUNT DATA block with explicit
instructions to treat it as more reliable than training-data memory.
`validate_account()` calls `search_company()` before building the
prompt, using the account's state for disambiguation - and, per a
direct question about the 586 accounts (6% of the real file) with no
state on file at all, skips search entirely for those, falling back
to memory-only rather than risking an unfixable mismatch with no way
to catch it (a deliberate, conservative tradeoff: lose the upside for
6% of accounts rather than risk a confidently-wrong grounded answer
for any of them). The account's own location is also now shown
directly in the prompt's ACCOUNT DATA block (previously computed for
the search query but never actually shown to the model), paired with
an explicit instruction to cross-check any search result against it
and flag conflicting results rather than silently picking one.

### Real production evidence the fix works, twice confirmed

Retested against 11 real accounts from the actual production file
(not the small test fixture missing the location column). United
Community Bank correctly identified as the real ~200-location,
$28.2 billion regional bank across GA/NC/TN/SC/FL/AL, in BOTH
appearances in the batch - the location fix and cross-check
instruction both held under real, repeated testing, not a fluke.
Facts across the board got measurably richer: Cleo's founding year
(1976), Staywell's employee count (501-1,000), PeopleAdmin's parent
company (a PowerSchool company) - all real, checkable details that
weren't present in memory-only output. `llm_used_web_search` field
added (visible on the Call Brief as a `\U0001F50D Web-Verified` tag,
alongside the existing `\u26A0 NOT COMPANY-VERIFIED` warning) so a
rep can tell at a glance whether an account's narrative is grounded
in a real, live search result.

### Cost and safety notes

Serper.dev's free tier (2,500 queries, no credit card required) was
used for all testing in this session. Since no payment method is on
file, there is structurally no way to be charged beyond the free
tier - additional calls simply fail cleanly (same as any other
search failure: fall back to memory-only). At full production scale
(3,523 qualified accounts minus ~586 skipped for no location), one
search per qualifying account would use roughly 3,000 queries -
comfortably within a single top-up if the free tier is exhausted.

### Final status of the narrative-quality investigation

Genuinely improved: vocabulary-level genericness (product names
appearing anywhere in the constraint sentence) is fixed and
code-verified, not just prompt-requested. Fact richness is
measurably better with search grounding live. What remains
unresolved and accepted: the underlying sentence-structure
convergence for the constraint field itself, which appears to be a
structural habit of the model rather than something further
word-level prompt engineering can reach - documented as a known
limitation rather than pursued through a fourth round of word bans,
given three consecutive attempts showing the same diminishing
return.

---

## Same-day follow-up: three more substring fixes, and drawing a real line on what gets fixed in code

### Two more real substring-collision bugs found via systematic testing, one gap closed

`KEYWORD_FALSE_POSITIVE_EXCLUSIONS` gained three entries after
testing every short (<=5 char) keyword across the entire pattern
file against a real English word list, not just reacting to the
next bug found by chance: `"api"` (matched inside "Capital" -
confirmed real via KPS Capital Partners, LP getting tagged
`api_platform`/"Technology, SaaS" via `c-API-tal`, the same root
cause as the earlier, never-actually-fixed H.I.G. Capital
Management issue), `"power"` (matched inside "Empower" - a large
real financial services company, not a utility - found
preemptively via the same systematic check, not yet seen in
production), and `"cardiology"` added to the existing `"card"`
entry (closing a gap that was found and documented earlier this
session but never actually added to the exclusion list).

### A random, blind sample check - not bug-hunting, measuring the real rate

At the user's explicit direction ("I don't want to chase isolated
bug fixes... I'm looking to make sure what we're delivering is
predominantly accurate"), pulled two independent random samples of
60 verified accounts each and judged fact-vs-score alignment
directly - a genuinely different exercise from every targeted
spot-check earlier this session. Found and named four distinct
patterns through this process:

- **Outside-knowledge leak** (Epic Games, Detroit Tigers): the
  model describes things about a well-known company that never
  appear in the given fact - not filling a gap with a guess, but
  overriding what's actually stated with background training
  knowledge. Confirmed as a worse variant on Nikon Inc.: the fact
  explicitly states "51-200 employees," and the narrative describes
  "Nikon's large customer base" anyway - contradicting stated
  evidence, not just supplementing thin evidence.
- **Wrong-type-evidence** (KPS Capital Partners, US Air Force
  AFLCMC/LZIA): a real, specific number cited, but one that doesn't
  measure the thing actually being estimated - assets under
  management measures money managed for others, not KPS's own
  systems; headcount doesn't correlate with database workload
  outside businesses where it plausibly does (a distributor,
  confirmed earlier, versus a military command or an investment
  firm).
- **Thin-fact-defaults-upward** (Manta, Cornerstone Information
  Systems, ReviewTrackers): near-zero concrete detail in the fact,
  score still lands in the familiar mid-to-high range regardless -
  the same root disease as the narrative genericness problem,
  confirmed to also affect the score.
- **Genuinely aligned, including correctly-low scores** (Hiller
  Companies, Five Star Senior Living, Museum of Modern Art): real
  or honestly-vague evidence, score genuinely tracks it - including
  cases where a LOW score with specific real reasoning is the
  correct call, not just high scores backed by evidence.

### A discovery-phase regression found in the same review

Reviewing full narrative content (not just facts/scores) surfaced
a partial regression on the Discovery Strategy fix from the prior
session: Phase 4's objective ("Determine whether operational
database architecture is worth discussing further") is a near-
verbatim reconstruction of the exact phrase banned earlier
("Determine whether operational database architecture is becoming
a discussion"). Found in 4 of 5 manually reviewed accounts
(Resorts Casino Hotel, Apollo Retail Specialists, Cardtronics,
Nikon Inc.) - Nestle North America was the one exception, correctly
producing account-specific Phase 4 language. The pattern correlates
with fact richness: accounts with strong specific facts (Cardtronics,
Nestle) show good Phase 1-3 content regardless of Phase 4; accounts
with thin facts show generic language throughout, Phase 4 included.

### The real decision made today: where to stop fixing in code

Every fix that has actually held up this session - the dollar-figure
magnitude floor, defunct-company detection, the revert-unbacked-
increase rule, the three substring exclusions above - worked because
there was a clean, deterministic signal to check: a real number, a
specific phrase, a stored before/after comparison. Explicitly decided
NOT to chase the patterns found in this review (brand-knowledge
override, the Phase 4 regression, thin-fact defaults) with further
narrow code patches, for a specific, principled reason: none of them
have an equivalent clean signal. "Is this describing something from
the given fact or from training knowledge" is a semantic judgment,
not a deterministic check - the same reasoning that already applies
to the accepted pure-fabrication risk (BayMark, Pfizer, Microvast).
Tightening one narrow parameter (e.g. the small-employee threshold,
to catch Nikon's 51-200 range) would only shift the failure to the
next account just outside whatever new boundary is chosen - the same
whack-a-mole dynamic already observed with the "card"/"media"/"energy"
keyword exclusions, just with a fuzzier trigger. Documented explicitly
as accepted, known limitations rather than pursued further.

### Mission-statement alignment check

Re-read the README's Mission section together mid-session: "The COI
score is only a prioritization mechanism. The real goal is seller
intelligence... The LLM never scores or qualifies accounts." Confirmed
via direct code inspection that `llm_total_score` (the independent
score this session invested heavily in correcting) does not appear
anywhere in `build_ae_call_list.py` and does not drive sort order
(`sort_values("overall_coi")` does) - it genuinely isn't shown to reps
today. This reframed the back half of the session: the narrative
content (`engineering_implications`, `couchbase_point_of_view`,
`discovery_progression`) is what the mission's five stated questions
are actually about, and is where review effort shifted accordingly.
