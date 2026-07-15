def generate_explanation(row):

    """
    Generates AE-facing sales intelligence.

    Converts scoring output into:
    - Why this account
    - Likely workloads
    - Personas
    - Discovery questions
    - Couchbase story
    """


    business_model = str(
        row.get(
            "business_model",
            "Unknown"
        )
    )

    industry = str(
        row.get(
            "industry",
            "Unknown"
        )
    )


    workloads = row.get(
        "additional_workloads",
        []
    )


    if not isinstance(workloads, list):

        workloads = []



    coi = row.get(
        "overall_coi",
        0
    )


    #
    # Why this account
    #
    if business_model != "Unknown":

        why = (
            f"{business_model} organization in the "
            f"{industry} space with potential "
            f"Couchbase operational database workloads."
        )

    elif industry != "Unknown":

        why = (
            f"{industry} organization with "
            f"potential high-performance operational "
            f"application requirements."
        )

    else:

        why = (
            "Limited intelligence available. "
            "Additional enrichment recommended."
        )



    #
    # Workloads
    #
    if workloads:

        workload_text = ", ".join(
            workloads
        )

    else:

        workload_text = (
            "Customer profiles, transactional "
            "applications, APIs, operational workloads"
        )



    #
    # Recommended personas
    #
    personas = [

        "VP Engineering",

        "Director of Applications",

        "Enterprise Architect",

        "Platform Engineering"

    ]


    #
    # Discovery questions
    #
    questions = [

        "How are you managing operational application data today?",

        "Are you running multiple databases for operational workloads, caching, or search?",

        "What AI initiatives are you exploring that require access to operational data?"

    ]



    #
    # Couchbase value proposition
    #
    couchbase_story = (

        "Couchbase Capella can help consolidate "
        "operational database workloads, caching, "
        "and AI-ready data services while improving "
        "application performance and reducing "
        "operational complexity."

    )



    #
    # Return enrichment
    #
    return {

        "opportunity_score": coi,

        "why_this_account": why,

        "likely_workloads": workload_text,

        "recommended_personas": ", ".join(
            personas
        ),

        "discovery_questions": " | ".join(
            questions
        ),

        "couchbase_story": couchbase_story

    }
