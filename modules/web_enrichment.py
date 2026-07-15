import json
import os


CONFIG_FILE = "data/technology_patterns.json"


def load_patterns():
    if not os.path.exists(CONFIG_FILE):
        return {}

    with open(CONFIG_FILE, "r") as file:
        return json.load(file)


def analyze_technology_signals(company_name):
    """
    Phase 2 placeholder enrichment engine.

    Future:
    - company website scraping
    - LinkedIn enrichment
    - news APIs
    - technology detection

    Current:
    pattern based intelligence
    """

    patterns = load_patterns()

    company = company_name.lower()

    result = {
        "cloud_signal": "Unknown",
        "database_signal": "Unknown",
        "ai_signal": "Unknown",
        "technology_score": 0
    }


    for category, values in patterns.items():

        for keyword in values:

            if keyword.lower() in company:

                if category == "cloud":
                    result["cloud_signal"] = keyword
                    result["technology_score"] += 10

                elif category == "database":
                    result["database_signal"] = keyword
                    result["technology_score"] += 15

                elif category == "ai":
                    result["ai_signal"] = keyword
                    result["technology_score"] += 15


    return result
