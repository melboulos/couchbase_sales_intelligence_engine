# Couchbase Sales Intelligence Engine

A sales intelligence pipeline that scores Salesforce accounts for genuine Couchbase technical fit, then uses an LLM to generate account-specific discovery prep for qualifying accounts — helping AEs identify who to call, why, and what to ask.

## Mission

The COI (Couchbase Opportunity Index) score is only a prioritization mechanism. The real goal is seller intelligence:

- Which accounts should I call?
- Why should I call them now?
- What evidence suggests a genuine Couchbase opportunity?
- What workloads and technical challenges should I explore?
- What discovery questions will create a valuable conversation?

The deterministic pipeline decides *which* accounts qualify. The LLM never scores or qualifies accounts — it generates qualitative seller intelligence for accounts the deterministic engine has already selected.

## Architecture

```
Salesforce Account List
        |
        v
Normalization -> Industry Classification -> Company Intelligence
(matches against data/company_patterns.json: known_companies ->
 business_patterns -> workload_profiles join)
        |
        v
Technology Enrichment -> Account Intelligence -> Company Archetype
        |
        v
COI Scoring Engine (modules/scoring_engine.py)
  workload fit, database opportunity, real-time requirement,
  technical environment, company context
        |
        v
Deterministic Gate (modules/deterministic_gate.py)
  gate_score = overall_coi + adjustments for database tech /
  modernization / cloud / negative signals
        |
   +---------+---------+
   |                   |
  SKIP        LLM Intelligence Generation
                       |
                       v
              LLM Output Validation
                       |
                       v
          Merge back (validated accounts only)
                       |
                       v
     Excel export + Streamlit JSON export
```

## Setup

```bash
git clone https://github.com/melboulos/couchbase_sales_intelligence_engine.git
cd couchbase_sales_intelligence_engine
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**AWS credentials** — the pipeline calls Amazon Bedrock (`meta.llama3-70b-instruct-v1:0`) via `boto3`. Configure credentials with access to Bedrock in your environment (`aws configure`, environment variables, or an assumed role) before running `main.py`.

**Input data** — `input/` is gitignored, since account lists typically contain sensitive customer data. Place your own Salesforce account export at `input/Enterprise_East_Account_List.xlsx` (or update `INPUT_FILE` in `main.py` to point elsewhere). Expected columns include at minimum `Account Name`.

## Running

**Full pipeline** — scores every account, applies the deterministic gate, and sends qualifying accounts to the LLM:
```bash
python main.py
```
⚠️ **This calls Bedrock and costs real money.** A recent full run against ~6,700 accounts routed 350 to the LLM at ~1,336 tokens/account average, totaling ~$463. Cost scales with how many accounts clear the gate — check `LLM_THRESHOLD` in `modules/deterministic_gate.py` before running against a new dataset.

**Smoke test** — re-runs enrichment, scoring, and the LLM against a small hardcoded set of accounts, without needing a full run first:
```bash
python test_llm_validation.py
```

**AE call list export** — builds a clean, formatted Excel file (Summary with industry heat map, Overview, per-account Call Briefs) from the output of `main.py`:
```bash
python build_ae_call_list.py
```

**Dashboard**:
```bash
streamlit run app.py
```

## Re-running failed/flagged accounts

`pipeline/llm_validation_pipeline.py` checks `output/llm_validation_results.xlsx` on each run. Accounts already marked `llm_validation == True` are kept as-is; anything `False` or missing is (re)sent to the LLM. To force a specific account to re-run, open that file, set its `llm_validation` cell to `FALSE`, save, and re-run `main.py` — only that account gets reprocessed.

## Output files (all in `output/`, gitignored)

| File | Contents |
|---|---|
| `Enterprise_East_Scored.xlsx` | Full account list with COI, tier, and validated LLM intelligence merged in |
| `account_intelligence.json` | Same data, shaped for the Streamlit dashboard |
| `AE_Call_List.xlsx` | Formatted deliverable for AEs — Summary, Overview, Call Briefs |
| `LLM_Validated_Accounts.xlsx` | Full unfiltered LLM output, including failed/unvalidated rows and error messages |
| `llm_validation_results.xlsx` | Checkpoint file used for the per-row re-run logic above |
| `llm_token_summary.xlsx` | Token counts and cost for the most recent LLM run |

## Project structure

```
main.py                  # Full pipeline entry point
app.py                   # Streamlit dashboard
build_ae_call_list.py    # AE-facing Excel export
test_llm_validation.py   # Smoke test on a small account set
config.py

data/                    # Pattern/rule data (company_patterns.json, etc.)
modules/                 # Core logic: enrichment, scoring, gate, LLM prompt/validation
pipeline/                # Orchestration wrappers called by main.py
schemas/                 # Output schema definitions
docs/                    # Design docs
```

## Data sensitivity

`input/` and `output/` are both gitignored. Do not commit real account/customer data to this repository.
