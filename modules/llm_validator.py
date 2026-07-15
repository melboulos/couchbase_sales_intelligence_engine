import json
from datetime import datetime, timezone

from modules.llm_client import call_llm



# =====================================================
# RUN ID
# =====================================================

LLM_RUN_ID = datetime.now(
    timezone.utc
).strftime(
    "%Y%m%d_%H%M%S"
)



# =====================================================
# JSON EXTRACTION
# =====================================================

def extract_json(text):

    if isinstance(text, dict):
        return text


    text = str(text)

    text = (
        text
        .replace("：", ":")
        .replace("\r", "")
    )


    start = text.find("{")
    end = text.rfind("}")


    if start == -1 or end == -1:

        raise ValueError(
            "No JSON found"
        )


    return json.loads(
        text[start:end+1]
    )



# =====================================================
# PROMPT
# =====================================================

def build_prompt(row):


    return f"""

You are an independent Couchbase enterprise sales analyst.

You are reviewing an automated Couchbase Opportunity Index (COI).

DO NOT simply agree with COI.

Your job:
Determine whether the account deserves the current ranking.


Analyze:

1. Workload Fit (40%)

Look for:

- operational database workloads
- real-time applications
- customer-facing applications
- API platforms
- transactional systems
- distributed data challenges


2. Evidence Quality (25%)

Strong evidence:

- database signals
- technology platforms
- engineering complexity
- application architecture


Weak evidence:

- industry alone
- company size alone
- generic AI interest


3. Technical Alignment (20%)

Evaluate:

- modernization opportunity
- NoSQL/document fit
- cloud-native applications


4. Business Opportunity (15%)

Evaluate:

- strategic importance
- adoption likelihood



ACCOUNT

Name:
{row.get("Account Name","")}


CURRENT COI:

{row.get("overall_coi",0)}


Priority Tier:

{row.get("priority_tier","Unknown")}


Industry:

{row.get("industry","Unknown")}


Business Model:

{row.get("business_model","Unknown")}


Company Signal:

{row.get("company_signal_score",0)}


Technology Score:

{row.get("technology_score",0)}


Technology Signals:

{row.get("technology_signals","Unknown")}


Database Signal:

{row.get("database_signal","Unknown")}


AI Signal:

{row.get("ai_signal","Unknown")}


Workloads:

{row.get("workloads","Unknown")}



Return ONLY JSON.


Format:


{{
"llm_score":0,

"validated":true,

"confidence":"High",

"couchbase_fit":"Strong",

"priority_recommendation":
"Keep Tier 1",

"delta_explanation":
"Explain why LLM score differs from COI",

"strongest_signals":
[
"signal"
],

"weakest_assumptions":
[
"assumption"
],

"reasoning":
[
"reason"
],

"recommended_sales_motion":
"action"

}}

"""



# =====================================================
# VALIDATE ACCOUNT
# =====================================================

def validate_account(row):


    try:


        response = call_llm(
            build_prompt(row)
        )


        result = extract_json(
            response["text"]
        )


        llm_score = int(
            result.get(
                "llm_score",
                0
            )
        )


        coi = int(
            row.get(
                "overall_coi",
                0
            )
        )


        return {


            "llm_run_id":
                LLM_RUN_ID,


            "derived_coi":
                coi,


            "llm_score":
                llm_score,


            "llm_score_difference":
                llm_score - coi,


            "llm_confidence":
                result.get(
                    "confidence",
                    ""
                ),


            "llm_couchbase_fit":
                result.get(
                    "couchbase_fit",
                    ""
                ),


            "llm_priority_recommendation":
                result.get(
                    "priority_recommendation",
                    ""
                ),


            "llm_delta_explanation":
                result.get(
                    "delta_explanation",
                    ""
                ),


            "llm_strongest_signals":
                result.get(
                    "strongest_signals",
                    []
                ),


            "llm_weakest_assumptions":
                result.get(
                    "weakest_assumptions",
                    []
                ),


            "llm_reasoning":
                result.get(
                    "reasoning",
                    []
                ),


            "llm_recommended_action":
                result.get(
                    "recommended_sales_motion",
                    ""
                ),


            "llm_input_tokens":
                response.get(
                    "input_tokens",
                    0
                ),


            "llm_output_tokens":
                response.get(
                    "output_tokens",
                    0
                ),


            "llm_total_tokens":
                response.get(
                    "total_tokens",
                    0
                ),


            "llm_model":
                response.get(
                    "model_id",
                    ""
                )

        }



    except Exception as e:


        return {


            "llm_run_id":
                LLM_RUN_ID,


            "llm_score":
                None,


            "derived_coi":
                row.get(
                    "overall_coi",
                    0
                ),


            "llm_score_difference":
                None,


            "llm_validation":
                False,


            "llm_reasoning":
                str(e),


            "llm_input_tokens":
                0,


            "llm_output_tokens":
                0,


            "llm_total_tokens":
                0

        }
