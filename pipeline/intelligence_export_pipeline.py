import json
import os
import pandas as pd


OUTPUT_FILE = (
    "output/"
    "account_intelligence.json"
)


def clean_value(value):

    if isinstance(value, list):
        return value

    if isinstance(value, dict):
        return value

    if pd.isna(value):
        return ""

    return value



def export_account_intelligence(
    accounts
):

    records = []


    for _, row in accounts.iterrows():

        record = {

            "account_name":
                clean_value(
                    row.get(
                        "Account Name",
                        ""
                    )
                ),


            "industry":
                clean_value(
                    row.get(
                        "industry",
                        ""
                    )
                ),


            "overall_coi":
                clean_value(
                    row.get(
                        "overall_coi",
                        0
                    )
                ),


            "priority_tier":
                clean_value(
                    row.get(
                        "priority_tier",
                        ""
                    )
                ),


            "business_model":
                clean_value(
                    row.get(
                        "business_model",
                        ""
                    )
                ),


            "workloads":
                clean_value(
                    row.get(
                        "workloads",
                        []
                    )
                ),


            "technology_signals": {

                "cloud_signal":
                    clean_value(
                        row.get(
                            "cloud_signal",
                            ""
                        )
                    ),


                "database_signal":
                    clean_value(
                        row.get(
                            "database_signal",
                            ""
                        )
                    ),


                "ai_signal":
                    clean_value(
                        row.get(
                            "ai_signal",
                            ""
                        )
                    )
            },


            "sales_intelligence": {

                "why_this_account":
                    clean_value(
                        row.get(
                            "opportunity_explanation",
                            ""
                        )
                    ),


                "recommended_action":
                    clean_value(
                        row.get(
                            "llm_recommended_action",
                            ""
                        )
                    ),


                "recommended_persona":
                    clean_value(
                        row.get(
                            "recommended_persona",
                            ""
                        )
                    )
            },


            "llm_validation": {

            "llm_original_score":
                clean_value(
                    row.get(
                        "llm_score",
                        ""
                    )
                ),
                "llm_score":
                    clean_value(
                        row.get(
                            "llm_score",
                            0
                        )
                    ),


                "confidence":
                    clean_value(
                        row.get(
                            "llm_confidence",
                            ""
                        )
                    ),


                "reasoning":
                    clean_value(
                        row.get(
                            "llm_reasoning",
                            ""
                        )
                    ),


                "recommended_action":
                    clean_value(
                        row.get(
                            "llm_recommended_action",
                            ""
                        )
                    )
            }

        }


        records.append(
            record
        )


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
