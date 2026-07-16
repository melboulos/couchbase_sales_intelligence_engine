def select_llm_candidate(row):

    score = 0
    reasons = []


    # =====================================================
    # COUCHBASE OPPORTUNITY SCORE
    # Evidence-based LLM qualification
    # =====================================================

    coi = row.get(
        "overall_coi",
        0
    )

    try:
        coi = int(coi)

    except:
        coi = 0



    # =====================================================
    # WORKLOAD SIGNAL
    # Strongest indicator
    # =====================================================

    workloads = row.get(
        "workloads",
        []
    )


    if isinstance(workloads, list):

        if len(workloads) > 0:

            score += 25

            reasons.append(
                "Operational workload evidence"
            )



    # =====================================================
    # DATABASE SIGNAL
    # =====================================================

    database_signal = str(
        row.get(
            "database_signal",
            ""
        )
    )


    if database_signal.lower() not in [
        "",
        "unknown",
        "none"
    ]:

        score += 20

        reasons.append(
            "Database technology signal"
        )



    # =====================================================
    # TECHNOLOGY SIGNAL
    # =====================================================

    technology_score = row.get(
        "technology_score",
        0
    )


    try:
        technology_score = int(
            technology_score
        )

    except:
        technology_score = 0



    if technology_score >= 15:

        score += 15

        reasons.append(
            "Modern technology environment"
        )



    # =====================================================
    # ENGINEERING SIGNAL
    # =====================================================

    if row.get(
        "engineering_signal"
    ) == "High":

        score += 10

        reasons.append(
            "Strong engineering organization"
        )



    # =====================================================
    # COI SIGNAL
    # =====================================================

    if coi >= 80:

        score += 15

        reasons.append(
            "High Couchbase Opportunity Index"
        )


    elif coi >= 60:

        score += 10

        reasons.append(
            "Strong Couchbase Opportunity Index"
        )



    # =====================================================
    # AI SIGNAL
    # Lower weight
    # =====================================================

    ai_signal = str(
        row.get(
            "ai_signal",
            ""
        )
    )


    if ai_signal.lower() not in [
        "",
        "unknown",
        "none"
    ]:

        score += 5

        reasons.append(
            "AI modernization signal"
        )



    # =====================================================
    # INDUSTRY FIT
    # Lower weight
    # =====================================================

    industry = row.get(
        "industry",
        ""
    )


    if industry in [
        "Financial Services",
        "Healthcare",
        "Technology / SaaS",
        "Retail"
    ]:

        score += 5

        reasons.append(
            "Target industry"
        )



    # =====================================================
    # FINAL DECISION
    #
    # LLM candidates are ranked.
    # Candidate flag only means qualified.
    # =====================================================

    candidate = False


    if score >= 50:

        candidate = True

        reasons.append(
            "LLM validation candidate"
        )



    return {

        "llm_score": score,

        "llm_candidate": candidate,

        "llm_reason": "; ".join(
            reasons
        )

    }
