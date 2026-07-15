def analyze_account_intelligence(row):

    industry = str(
        row.get(
            "industry",
            "Unknown"
        )
    )


    workloads = row.get(
        "workloads",
        []
    )


    if not isinstance(workloads, list):
        workloads = []


    business_model = str(
        row.get(
            "business_model",
            "Unknown"
        )
    )


    database_pressure = "Low"

    modernization_signal = "Low"

    couchbase_use_cases = []

    buyer_personas = []



    # =====================================================
    # FINANCIAL SERVICES
    # =====================================================

    if industry == "Financial Services":

        database_pressure = "High"

        modernization_signal = (
            "Legacy transaction platforms, "
            "customer data systems, real-time analytics"
        )


        couchbase_use_cases = [
            "Customer 360",
            "Fraud detection",
            "Real-time transaction applications",
            "Digital banking platforms"
        ]


        buyer_personas = [
            "CIO",
            "VP Engineering",
            "Enterprise Architect",
            "Data Architect"
        ]



    # =====================================================
    # HEALTHCARE
    # =====================================================

    elif industry == "Healthcare":

        database_pressure = "High"

        modernization_signal = (
            "Healthcare application modernization, "
            "API platforms, patient data access"
        )


        couchbase_use_cases = [
            "Patient 360",
            "Healthcare APIs",
            "Application modernization",
            "Real-time patient applications"
        ]


        buyer_personas = [
            "CIO",
            "VP Applications",
            "Chief Data Officer",
            "Enterprise Architect"
        ]



    # =====================================================
    # TECHNOLOGY / SAAS
    # =====================================================

    elif industry == "Technology / SaaS":

        database_pressure = "High"

        modernization_signal = (
            "Cloud-native applications, "
            "multi-tenant platforms, developer velocity"
        )


        couchbase_use_cases = [
            "Multi-tenant SaaS",
            "Operational applications",
            "Real-time APIs",
            "Application scalability"
        ]


        buyer_personas = [
            "CTO",
            "VP Engineering",
            "Platform Engineering",
            "Software Architects"
        ]



    # =====================================================
    # RETAIL
    # =====================================================

    elif industry == "Retail":

        database_pressure = "Medium"

        modernization_signal = (
            "Commerce modernization, "
            "customer engagement systems"
        )


        couchbase_use_cases = [
            "Customer 360",
            "Personalization",
            "Commerce applications"
        ]


        buyer_personas = [
            "CIO",
            "Digital Transformation Leader",
            "VP Engineering"
        ]



    # =====================================================
    # GENERAL CLOUD SIGNAL
    # =====================================================

    cloud_signal = str(
        row.get(
            "cloud_signal",
            "Unknown"
        )
    )


    if cloud_signal == "Cloud":

        modernization_signal += (
            ". Existing cloud adoption indicates "
            "modernization readiness."
        )



    # =====================================================
    # WORKLOAD BOOST
    # =====================================================

    if workloads:

        database_pressure = "High"



    return {

        "database_pressure": database_pressure,

        "modernization_signal": modernization_signal,

        "couchbase_use_cases": couchbase_use_cases,

        "buyer_personas": buyer_personas

    }
