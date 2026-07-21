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
                "why_this_workload_matters": clean_value(
                    row.get("why_this_workload_matters", "")
                ),
                "engineering_implications": clean_value(
                    row.get("engineering_implications", [])
                ),
                "couchbase_point_of_view": clean_value(
                    row.get("couchbase_point_of_view", "")
                ),
                "technical_risks_to_validate": clean_value(
                    row.get("technical_risks_to_validate", [])
                ),
                "conversation_strategy": clean_value(
                    row.get("conversation_strategy", "")
                ),
                "discovery_progression": clean_value(
                    row.get("discovery_progression", [])
                ),
                "missing_information": clean_value(
                    row.get("missing_information", [])
                )
            },
            "llm_validation": {
                "llm_run_id": clean_value(
                    row.get("llm_run_id", "")
                ),
                "llm_validation": clean_value(
                    row.get("llm_validation", "")
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
