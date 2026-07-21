# Couchbase Sales Intelligence Engine (SIP)
## Design Status Update — July 20, 2026

---

## Mission

Help Couchbase sales reps identify the right accounts to call, have more meaningful technical discovery conversations, shorten sales cycles, and prioritize accounts with strong Couchbase opportunity signals.

The product is not just an account scoring system. The COI score is only a prioritization mechanism. The real mission is to deliver seller intelligence:

- Which accounts should I call?
- Why should I call them now?
- What evidence suggests there is a Couchbase opportunity?
- Who should I engage?
- What workloads and technical challenges should I explore?
- What discovery questions will create a valuable conversation?

**North star:** increase seller productivity and improve conversation quality by turning account signals into actionable technical sales intelligence.

---

## Architecture (Current)

```
Salesforce Account List
        |
        v
Normalization
        |
        v
Industry Classification
        |
        v
Company Intelligence
  (company_patterns.json match:
   known_companies -> business_patterns
   -> workload_profiles join)
        |
        v
Technology Enrichment
        |
        v
Account Intelligence / Account Enrichment
        |
        v
Company Archetype Classification
        |
        v
COI Scoring Engine
  (scoring_engine.py — workload fit,
   database opportunity, real-time
   requirement, technical environment,
   company context)
        |
        v
Deterministic Gate
  (gate_score = overall_coi, +/- adjustments
   for database tech / modernization /
   cloud / negative signals; requires
   workload_profile to be set)
        |
        +---------------+
        |               |
        v               v
     SKIP        LLM Intelligence Generation
                        |
                        v
                 LLM Output Validation
                        |
                        v
              Merge back into full dataset
                        |
                        v
         Excel export + Streamlit JSON export
                        |
                        v
              app.py (Streamlit dashboard)
```

---

## Core Philosophy (Unchanged, Reaffirmed This Session)

- The deterministic pipeline qualifies accounts. COI is the single source of truth for "is this account worth calling."
- The LLM never qualifies or scores accounts. It generates seller intelligence: workload interpretation, engineering implications, a Couchbase point of view, technical risks, conversation strategy, discovery questions, and known gaps.
- The LLM's stated persona: a Senior Couchbase Solutions Engineer sitting beside the AE — not a scoring system.
- Every score must be explainable. Every hallucination must be rejected, not tolerated.

---

## Key Changes Made This Session

### 1. LLM contract — removed scoring from the LLM entirely
`seller_value_score` was present in the LLM's return schema with no supporting prompt guidance, producing an unguided, unexplained number that risked being read as a second, competing qualification signal alongside COI. Removed from:
- `llm_prompt_builder.py` schema
- `sales_intelligence_pipeline.py` `REQUIRED_FIELDS` and `validate_score()`

The LLM contract is now purely qualitative: `why_this_workload_matters`, `engineering_implications`, `couchbase_point_of_view`, `technical_risks_to_validate`, `conversation_strategy`, `discovery_progression`, `missing_information`.

### 2. `couchbase_fit_reason` retired
Previously hardcoded per `known_companies` entry — duplicated what the LLM's `couchbase_point_of_view` already does. Removed from `company_intelligence.py` and all 7 `known_companies` entries in `company_patterns.json`.

### 3. Fixed the `workload_profile` → `workload_profiles` join (root cause of dataset-wide zero scores)
`company_intelligence.py` was reading `database_intensity` / `operational_complexity` / `realtime_requirement` directly off the matched pattern entry, but those values actually lived in a separate `workload_profiles` lookup table, referenced only by a pointer string. The join was never implemented. This caused **100% of the 6,701-account dataset** to show `database_intensity = 0`, `operational_complexity = 0`, `realtime_requirement = 0`, `workload_strength = "Unknown"` — regardless of which pattern matched.

Fixed via `apply_workload_profile()`, which joins the pointer to `workload_profiles` and derives a High/Medium/Low `workload_strength` label from the sub-signal average. `known_companies` inline values still take precedence when present.

Also discovered and fixed: `workload_profile` itself (a field `scoring_engine.py` was designed to read for a +10 COI bonus) was never being written to the row at all — a second, independent gap in the same area.

### 4. COI-based, unified deterministic gate
Previously, `deterministic_gate.py` computed `gate_score` from its own independent keyword system (`WORKLOAD_CATEGORIES`), completely disconnected from `scoring_engine.py`'s COI calculation — the two could and did disagree (e.g., COI 66 but gate_score 40, causing a Tier 2 account to be skipped).

Rebuilt so `gate_score` starts from `overall_coi` directly, with additive adjustments only for signals COI doesn't already capture: existing database technology mentions, modernization language, cloud-native signals, and negative signals (consulting, staff augmentation, etc.). Qualifying workload evidence is now based on `workload_profile` being set, not a second independent keyword search.

### 5. Expanded `company_patterns.json` coverage — five new business patterns
Prior to this session, only 4 business patterns existed (FinTech, Healthcare Technology, SaaS, API Platform), covering a small fraction of the account base. Added, based on real name-pattern analysis of the ~6,700-account book:

| Pattern | Database Intensity | Operational Complexity | Realtime Requirement |
|---|---|---|---|
| Retail (incl. restaurants — POS-driven) | 4 | 3 | 3 |
| Logistics/Transportation | 3 | 4 | 3 |
| Utilities | 3 | 3 | 2 |
| Media/Advertising | 3 | 3 | 3 |
| Insurance | 2 | 2 | 1 |

### 6. Non-buyer exclusions
Per explicit direction that Couchbase does not sell to these segments regardless of technical fit:
- Banks, credit unions, investment firms — never matched by `FinTech` (kept narrowly scoped to payments/transaction companies only).
- Hospitals, health systems, clinics, home care, hospice, senior living — excluded via a dedicated `is_excluded_provider()` check in `company_intelligence.py`, applied only to the business-pattern matching path (never overrides `known_companies` entries like Redox/Staywell).
- Pharma manufacturers, medical device makers, pharmacy operations — split out of `Healthcare Technology` into a new low-scored `Pharma/Medical Device` pattern (same scoring as Insurance: real interest, low priority), since they are a different business model than health-tech vendors.

This also fixed a real contamination problem: prior to the exclusion, ~69% of `Healthcare Technology` matches were hospitals/health systems, inflating COI and LLM-routing counts with non-buyer accounts.

### 7. `main.py` — removed the hardcoded top-10 LLM cap
The entire gate-rebuild effort (#4) was, until this fix, never actually exercised in production. `main.py` selected LLM candidates via `.sort_values("overall_coi").head(LLM_TEST_LIMIT)` with `LLM_TEST_LIMIT = 10` — a leftover test constant that bypassed the deterministic gate entirely. Replaced with a real call to `deterministic_gate()` across the full account set, filtered to `run_llm == True`.

Result: LLM-routed accounts went from a hardcoded 10 → 480 (pre-exclusion fixes) → **351** (current, post-exclusion, trusted baseline).

### 8. Fixed the LLM merge/export chain (old schema was silently discarding all new LLM output)
`main.py`'s `llm_merge_columns` and `pipeline/intelligence_export_pipeline.py`'s JSON export both still referenced the **old, retired LLM schema** (`llm_opportunity_score`, `coi_assessment`, `coi_delta_reason`, `opportunity_summary`, `couchbase_trigger`, `evidence_found`, `missing_evidence`, `database_replacement_probability`, `seller_action`, `discovery_questions` as a flat list). Since none of these fields exist in current LLM output, **every account's real seller intelligence was being silently dropped** before reaching `Enterprise_East_Scored.xlsx` or the Streamlit dashboard — even after all upstream fixes.

Both files rewritten to use the current seven-field contract. `app.py`'s "AI Sales Assistant" section (which read non-existent `reasoning`/`recommended_action` keys) rewritten to display the real fields: why this workload matters, engineering implications, Couchbase point of view, technical risks, conversation strategy, discovery progression, missing information.

### 9. Dead code removal
- `modules/llm_candidate_selector.py` — a fourth, independent qualification system whose output was computed but never actually used to filter anything. Deleted.
- `pipeline/enrichment_pipeline.py` — removed an unused duplicate `select_llm_candidates()` function and its local `LLM_TEST_LIMIT`, and a broken, never-called `generate_account_intelligence_json()` (referenced an unimported function, would have raised `NameError` if ever invoked).
- `modules/sales_brief_generator.py` — deleted. Independently hardcoded vendor names as "likely databases" per industry (e.g., "Oracle, SQL Server" for all Financial Services accounts) — a direct contradiction of the fact-protection rules built everywhere else in the system. Also duplicated priority tiering and discovery questions in a third, non-LLM, templated form.

### 10. Validator gap fix
`validate_llm_value()` only matched the literal phrase `"understand their needs"`; a real LLM response used the gerund form `"understanding their needs"` and passed undetected. Expanded to catch verb-tense variants.

### 11. Prompt rewrite for generic/repeated output (in progress — pending re-test)
`engineering_implications` and `couchbase_point_of_view` were found, repeatedly and reproducibly (confirmed across multiple independent test runs), to reproduce the prompt's own illustrative example bullets nearly verbatim rather than reasoning about the specific account — most persistently on Paytronix Systems. Root cause: the prompt's example lists were being used by the model as answers to copy rather than illustrations of reasoning style.

Rewrote the "ENGINEERING INTERPRETATION" and "COUCHBASE POINT OF VIEW" sections of `llm_prompt_builder.py` to remove all example bullets and instead require explicit per-workload reasoning, tied to the account's specific `database_intensity` / `operational_complexity` / `realtime_requirement` values, with an explicit instruction not to reuse phrasing across accounts. **Not yet confirmed fixed — pending re-run.**

---

## Current State Summary

| Item | Status |
|---|---|
| LLM contract — no scoring, qualitative only | Done |
| `couchbase_fit_reason` retired | Done |
| `workload_profile` → `workload_profiles` join | Done |
| COI-based unified gate | Done |
| 5 new business patterns (Retail, Logistics, Utilities, Media, Insurance) | Done |
| Non-buyer exclusions (banks, hospitals, pharma split) | Done |
| `main.py` top-10 cap removed, real gate wired in | Done |
| LLM merge/export chain fixed (old schema → current schema) | Done |
| `app.py` dashboard fixed to display real fields | Done |
| Dead code removed (4 files/functions) | Done |
| Validator verb-tense gap | Done |
| Prompt rewrite for generic/repeated output | **Pending re-test** |
| Full 351-account production run | **Not yet executed** |

---

## Immediate Next Steps

1. Re-run the smoke test (`test_llm_validation.py`) against the rewritten prompt, with specific attention to Paytronix Systems — the account that has failed the "generic/repeated output" check three times previously.
2. If clean, run the full pipeline (`main.py`) against all 6,701 accounts, producing a fresh `Enterprise_East_Scored.xlsx` and `account_intelligence.json` with the ~351-account LLM-routed set.
3. Spot-check a sample of the 351 for output quality against the SIP mission criteria: is the workload hypothesis believable, is the Couchbase point of view useful, are engineering implications technically correct and account-specific, is anything generic or hallucinated.
4. Revisit `LLM_THRESHOLD` calibration only if the 351-account figure proves too small or too large in practice — current recommendation is to treat this as a trustworthy, clean baseline rather than force a match to a round target number.
