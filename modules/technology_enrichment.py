import json
import os
import re


TECH_FILE = "data/technology_patterns.json"


def load_patterns():

    if not os.path.exists(TECH_FILE):
        return []

    with open(TECH_FILE, "r") as file:
        return json.load(file)



def keyword_match(text, keyword):

    text = text.lower()
    keyword = keyword.lower()


    # Handle multi-word phrases
    if " " in keyword:

        return keyword in text


    # Whole word matching prevents:
    # ai -> aim
    # ai -> haimo

    return re.search(
        r"\b" + re.escape(keyword) + r"\b",
        text
    ) is not None



def analyze_technology(row):


    company_name = " ".join(
        [

            str(
                row.get(
                    "normalized_account_name",
                    ""
                )
            ),

            str(
                row.get(
                    "Account Name",
                    ""
                )
            ),

            str(
                row.get(
                    "industry",
                    ""
                )
            ),

            str(
                row.get(
                    "financial_segment",
                    ""
                )
            ),

            str(
                row.get(
                    "business_model",
                    ""
                )
            ),

            str(
                row.get(
                    "workloads",
                    ""
                )
            ),

            str(
                row.get(
                    "couchbase_use_cases",
                    ""
                )
            )

        ]

    ).lower()



    patterns = load_patterns()



    result = {

        "cloud_signal": "Unknown",

        "database_signal": "Unknown",

        "ai_signal": "Unknown",

        "technology_signals": [],

        "technology_score": 0

    }



    matched_scores = []



    for item in patterns:


        keywords = item.get(
            "keywords",
            []
        )


        matched = False



        for keyword in keywords:


            if keyword_match(
                company_name,
                keyword
            ):

                matched = True
                break



        if matched:


            result["technology_signals"].append(
                item.get(
                    "name",
                    "Technology Signal"
                )
            )



            if result["cloud_signal"] == "Unknown":

                result["cloud_signal"] = item.get(
                    "cloud_signal",
                    "Unknown"
                )



            if result["database_signal"] == "Unknown":

                result["database_signal"] = item.get(
                    "database_signal",
                    "Unknown"
                )



            if result["ai_signal"] == "Unknown":

                result["ai_signal"] = item.get(
                    "ai_signal",
                    "Unknown"
                )



            matched_scores.append(
                item.get(
                    "score",
                    0
                )
            )



    result["technology_score"] = min(
        sum(matched_scores),
        30
    )


    return result
