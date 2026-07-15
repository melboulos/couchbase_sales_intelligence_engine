def generate_opportunity_explanation(row):


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



    account = safe_value(
        "Account Name"
    )


    industry = safe_value(
        "industry"
    )


    business_model = safe_value(
        "business_model"
    )


    database_signal = safe_value(
        "database_signal"
    )


    technology_signals = row.get(
        "technology_signals",
        []
    )


    if not isinstance(
        technology_signals,
        list
    ):

        technology_signals = []



    workloads = row.get(
        "workloads",
        []
    )


    if not isinstance(
        workloads,
        list
    ):

        workloads = []



    # =====================================================
    # INDUSTRY MESSAGING
    # =====================================================


    if industry == "Financial Services":

        industry_message = (
            "Financial services organizations often require "
            "high availability, low latency transactions, "
            "customer data platforms, and real-time analytics."
        )


    elif industry == "Healthcare":

        industry_message = (
            "Healthcare organizations often manage "
            "complex patient applications, interoperability "
            "requirements, and rapidly growing data workloads."
        )


    elif industry == "Technology / SaaS":

        industry_message = (
            "Software companies typically require "
            "scalable application databases, flexible schemas, "
            "and developer-friendly operational platforms."
        )


    else:

        industry_message = (
            "The account shows potential operational "
            "application and modernization opportunities."
        )



    # =====================================================
    # TECHNOLOGY SIGNALS
    # =====================================================

    if technology_signals:

        technology_message = (
            "Technology indicators include: "
            +
            ", ".join(
                technology_signals[:5]
            )
            +
            "."
        )


    else:

        technology_message = (
            "Additional technical discovery is recommended "
            "to identify database and modernization opportunities."
        )



    # =====================================================
    # WORKLOAD SIGNALS
    # =====================================================

    if workloads:

        workload_message = (
            "Potential workloads: "
            +
            ", ".join(
                workloads[:5]
            )
            +
            "."
        )


    else:

        workload_message = (
            "Likely workloads include operational applications, "
            "customer data, and real-time services."
        )



    # =====================================================
    # DATABASE MESSAGE
    # =====================================================

    database_message = (
        f"Current database pressure signal: "
        f"{database_signal}."
    )



    # =====================================================
    # FINAL EXPLANATION
    # =====================================================


    explanation = f"""

{account} represents a potential Couchbase opportunity.

Business profile:
{business_model}

Industry fit:
{industry}

Why Couchbase may fit:

- {industry_message}

- {technology_message}

- {workload_message}

- {database_message}

Potential Couchbase value:

- Modernize operational applications
- Support high-performance real-time workloads
- Reduce database complexity
- Enable scalable application development
- Provide a foundation for AI-enabled experiences

""".strip()



    return {

        "opportunity_explanation":
            explanation

    }
