def calculate_coi(row):

    score = 0
    breakdown = {}


    # =====================================================
    # SIGNAL INPUTS
    # =====================================================

    industry = str(row.get("industry", "Unknown"))

    financial_segment = str(
        row.get("financial_segment", "Unknown")
    )

    business_model = str(
        row.get("business_model", "Unknown")
    )

    workloads = row.get(
        "workloads",
        []
    )

    if isinstance(workloads, str):
        workloads = [
            workloads
        ]


    company_signal = int(
        row.get(
            "company_signal_score",
            0
        )
    )


    technology_score = int(
        row.get(
            "technology_score",
            0
        )
    )


    company_size = str(
        row.get(
            "company_size",
            "Unknown"
        )
    )


    engineering = str(
        row.get(
            "engineering_signal",
            "Unknown"
        )
    )


    revenue = str(
        row.get(
            "revenue_signal",
            "Unknown"
        )
    )



    # =====================================================
    # 1. WORKLOAD FIT (MOST IMPORTANT)
    # =====================================================

    workload_points = 0


    high_value_workloads = [
        "transaction",
        "payment",
        "customer",
        "profile",
        "identity",
        "api",
        "application",
        "real-time",
        "real time",
        "operational",
        "integration",
        "data exchange"
    ]


    workload_text = " ".join(
        [
            str(x).lower()
            for x in workloads
        ]
    )


    matches = 0

    for item in high_value_workloads:

        if item in workload_text:

            matches += 1


    if matches >= 5:

        workload_points = 35

    elif matches >= 3:

        workload_points = 25

    elif matches >= 1:

        workload_points = 15



    breakdown["workload_fit_points"] = workload_points

    score += workload_points



    # =====================================================
    # 2. KNOWN COMPANY SIGNAL
    # =====================================================

    # company intelligence is evidence,
    # but cannot create Tier 1 alone

    company_points = min(
        company_signal,
        20
    )


    breakdown["company_signal_points"] = company_points

    score += company_points



    # =====================================================
    # 3. TECHNOLOGY MATURITY
    # =====================================================

    tech_points = 0


    if technology_score >= 40:

        tech_points = 15

    elif technology_score >= 20:

        tech_points = 10

    elif technology_score > 0:

        tech_points = 5



    breakdown["technology_signal_points"] = tech_points

    score += tech_points



    # =====================================================
    # 4. INDUSTRY FIT
    # =====================================================

    industry_points = 0


    if industry == "Technology / SaaS":

        industry_points = 10


    elif industry == "Financial Services":

        if financial_segment == "Payments":

            industry_points = 15

        else:

            industry_points = 10


    elif industry == "Healthcare":

        industry_points = 10


    elif industry == "Retail":

        industry_points = 8



    breakdown["industry_fit_points"] = industry_points

    score += industry_points



    # =====================================================
    # 5. ENGINEERING CAPABILITY
    # =====================================================

    engineering_points = 0


    if engineering == "High":

        engineering_points = 10


    elif engineering == "Medium":

        engineering_points = 5



    breakdown["engineering_points"] = engineering_points

    score += engineering_points



    # =====================================================
    # 6. ENTERPRISE VALUE
    # =====================================================

    enterprise_points = 0


    if company_size == "Enterprise":

        enterprise_points = 5


    breakdown["enterprise_points"] = enterprise_points

    score += enterprise_points



    # =====================================================
    # REMOVE FALSE POSITIVES
    # =====================================================

    # AI alone is NOT opportunity

    if (
        workload_points == 0
        and
        company_signal == 0
    ):

        score = min(
            score,
            40
        )



    # =====================================================
    # FINAL SCORE
    # =====================================================

    breakdown["raw_coi_score"] = score


    breakdown["overall_coi"] = min(
        score,
        100
    )



    # =====================================================
    # PRIORITY
    # =====================================================

    if score >= 80:

        tier = "Tier 1 Strategic"


    elif score >= 60:

        tier = "Tier 2 Strong Target"


    elif score >= 40:

        tier = "Tier 3 Nurture"


    else:

        tier = "Tier 4 Monitor"



    breakdown["priority_tier"] = tier



    # =====================================================
    # SALES MOTION
    # =====================================================

    if tier == "Tier 1 Strategic":

        motion = (
            "Enterprise technical discovery - "
            "target architecture, engineering, "
            "and data platform leaders"
        )

    elif tier == "Tier 2 Strong Target":

        motion = (
            "Business discovery - validate "
            "workloads and database challenges"
        )

    else:

        motion = (
            "Continue enrichment before outreach"
        )


    breakdown["sales_motion"] = motion


    return breakdown
