def generate_sales_brief(row):

    account = str(
        row.get(
            "Account Name",
            ""
        )
    )


    # =====================================================
    # SAFE EXTRACTION
    # =====================================================

    def safe_value(field, default="Unknown"):

        value = row.get(
            field,
            default
        )

        if hasattr(value, "iloc"):
            value = value.iloc[-1]

        if value is None or str(value).strip() == "":
            return default

        return str(value)



    industry = safe_value(
        "industry"
    )


    business_model = safe_value(
        "business_model"
    )


    database_pressure = safe_value(
        "database_pressure"
    )


    modernization_signal = safe_value(
        "modernization_signal"
    )


    confidence = safe_value(
        "confidence"
    )


    cloud_signal = safe_value(
        "cloud_signal"
    )


    database_signal = safe_value(
        "database_signal"
    )


    ai_signal = safe_value(
        "ai_signal"
    )



    # =====================================================
    # LIST EXTRACTION
    # =====================================================

    def safe_list(field):

        value = row.get(
            field,
            []
        )

        if hasattr(value, "iloc"):
            value = value.iloc[-1]

        if isinstance(value, list):
            return value

        return []



    workloads = safe_list(
        "workloads"
    )


    use_cases = safe_list(
        "couchbase_use_cases"
    )


    buyer_personas = safe_list(
        "buyer_personas"
    )


    technology_signals = safe_list(
        "technology_signals"
    )



    # =====================================================
    # TECHNOLOGY SCORE
    # =====================================================

    technology_score = row.get(
        "technology_score",
        0
    )


    if hasattr(technology_score, "iloc"):
        technology_score = technology_score.iloc[-1]


    try:

        technology_score = int(
            technology_score
        )

    except:

        technology_score = 0



    # =====================================================
    # SCORE
    # =====================================================

    score = row.get(
        "overall_coi",
        0
    )


    if hasattr(score, "iloc"):
        score = score.iloc[-1]


    try:

        score = int(score)

    except:

        score = 0



    # =====================================================
    # PRIORITY
    # =====================================================

    if score >= 80:

        priority = "High"

    elif score >= 50:

        priority = "Medium"

    else:

        priority = "Low"



    # =====================================================
    # LIKELY DATABASES
    # =====================================================

    if industry == "Financial Services":

        likely_db = (
            "Oracle, SQL Server, "
            "transaction processing platforms, "
            "customer data systems"
        )


    elif industry == "Healthcare":

        likely_db = (
            "Epic ecosystem, SQL Server, "
            "healthcare application databases, "
            "API data platforms"
        )


    elif industry == "Technology / SaaS":

        likely_db = (
            "PostgreSQL, MongoDB, "
            "cloud operational databases, "
            "distributed application databases"
        )


    elif industry == "Retail":

        likely_db = (
            "SQL Server, Oracle, "
            "commerce platforms, "
            "customer engagement systems"
        )


    else:

        likely_db = (
            "Relational databases, "
            "application databases"
        )



    # =====================================================
    # FORMAT LISTS
    # =====================================================

    workload_text = (
        ", ".join(
            workloads[:5]
        )
        if workloads
        else "Operational applications"
    )


    use_case_text = (
        ", ".join(
            use_cases[:5]
        )
        if use_cases
        else "Real-time operational applications"
    )


    persona_text = (
        ", ".join(
            buyer_personas[:5]
        )
        if buyer_personas
        else "Technology leadership"
    )


    technology_text = (
        ", ".join(
            technology_signals[:5]
        )
        if technology_signals
        else "No technology signals identified"
    )



    # =====================================================
    # DISCOVERY QUESTIONS
    # =====================================================

    discovery = (
        "Explore database scalability, "
        "cloud modernization, "
        "application performance, "
        "and real-time data requirements."
    )


    if industry == "Financial Services":

        discovery = (
            "Explore transaction volume, "
            "fraud detection latency, "
            "customer data platforms, "
            "and modernization of legacy systems."
        )


    elif industry == "Healthcare":

        discovery = (
            "Explore patient data access, "
            "API workloads, "
            "application modernization, "
            "and healthcare interoperability."
        )


    elif industry == "Technology / SaaS":

        discovery = (
            "Explore multi-tenant architecture, "
            "developer velocity, "
            "API scalability, "
            "and cloud-native applications."
        )



    # =====================================================
    # SALES BRIEF
    # =====================================================

    sales_brief = f"""
{account} represents a potential Couchbase opportunity.

==================================================
ACCOUNT PROFILE
==================================================

Industry:
{industry}

Business Model:
{business_model}

Couchbase Opportunity Score:
{score}

Priority:
{priority}

Confidence:
{confidence}


==================================================
CURRENT ENVIRONMENT SIGNALS
==================================================

Database Pressure:
{database_pressure}


Modernization Signal:
{modernization_signal}


Likely Existing Databases:
{likely_db}


==================================================
TECHNOLOGY INTELLIGENCE
==================================================

Technology Signals:
{technology_text}

Technology Score:
{technology_score}

Cloud Signal:
{cloud_signal}

Database Signal:
{database_signal}

AI Signal:
{ai_signal}



==================================================
POTENTIAL WORKLOADS
==================================================

{workload_text}


==================================================
WHY COUCHBASE MAY FIT
==================================================

Potential Couchbase Use Cases:

{use_case_text}


Couchbase value hypothesis:

- Modernize operational applications
- Reduce complexity from legacy database platforms
- Support high availability and scalability
- Enable real-time application experiences



==================================================
TARGET BUYERS
==================================================

{persona_text}



==================================================
DISCOVERY QUESTIONS
==================================================

{discovery}

""".strip()



    # =====================================================
    # WHY RANKED
    # =====================================================

    why_ranked = []


    if industry != "Unknown":

        why_ranked.append(
            f"Industry fit: {industry}"
        )


    if business_model != "Unknown":

        why_ranked.append(
            f"Business model: {business_model}"
        )


    if database_pressure != "Unknown":

        why_ranked.append(
            f"Database pressure: {database_pressure}"
        )


    if modernization_signal != "Unknown":

        why_ranked.append(
            f"Modernization: {modernization_signal}"
        )


    if workloads:

        why_ranked.append(
            f"Operational workloads: {', '.join(workloads[:3])}"
        )


    if technology_signals:

        why_ranked.append(
            f"Technology signals: {', '.join(technology_signals[:3])}"
        )


    if ai_signal != "Unknown":

        why_ranked.append(
            f"AI opportunity: {ai_signal}"
        )


    if confidence == "High":

        why_ranked.append(
            "High confidence signals"
        )



    # =====================================================
    # AI ENRICHMENT DECISION
    # =====================================================

    ai_enrichment_recommended = False


    if (
        score >= 80
        and (
            technology_score >= 15
            or confidence in [
                "High",
                "Medium"
            ]
        )
    ):

        ai_enrichment_recommended = True



    # =====================================================
    # RETURN
    # =====================================================

    return {

        "priority": priority,

        "likely_databases": likely_db,

        "why_ranked": why_ranked,

        "ai_enrichment_recommended":
            ai_enrichment_recommended,

        "discovery_questions":
            discovery,

        "workload_summary":
            workload_text,

        "use_case_summary":
            use_case_text,

        "buyer_persona_summary":
            persona_text,

        "technology_summary":
            technology_text,

        "sales_brief":
            sales_brief

    }
