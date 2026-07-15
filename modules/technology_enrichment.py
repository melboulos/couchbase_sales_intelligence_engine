import json
import os


TECH_FILE = "data/technology_patterns.json"


def load_patterns():

    if not os.path.exists(TECH_FILE):
        return []

    with open(TECH_FILE, "r") as file:
        return json.load(file)



def analyze_technology(company_name):

    company_name = str(company_name).lower()

    patterns = load_patterns()

    result = {
        "cloud_signal": "Unknown",
        "database_signal": "Unknown",
        "ai_signal": "Unknown",
        "technology_score": 0
    }


    for item in patterns:

        keywords = item.get("keywords", [])

        for keyword in keywords:

            if keyword.lower() in company_name:

                result["cloud_signal"] = item.get(
                    "cloud_signal",
                    "Unknown"
                )

                result["database_signal"] = item.get(
                    "database_signal",
                    "Unknown"
                )

                result["ai_signal"] = item.get(
                    "ai_signal",
                    "Unknown"
                )

                result["technology_score"] = item.get(
                    "score",
                    0
                )

                return result


    return result
