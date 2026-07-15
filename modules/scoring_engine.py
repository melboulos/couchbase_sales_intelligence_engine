def calculate_coi(row):

    score = 0

    breakdown = {}

    # =====================================================
    # INPUT SIGNALS
    # =====================================================

    industry = str(
        row.get(
            "industry",
            "Unknown"
        )
    )

    financial_segment = str(
        row.get(
            "financial_segment",
            "Unknown"
        )
    )

    business_model = str(
        row.get(
            "business_model",
            "Unknown"
        )
    )

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

    ai = str(
        row.get(
            "ai_initiatives",
            "Unknown"
        )
    )


    # =====================================================
    # COMPANY INTELLIGENCE
    # =====================================================

    breakdown["company_signal_points"] = company_signal

    score += company_signal



    # =====================================================
    # TECHNOLOGY FIT
    # =====================================================

    breakdown["technology_signal_points"] = technology_score

    score += technology_score



    # =====================================================
    # INDUSTRY / SEGMENT FIT
    # =====================================================

    industry_points = 0


    if industry == "Technology / SaaS":

        industry_points = 25



    elif industry == "Financial Services":


        if financial_segment == "Payments":

            industry_points = 30


        elif financial_segment == "Fintech":

            industry_points = 25


        elif financial_segment == "Lending":

            industry_points = 20


        elif financial_segment == "Banking":

            industry_points = 10


        elif financial_segment == "Investment":

            industry_points = 5


        elif financial_segment == "Insurance":

            industry_points = 5


        else:

            industry_points = 10



    elif industry == "Healthcare":

        industry_points = 20



    elif industry == "Retail":

        industry_points = 15



    elif industry == "Transportation and Logistics":

        industry_points = 10



    elif industry == "Energy and Utilities":

        industry_points = 10



    breakdown["industry_fit_points"] = industry_points

    score += industry_points



    # =====================================================
    # BUSINESS MODEL
    # =====================================================

    business_points = 0


    if business_model != "Unknown":

        business_points = 10


    breakdown["business_model_fit_points"] = business_points

    score += business_points



    # =====================================================
    # ENTERPRISE
    # =====================================================

    enterprise_points = 0


    if company_size == "Enterprise":

        enterprise_points = 10


    breakdown["enterprise_signal_points"] = enterprise_points

    score += enterprise_points



    # =====================================================
    # ENGINEERING
    # =====================================================

    engineering_points = 0


    if engineering == "High":

        engineering_points = 10


    breakdown["engineering_strength_points"] = engineering_points

    score += engineering_points



    # =====================================================
    # REVENUE
    # =====================================================

    revenue_points = 0


    if revenue == "High":

        revenue_points = 5


    breakdown["revenue_signal_points"] = revenue_points

    score += revenue_points



    # =====================================================
    # AI SIGNAL
    # =====================================================

    ai_points = 0


    if ai != "Unknown":

        ai_points = 5


    breakdown["ai_signal_points"] = ai_points

    score += ai_points



    # =====================================================
    # CONFIDENCE
    # =====================================================

    intelligence_fields = 0


    if industry != "Unknown":

        intelligence_fields += 1


    if business_model != "Unknown":

        intelligence_fields += 1


    if company_signal > 0:

        intelligence_fields += 1


    if technology_score > 0:

        intelligence_fields += 1


    if company_size != "Unknown":

        intelligence_fields += 1



    confidence_score = int(
        (intelligence_fields / 5) * 100
    )


    if confidence_score >= 80:

        confidence = "High"


    elif confidence_score >= 40:

        confidence = "Medium"


    else:

        confidence = "Low"



    breakdown["confidence_score"] = confidence_score

    breakdown["confidence"] = confidence



    # =====================================================
    # FINAL SCORE
    # =====================================================

    breakdown["raw_coi_score"] = score


    breakdown["overall_coi"] = min(
        score,
        100
    )


    return breakdown
