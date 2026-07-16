from modules.llm_client import call_llm

from modules.llm_json_parser import extract_json

from modules.llm_prompt_builder import build_prompt

from modules.llm_utils import (
    LLM_RUN_ID,
    get_usage_value,
    get_model_name
)


# =====================================================
# VALIDATE ACCOUNT
# =====================================================

def validate_account(row):

    response = None

    try:

        response = call_llm(
            build_prompt(row)
        )


        raw_text = response.get(
            "text",
            ""
        )


        result = extract_json(
            raw_text
        )


        if "llm_score" not in result:

            raise ValueError(
                "LLM returned JSON but missing llm_score"
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


            "llm_validation":
                True,


            "llm_qualification_bucket":
                result.get(
                    "qualification_bucket",
                    ""
                ),


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


            "llm_evidence_strength":
                result.get(
                    "evidence_strength",
                    ""
                ),


            "llm_database_replacement_signal":
                result.get(
                    "database_replacement_signal",
                    ""
                ),


            "llm_technical_risk":
                result.get(
                    "technical_risk",
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


            "llm_score_blockers":
                result.get(
                    "score_blockers",
                    []
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


            "llm_required_discovery_questions":
                result.get(
                    "required_discovery_questions",
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
                get_usage_value(
                    response,
                    "input_tokens"
                ),


            "llm_output_tokens":
                get_usage_value(
                    response,
                    "output_tokens"
                ),


            "llm_total_tokens":
                get_usage_value(
                    response,
                    "total_tokens"
                ),


            "llm_model":
                get_model_name(
                    response
                ),


            "llm_raw_response":
                raw_text[:2000]

        }


    except Exception as e:


        return {

            "llm_run_id":
                LLM_RUN_ID,


            "derived_coi":
                row.get(
                    "overall_coi",
                    0
                ),


            "llm_score":
                None,


            "llm_score_difference":
                None,


            "llm_validation":
                False,


            "llm_qualification_bucket":
                "",


            "llm_confidence":
                "",


            "llm_couchbase_fit":
                "",


            "llm_evidence_strength":
                "",


            "llm_database_replacement_signal":
                "",


            "llm_technical_risk":
                "",


            "llm_priority_recommendation":
                "",


            "llm_delta_explanation":
                "",


            "llm_score_blockers":
                [],


            "llm_strongest_signals":
                [],


            "llm_weakest_assumptions":
                [],


            "llm_required_discovery_questions":
                [],


            "llm_reasoning":
                str(e),


            "llm_recommended_action":
                "",


            "llm_input_tokens":
                get_usage_value(
                    response,
                    "input_tokens"
                ),


            "llm_output_tokens":
                get_usage_value(
                    response,
                    "output_tokens"
                ),


            "llm_total_tokens":
                get_usage_value(
                    response,
                    "total_tokens"
                ),


            "llm_model":
                get_model_name(
                    response
                ),


            "llm_raw_response":
                response.get(
                    "text",
                    ""
                )[:2000]
                if response
                else ""

        }
