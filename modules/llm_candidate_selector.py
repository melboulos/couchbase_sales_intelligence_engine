def select_llm_candidate(row):

    score = 0
    reasons = []


    # =====================================================
    # COUCHBASE OPPORTUNITY SCORE
    # =====================================================

    coi = row.get(
        "overall_coi",
        0
    )

    try:
        coi = int(coi)

    except:
        coi = 0


    if coi >= 80:

        score += 30

        reasons.append(
            "High Couchbase Opportunity Index"
        )


    elif coi >= 60:

        score += 15

        reasons.append(
            "Strong Couchbase fit signal"
        )



    # =====================================================
    # ENGINEERING SIGNAL
    # =====================================================

    if row.get(
        "engineering_signal"
    ) == "High":

        score += 20

        reasons.append(
            "Strong engineering organization"
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
            "Modern technology signals"
        )



    # =====================================================
    # AI SIGNAL
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

        score += 15

        reasons.append(
            "AI modernization opportunity"
        )



    # =====================================================
    # ENTERPRISE SIGNAL
    # =====================================================

    if row.get(
        "company_size"
    ) == "Enterprise":

        score += 10

        reasons.append(
            "Enterprise account"
        )



    # =====================================================
    # INDUSTRY FIT
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

        score += 10

        reasons.append(
            "Strong Couchbase target industry"
        )



    # =====================================================
    # FINAL DECISION
    # =====================================================

    candidate = False


    if score >= 60:

        candidate = True



    return {

        "llm_score": score,

        "llm_candidate": candidate,

        "llm_reason": "; ".join(
            reasons
        )

    }
