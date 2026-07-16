import json
import os
import pandas as pd


OUTPUT_FILE = "output/account_intelligence.json"


def clean_value(value):

    if value is None:
        return ""

    if isinstance(value, (list, dict)):
        return value

    if hasattr(value, "tolist"):
        return value.tolist()

    try:
        result = pd.isna(value)

        if isinstance(result, bool) and result:
            return ""

    except Exception:
        pass

    return value



def export_account_intelligence(accounts):

    records = []

    for _, row in accounts.iterrows():

        record = {

            "account_name": clean_value(
                row.get("Account Name", "")
            ),

            "industry": clean_value(
                row.get("industry", "")
            ),

            "overall_coi": clean_value(
                row.get("overall_coi", 0)
            ),

            "priority_tier": clean_value(
                row.get("priority_tier", "")
            ),

            "business_model": clean_value(
                row.get("business_model", "")
            ),

            "workloads": clean_value(
                row.get("workloads", [])
            ),


            "technology_signals": {

                "cloud_signal": clean_value(
                    row.get("cloud_signal", "")
                ),

                "database_signal": clean_value(
                    row.get("database_signal", "")
                ),

                "ai_signal": clean_value(
                    row.get("ai_signal", "")
                )
            },


            "sales_intelligence": {

                "opportunity_summary": clean_value(
                    row.get("opportunity_summary", "")
                ),

                "couchbase_trigger": clean_value(
                    row.get("couchbase_trigger", "")
                ),

                "seller_action": clean_value(
                    row.get("seller_action", "")
                ),

                "discovery_questions": clean_value(
                    row.get("discovery_questions", [])
                ),

                "evidence_found": clean_value(
                    row.get("evidence_found", [])
                ),

                "missing_evidence": clean_value(
                    row.get("missing_evidence", [])
                )
            },


            "llm_validation": {

                "llm_opportunity_score": clean_value(
                    row.get("llm_opportunity_score", "")
                ),

                "coi_assessment": clean_value(
                    row.get("coi_assessment", "")
                ),

                "coi_delta_reason": clean_value(
                    row.get("coi_delta_reason", "")
                ),

                "database_replacement_probability": clean_value(
                    row.get("database_replacement_probability", "")
                ),

                "technical_risk": clean_value(
                    row.get("technical_risk", "")
                )
            }
        }


        records.append(record)


    os.makedirs(
        "output",
        exist_ok=True
    )


    with open(
        OUTPUT_FILE,
        "w"
    ) as f:

        json.dump(
            records,
            f,
            indent=2,
            default=str
        )


    print(
        f"Saved intelligence JSON: {OUTPUT_FILE}"
    )
