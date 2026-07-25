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
