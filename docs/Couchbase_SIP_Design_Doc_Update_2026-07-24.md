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
