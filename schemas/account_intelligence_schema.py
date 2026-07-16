def build_account_intelligence(row):

    return {

        "account_name":
            row.get(
                "Account Name",
                ""
            ),

        "industry":
            row.get(
                "industry",
                ""
            ),

        "overall_coi":
            row.get(
                "overall_coi",
                0
            ),

        "priority_tier":
            row.get(
                "priority_tier",
                ""
            ),

        "business_model":
            row.get(
                "business_model",
                ""
            ),

        "workloads":
            row.get(
                "workloads",
                []
            ),

        "technology_signals": {

            "cloud_signal":
                row.get(
                    "cloud_signal",
                    ""
                ),

            "database_signal":
                row.get(
                    "database_signal",
                    ""
                ),

            "ai_signal":
                row.get(
                    "ai_signal",
                    ""
                )
        },


        "sales_intelligence": {

            "why_this_account":
                row.get(
                    "why_this_account",
                    ""
                ),

            "recommended_action":
                row.get(
                    "recommended_action",
                    ""
                )
        },


        "llm_validation": {

            "llm_score":
                row.get(
                    "llm_score",
                    0
                ),

            "confidence":
                row.get(
                    "llm_confidence",
                    ""
                ),

            "reasoning":
                row.get(
                    "llm_reasoning",
                    ""
                )
        }
    }
