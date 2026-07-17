# =====================================================
# LLM OUTPUT VALIDATOR
# Couchbase Sales Intelligence Agent
#
# Validates new intelligence contract
#
# =====================================================

import re



# =====================================================
# FORBIDDEN UNSUPPORTED CLAIMS
# =====================================================

FORBIDDEN_CLAIMS = [

    "uses oracle",

    "uses mongodb",

    "uses postgresql",

    "uses mysql",

    "current database is",

    "production database",

    "confirmed migration",

    "confirmed replacement",

    "customer is migrating"

]



# =====================================================
# REQUIRED OUTPUT CONTRACT
# =====================================================

INTELLIGENCE_REQUIRED_FIELDS = [

    "llm_opportunity_score",

    "coi_assessment",

    "coi_delta_reason",

    "opportunity_summary",

    "couchbase_trigger",

    "evidence_found",

    "missing_evidence",

    "database_replacement_probability",

    "technical_risk",

    "seller_action",

    "discovery_questions"

]



LIST_FIELDS = [

    "evidence_found",

    "missing_evidence",

    "discovery_questions"

]



# =====================================================
# NORMALIZATION
# =====================================================


def normalize_text(value):

    if value is None:

        return ""


    text = str(value).lower()


    text = re.sub(
        r"\s+",
        " ",
        text
    )


    return text.strip()



# =====================================================
# BUILD SEARCH TEXT
# =====================================================


def build_llm_text(result, raw_text):

    values = [

        raw_text

    ]


    for value in result.values():

        if isinstance(value, list):

            values.extend(value)

        else:

            values.append(value)


    return normalize_text(
        " ".join(
            str(v)
            for v in values
        )
    )



# =====================================================
# HALLUCINATION CHECK
# =====================================================


def detect_hallucinations(text):

    violations = []


    for claim in FORBIDDEN_CLAIMS:

        if claim in text:

            violations.append(
                claim
            )


    return violations



# =====================================================
# SCORE VALIDATION
# =====================================================


def validate_score(score):

    try:

        score = float(score)

    except:

        raise ValueError(
            "Invalid opportunity score"
        )


    if score < 0 or score > 100:

        raise ValueError(
            "Opportunity score outside 0-100"
        )



# =====================================================
# REQUIRED FIELDS
# =====================================================


def validate_required_fields(result):

    missing = [

        field

        for field in INTELLIGENCE_REQUIRED_FIELDS

        if field not in result

    ]


    if missing:

        raise ValueError(
            f"Missing LLM fields: {missing}"
        )



# =====================================================
# LIST VALIDATION
# =====================================================


def validate_lists(result):

    for field in LIST_FIELDS:


        if not isinstance(

            result.get(field),

            list

        ):

            raise ValueError(

                f"{field} must be list"

            )



# =====================================================
# EVIDENCE SEPARATION
#
# Evidence = facts
#
# Missing evidence = unknowns
#
# Signals are allowed.
#
# =====================================================


def validate_evidence(result):


    evidence_text = normalize_text(

        " ".join(

            result.get(
                "evidence_found",
                []
            )

        )

    )


    forbidden = [

        "ai potential",

        "cloud signal",

        "engineering signal",

        "innovation",

        "technology signal"

    ]


    violations = []


    for item in forbidden:

        if item in evidence_text:

            violations.append(item)



    if violations:


        raise ValueError(

            "Non-evidence signals placed in evidence_found: "

            f"{violations}"

        )



# =====================================================
# DATABASE PROBABILITY CHECK
# =====================================================


def validate_database_probability(result):


    probability = normalize_text(

        result.get(

            "database_replacement_probability",

            ""

        )

    )


    evidence = normalize_text(

        " ".join(

            result.get(

                "evidence_found",

                []

            )

        )

    )


    if probability in [

        "high",

        "medium"

    ]:


        if not evidence:


            raise ValueError(

                "Database replacement probability "
                "requires evidence"

            )



# =====================================================
# MAIN VALIDATOR
# =====================================================


def validate_llm_output(result, raw_text):


    validate_required_fields(
        result
    )


    text = build_llm_text(
        result,
        raw_text
    )


    violations = detect_hallucinations(
        text
    )


    if violations:

        raise ValueError(

            "Possible hallucination detected: "

            f"{violations}"

        )


    validate_score(

        result.get(
            "llm_opportunity_score"
        )

    )


    validate_lists(
        result
    )


    validate_evidence(
        result
    )


    validate_database_probability(
        result
    )


    return True
