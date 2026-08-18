# Couchbase Sales Intelligence Platform (SIP) — Technical Specification

**This is a current-state reference, not a history.** For the
chronological log of individual fixes, discoveries, and decisions
(including *why* things are built the way they are), see
`OUTSTANDING_ITEMS_AND_PREFERENCES.md`. This document describes what
the system does today, as of 2026-08-18.

---

## 1. Purpose

SIP takes a raw account list (typically a Salesforce report export)
and produces a scored, prioritized call list for a sales rep — for
each account, two independent signals (a deterministic rules-based
score and an AI-generated technical assessment), a specific grounded
fact about the company, discovery questions, and a recommended first
contact.

---

## 2. Pipeline Architecture

Run via `main.py --input <file>`, in this order:

1. **`pipeline/loader.py` → `load_accounts()`** — reads the raw file.
   Auto-detects report-metadata rows (title/timestamp/"Filtered By"
   sections some Salesforce exports include above the real header) by
   scanning for the row containing `"Account Name"`, rather than
   assuming the header is always row 1. Warns (does not fail) if
   `CB Account Number` or `ID (Long)` are missing.

2. **`pipeline/enrichment_pipeline.py` → `normalize_accounts()`** —
   adds a normalized version of the account name for matching.

3. **`classify_industries()`** — first-pass industry classification
   via `modules/industry_classifier.py`.

4. **`enrich_company_intelligence()`** — calls
   `modules/company_intelligence.py`'s `analyze_company()` per
   account (name matching against `KNOWN_COMPANIES`, then keyword
   matching against `BUSINESS_PATTERNS` from
   `data/company_patterns.json`, using web-search snippets as a
   fallback when the account name alone doesn't match). Sets
   `industry`, `business_model`, `workload_profile`,
   `database_intensity`, `operational_complexity`,
   `realtime_requirement`, `workloads` (the actual list of named
   workloads, e.g. "Point of Sale", "Inventory Management" for
   `retail_platform`).

   **Three-tier industry override, in priority order:**
   1. Real Salesforce `Industry` field, when present and non-blank —
      always wins.
   2. SIC Code fallback (see §4) — only when industry is still
      `"Unknown"` after keyword matching.
   3. Keyword-matched classification (steps 3-4 above) — the
      baseline.

   Verbose real Salesforce industry labels are shortened for display
   afterward (e.g. "Customer Relationship Management (CRM) Software"
   → "CRM Software") via a small mapping.

5. **`pipeline/technology_pipeline.py` → `enrich_technology()`** —
   technology/database signal detection from web-search text.

6. **`pipeline/account_enrichment_pipeline.py` → `enrich_accounts()`**
   — `modules/account_enrichment.py`'s `enrich_account()`. Sets
   `company_size` ("Enterprise" or default) and `revenue_signal`
   ("High"/"Medium"/default). Real Employees/Annual Revenue data
   takes priority when present, falling back to an
   industry-list/name-keyword heuristic otherwise.

7. **`pipeline/account_pipeline.py` → `enrich_account_intelligence()`**
   — additional account-level intelligence enrichment.

8. **`pipeline/company_archetype_pipeline.py` →
   `enrich_company_archetypes()`** — company archetype
   classification.

9. **`pipeline/scoring_pipeline.py` → `score_accounts()`** — computes
   `overall_coi` (see §5) via `modules/scoring_engine.py`.

10. **`modules/deterministic_gate.py` → `deterministic_gate()`** —
    decides which accounts qualify for the LLM step (`run_llm` flag),
    based on `overall_coi` clearing `LLM_THRESHOLD` (40).

11. **`pipeline/llm_validation_pipeline.py` → `validate_accounts()`**
    — the expensive step. For each `run_llm=True` account not already
    in the shared checkpoint (`output/llm_validation_results.xlsx`,
    keyed by Account Name, genuinely cumulative across every dataset
    ever run), calls Bedrock (Llama 3 70B) via
    `modules/llm_prompt_builder.py`'s prompt, producing
    `llm_total_score` and the account-specific narrative content (see
    §6).

12. **`pipeline/intelligence_export_pipeline.py` →
    `export_account_intelligence()`** — writes the scored file and
    JSON intelligence export.

13. **`build_ae_call_list.py --input <scored file>`** — separate
    script, builds the final `AE_Call_List.xlsx` report (see §7).

---

## 3. Real Salesforce Fields — What Each One Actually Does

Not every export includes every field below; each one is used only
when present.

| Field | Used for |
|---|---|
| `Account Name` | Identity/matching key throughout the entire pipeline; the checkpoint's join key |
| `Type` (Customer/Prospect Account) | **Not currently used anywhere** - present in every export, no scoring or grounding impact yet |
| `ICP Grade (Text)` | Displayed on the Overview tab only (ICP Grade column) - not used in COI or LLM scoring |
| `Account Owner` | Displayed on the Overview/SIP tabs (rep attribution) |
| `Account State/Province` (or `... (text only)`) | Feeds the web-search query for disambiguation (e.g. distinguishing two same-named companies). Both naming conventions are checked - different Salesforce exports use different ones |
| `Industry` | Highest-priority industry classification signal (§2, step 4) |
| `SIC Code` | Third-tier industry fallback, only when Industry is blank and keyword-matching also failed (§4) |
| `Ownership` (Public/Private) | Fed into the LLM prompt as context only - does not affect COI scoring or industry classification |
| `Annual Revenue` / `Annual Revenue (converted)` | Drives `company_size` (Enterprise threshold: ≥$1B) and `revenue_signal` (High: ≥$1B, Medium: ≥$10M) - real data takes priority over the old industry/keyword heuristic |
| `Employees` | Drives `company_size` (Enterprise threshold: ≥1,000 employees) |
| `Email Domain` | **Not currently used** - present in exports with Employees/Revenue, no grounding or matching use yet |
| `Parent Account ID` | **Not currently used** - no subsidiary/parent-context reasoning built yet |
| `Ticker Symbol` | **Not currently used** - confirms public-company status but nothing reads it yet |
| `LinkedIn Company Id` / `ZI Company ID` (ZoomInfo) | **Not currently used** - would require a real API integration to be useful |
| `Account ID` / `CB Account Number` | Displayed as "Account ID" on the Overview tab (hidden column) - NOT the same identifier across all export types; confirmed not to correspond to a real Salesforce record ID in every case |
| `ID (Long)` | The genuine 18-character Salesforce record ID - displayed as "Salesforce ID" (hidden column), intended for a downstream integration to join against |
| `Netsuite Id`, `Customer Profile Id` | **Not currently used** |

---

## 4. Industry & Business Classification

**Pattern matching** (`data/company_patterns.json`): a dict of named
business patterns (FinTech, Healthcare Technology, SaaS, Retail,
etc.), each with a keyword list and a mapped `industry`,
`business_model`, and `workload_profile`. Matched in dict order via
substring search against the account name or web-search snippets - **order
matters**: more specific patterns must be listed before more generic
ones that might also match the same text (e.g. "Ad Exchange /
Real-Time Advertising Platform" is checked before the generic
"Media/Advertising", so a real ad-tech exchange company isn't lumped
in with general media companies).

**Known false-positive protections** (`KEYWORD_FALSE_POSITIVE_EXCLUSIONS`
in `modules/company_intelligence.py`): per-keyword exclusion lists for
bare single-word keywords prone to substring collisions -
`"care"` excludes `"career"`, `"card"` excludes `"cardinal"`,
`"cardiology"`, `"cardiac"`, `"piccard"`, `"appcard"`, etc. `"power"`
uses a separate co-occurrence requirement instead of a simple
exclusion list (must appear near a genuine utility term). This list
is built incrementally as real false positives are discovered against
live data - **not exhaustive**; any bare single-word keyword not yet
audited could have the same class of risk.

**SIC Code mapping** (`SIC_TO_INDUSTRY` in `pipeline/enrichment_pipeline.py`):
a hand-built map covering SIC codes actually observed in real data so
far. Not a complete SIC reference - unmapped codes simply don't
trigger the fallback (no guessing).

**Workload profiles** (`workload_profiles` in the same JSON file):
independent of business patterns - describe the technical
characteristics (`database_intensity`, `operational_complexity`,
`realtime_requirement`, each roughly 1-5) and named `workloads` list
used for keyword-matching in COI's workload-fit scoring. Ratings vary
meaningfully by profile - `payment_platform` and
`adtech_realtime_platform` are rated 5/5/5 (maximum), `media_platform`
is rated 3/3/3, reflecting genuinely different technical intensity
expectations. **Any workload_profile not yet audited against real
account outcomes could have similarly miscalibrated ratings** -
`media_platform` was found under-scored via direct evidence
(confirmed against 59 real accounts across multiple datasets); this
process has not been repeated for every other profile.

---

## 5. Scoring Methodology

**COI (Couchbase Opportunity Index)** - deterministic, `modules/scoring_engine.py`,
0-100, five components:

| Component | Max points | Basis |
|---|---|---|
| Operational Workload Fit | 40 | Keyword matches in `workload_text` (joined from the account's `workloads` list) + a flat +10 bonus for having any structured workload_profile at all |
| Database Opportunity | 30 | Derived from `database_intensity` |
| Real-Time Requirement | 15 | Derived from `realtime_requirement` |
| Technical Environment | 10 | Engineering capability / technology maturity signals |
| Company Context | 5 | Binary: 5 points if `company_size == "Enterprise"`, else 0 |

**LLM Score** - AI-generated, independent, 0-100, three components
(via the Bedrock prompt in `modules/llm_prompt_builder.py`):
workload fit (0-40), real-time requirement (0-30), technical
complexity (0-30). Deliberately a different weighting than COI, not
meant to mirror it - genuine disagreement between the two is expected
and informative, not a bug. A large-scale override
(`apply_magnitude_based_score_adjustment` in
`modules/sales_intelligence_pipeline.py`) can force these three
sub-scores to a fixed floor (35/27/25, summing to 87) when a
genuine ≥$1B dollar figure (revenue, assets, or transaction volume -
requires either a literal `$` sign or a dollar-context word nearby,
not just any large number) is found in the account's generated text.

**Correlation between COI and LLM score is real and expected to be
low** (~0.27-0.32 measured across multiple real samples) - they are
designed to be independent, not redundant.

---

## 6. LLM Validation & Grounding

Each qualifying account gets one Bedrock call. The prompt includes:
Account Name, Industry, Business Model, Observed Workloads, Database
Signal, Cloud Signal, Engineering Signal, Revenue Signal, Ownership,
AI Signal - real search-derived facts where available, `"Unknown"`
otherwise.

**Grounding**: `serper_enrichment_pass.py` runs web searches per
account, cached in `output/serper_search_cache.xlsx` (genuinely
cumulative across every dataset ever processed, keyed by Account
Name - never re-searches an already-cached name). The LLM prompt
includes this real search text when available; `llm_used_web_search`
records whether a given account's response actually drew on it.

**Validation checks applied to the LLM's raw output** (in
`modules/sales_intelligence_pipeline.py`):
- `enforce_company_recognition_cap` - caps unverified-recognition
  scores
- `detect_ungrounded_score` - flags scores with no real evidence
  behind them
- `apply_magnitude_based_score_adjustment` - the large/small-scale
  floor/ceiling described in §5
- `llm_score_is_default` - the final flag distinguishing a genuinely
  evidence-backed score from a default fallback

**Not every generated result is accepted** - a separate check can
reject a result outright if its stated technical reasoning leans on
generic prominence language ("industry leader") rather than concrete
technical evidence, even if the model otherwise produced real content
(confirmed real case: Rollins, Inc. - real fact and reasoning
generated, still rejected for this reason).

---

## 7. Report Output (`build_ae_call_list.py`)

Produces `AE_Call_List.xlsx` with four sheets:

- **Sales Intelligence Platform** (first sheet) - splash banner, a
  "HOW TO READ THE SIP SCORES" guide (ICP/COI/LLM/SIP definitions,
  positioned beside the logo), Top 20 accounts table with
  recommended first contact (see below), a Tier Distribution pie
  chart.
- **Full Landscape** - industry-level summary table (top 15
  industries by count) with conditional-formatting color scales
  (red=low, green=high) and a pie chart of Tier 1 accounts by
  industry (chosen after bar/column chart category-label rendering
  could not be resolved - see the chronological log for the full
  debugging history).
- **Overview** - one row per qualifying account: Account Name, COI
  Score, ICP Grade, Priority Tier, Industry, Account Owner, Account
  ID, Salesforce ID (last two columns hidden by default). Headers and
  body cells centered; Non-Target ICP grades highlighted. The score
  guide also appears here, positioned beside the data (column J
  onward) rather than above it.
- **Call Briefs** - one detailed page per qualifying account: the
  LLM-generated fact, point of view, discovery questions, technical
  risks, missing information, with Web-Verified/Not-Verified markers.

**Recommended First Contact**: a two-tier lookup -
`(workload_profile, industry)` specific overrides checked first
(e.g. `("payment_platform", "Auctions")` → "VP of Trust & Safety /
Head of Fraud Prevention"), falling back to a broader
workload_profile-only mapping. Not exhaustive - any
(workload_profile, industry) pair not explicitly covered falls back
to the generic per-workload suggestion.

---

## 8. Known Limitations (as of this writing)

- SIC Code mapping table is not exhaustive and has not been
  independently verified entry-by-entry against an official SIC
  reference (one error already caught and removed: 679).
- Several real Salesforce fields are read into the pipeline but not
  yet used for anything (Type, Email Domain, Parent Account ID,
  Ticker Symbol, LinkedIn/ZoomInfo IDs) - see §3.
- Only `media_platform`'s ratings have been directly audited against
  real outcome data; other workload_profiles have not received the
  same scrutiny.
- Only one bare single-word keyword (`card`) has been found to have
  an unguarded substring risk via real-world discovery; the full
  keyword list has not been proactively audited for others.
- Enterprise East and the original 9,758-account file have not been
  re-scored with the fixes built after they were last run (real
  Industry override, SIC Code, Ownership, the Ad Exchange pattern,
  the `card` exclusion) - their current scored output reflects an
  older version of the classification logic.
- Tier 1 representativeness (are the accounts landing in Tier 1
  actually the right ones) has been flagged as worth checking but not
  yet directly audited.
