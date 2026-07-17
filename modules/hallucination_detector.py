"""
hallucination_detector.py

Sales Intelligence LLM hallucination detection.

Purpose:
    Prevent LLM from inventing:
      - database technologies
      - customer architecture
      - migration projects
      - performance problems
      - business initiatives
      - technical facts not supported by evidence

Used by:
    llm_output_validator.py

"""

import re


# =====================================================
# CONFIGURATION
# =====================================================

HIGH_RISK_PATTERNS = {

    "existing_database_claim": [

        r"existing database",
        r"current database",
        r"their database",
        r"database platform",
        r"database technology currently",
        r"currently uses .* database",
        r"running on .* database",
        r"built on .* database"

    ],


    "migration_claim": [

        r"migrat(ed|ing|ion)",
        r"replace(d|ment)? .* database",
        r"moving from",
        r"switching from",
        r"moderniz(ing|ation) from"

    ],


    "unsupported_vendor_claim": [

        r"\boracle\b",
        r"\bpostgres\b",
        r"\bpostgresql\b",
        r"\bmysql\b",
        r"\bmongodb\b",
        r"\bcassandra\b",
        r"\bdynamodb\b",
        r"\bcosmosdb\b",
        r"\bsql server\b"

    ],


    "invented_problems": [

        r"experiencing scalability issues",
        r"performance issues",
        r"latency problems",
        r"database bottleneck",
        r"slow queries",
        r"capacity issues",
        r"availability problems"

    ],


    "unsupported_metrics": [

        r"\d+\s*(ms|milliseconds)",
        r"\d+\s*(million|billion)",
        r"\d+%\s*(increase|decrease|improvement)",
        r"\d+x\s*(faster|scale)"

    ],


    "false_certainty": [

        r"is using",
        r"uses",
        r"currently has",
        r"currently runs",
        r"has deployed",
        r"has implemented",
        r"already adopted"

    ]

}


# =====================================================
# EVIDENCE EXTRACTION
# =====================================================


def flatten_evidence(row):

    """
    Convert enrichment data into searchable evidence text.
    """

    evidence = []


    fields = [

        "industry",

        "business_model",

        "workloads",

        "cloud_signal",

        "database_signal",

        "technology_score",

        "ai_initiatives",

        "engineering_signal",

        "revenue_signal",

        "company_signal"

    ]


    for field in fields:

        value = row.get(field)


        if value:

            if isinstance(value, list):

                evidence.extend(value)

            else:

                evidence.append(
                    str(value)
                )


    return " ".join(evidence).lower()



# =====================================================
# PATTERN SCANNER
# =====================================================


def scan_patterns(text):

    findings = []


    lower = text.lower()


    for category, patterns in HIGH_RISK_PATTERNS.items():

        for pattern in patterns:


            matches = re.findall(
                pattern,
                lower
            )


            if matches:

                findings.append(
                    {
                        "category": category,

                        "pattern": pattern,

                        "matches": matches
                    }
                )


    return findings



# =====================================================
# DATABASE CLAIM VALIDATION
# =====================================================


def validate_database_claims(
        text,
        evidence
):

    findings = []


    database_terms = [

        "oracle",
        "postgres",
        "postgresql",
        "mysql",
        "mongodb",
        "cassandra",
        "dynamodb",
        "cosmosdb",
        "sql server",
        "redis"

    ]


    for db in database_terms:


        if db in text.lower():


            if db not in evidence:


                findings.append(

                    {
                        "category":
                        "unsupported_database",

                        "claim":
                        db,

                        "severity":
                        "high"

                    }

                )


    return findings



# =====================================================
# CLAIM CERTAINTY ANALYSIS
# =====================================================


def detect_certainty_risk(text):

    findings = []


    sentences = re.split(
        r"[.!?]",
        text
    )


    for sentence in sentences:


        lower = sentence.lower()


        for pattern in HIGH_RISK_PATTERNS["false_certainty"]:


            if re.search(
                pattern,
                lower
            ):


                findings.append(

                    {
                        "category":
                        "certainty_language",

                        "sentence":
                        sentence.strip(),

                        "severity":
                        "medium"

                    }

                )


    return findings



# =====================================================
# MAIN ANALYZER
# =====================================================


def analyze_hallucinations(
        row,
        llm_output
):

    """
    Main hallucination analyzer.

    Args:

        row:
            original enriched account row

        llm_output:
            dictionary returned from LLM

    Returns:

        {
          hallucination_detected,
          hallucination_score,
          risk_level,
          findings
        }

    """


    text_parts = []


    for key, value in llm_output.items():


        if value is None:

            continue


        if isinstance(value, list):

            text_parts.extend(value)


        else:

            text_parts.append(
                str(value)
            )


    full_text = " ".join(
        text_parts
    )


    evidence = flatten_evidence(
        row
    )


    findings = []


    # ---------------------------------------------
    # Pattern detection
    # ---------------------------------------------

    findings.extend(

        scan_patterns(
            full_text
        )

    )


    # ---------------------------------------------
    # Database validation
    # ---------------------------------------------

    findings.extend(

        validate_database_claims(
            full_text,
            evidence
        )

    )


    # ---------------------------------------------
    # Certainty validation
    # ---------------------------------------------

    findings.extend(

        detect_certainty_risk(
            full_text
        )

    )



    # =================================================
    # SCORE
    # =================================================


    score = 0


    for finding in findings:


        severity = finding.get(
            "severity",
            "medium"
        )


        if severity == "high":

            score += 25


        elif severity == "medium":

            score += 10


        else:

            score += 5



    score = min(
        score,
        100
    )


    if score >= 60:

        risk = "HIGH"


    elif score >= 30:

        risk = "MEDIUM"


    else:

        risk = "LOW"



    return {


        "hallucination_detected":

            len(findings) > 0,


        "hallucination_score":

            score,


        "hallucination_risk":

            risk,


        "hallucination_findings":

            findings

    }



# =====================================================
# QUICK TEST
# =====================================================


if __name__ == "__main__":


    test_row = {

        "industry":
        "Financial Services",

        "workloads":
        [
            "Payments",
            "Fraud Detection"
        ]

    }


    test_output = {

        "technical_conversation":

        """

        Netspend currently uses Oracle
        and is experiencing database latency
        problems.

        """

    }


    result = analyze_hallucinations(
        test_row,
        test_output
    )


    print(result)
