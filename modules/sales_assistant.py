def generate_sales_assistant(row):

    industry = row.get("industry","Unknown")
    business = row.get("business_model","Unknown")
    ai = row.get("ai_initiatives","Unknown")
    db = row.get("database_signal","Unknown")
    coi = row.get("overall_coi",0)

    # Persona selection

    if "Financial" in industry or "FinTech" in business:
        persona = "CTO, VP Engineering, Data Architect"
        use_case = "High volume transactions, fraud detection, real-time analytics"

    elif "Healthcare" in industry:
        persona = "CTO, Chief Data Officer, Platform Engineering"
        use_case = "Healthcare interoperability and real-time patient data"

    elif "Technology" in industry or "SaaS" in business:
        persona = "VP Engineering, Software Architects, Product Engineering"
        use_case = "Cloud-native applications and developer velocity"

    else:
        persona = "Engineering Leadership"
        use_case = "Modern application modernization"

    
    if coi >= 80:
        action = "Immediate outbound priority"
        tier = "A"

    elif coi >=50:
        action = "Research and targeted outreach"
        tier = "B"

    else:
        action = "Nurture"
        tier = "C"


    talk_track = (
        f"{business} organizations often struggle with "
        f"scaling operational data workloads. "
        f"Couchbase can help with {use_case}."
    )


    questions = [
        "How are you currently handling operational application data?",
        "Are you modernizing workloads for cloud environments?",
        "Where are you seeing database scalability challenges?",
        "Are AI initiatives creating new data requirements?"
    ]


    return {
        "priority_tier": tier,
        "recommended_persona": persona,
        "database_use_case": use_case,
        "couchbase_talk_track": talk_track,
        "discovery_questions": " | ".join(questions),
        "next_best_action": action
    }
