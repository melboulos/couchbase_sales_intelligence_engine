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


        # =====================================================
        # SALES INTELLIGENCE CONTRACT VALIDATION
        # =====================================================

        required_fields = [

            "llm_opportunity_score",

            "coi_assessment",

            "opportunity_summary",

            "couchbase_trigger",

            "missing_evidence",

            "seller_action",

            "discovery_questions"

        ]


        missing_fields = [

            field

            for field in required_fields

            if field not in result

        ]


        if missing_fields:

            raise ValueError(
                f"LLM missing required sales intelligence fields: {missing_fields}"
            )


        # =====================================================
        # RETURN SALES INTELLIGENCE
        # =====================================================

        return {


            "llm_run_id":

                LLM_RUN_ID,


            "llm_validation":

                True,


            "llm_opportunity_score":

                result.get(
                    "llm_opportunity_score",
                    0
                ),


            "coi_assessment":

                result.get(
                    "coi_assessment",
                    ""
                ),


            "coi_delta_reason":

                result.get(
                    "coi_delta_reason",
                    ""
                ),


            "opportunity_summary":

                result.get(
                    "opportunity_summary",
                    ""
                ),


            "couchbase_trigger":

                result.get(
                    "couchbase_trigger",
                    ""
                ),


            "evidence_found":

                result.get(
                    "evidence_found",
                    []
                ),


            "missing_evidence":

                result.get(
                    "missing_evidence",
                    []
                ),


            "database_replacement_probability":

                result.get(
                    "database_replacement_probability",
                    ""
                ),


            "technical_risk":

                result.get(
                    "technical_risk",
                    ""
                ),


            "seller_action":

                result.get(
                    "seller_action",
                    ""
                ),


            "discovery_questions":

                result.get(
                    "discovery_questions",
                    []
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


            "llm_validation":

                False,


            "llm_error":

                str(e)

        }
