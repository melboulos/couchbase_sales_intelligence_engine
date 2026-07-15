def generate_explanation(row):

    industry = str(
        row.get(
            "industry",
            "Unknown"
        )
    )

    business_model = str(
        row.get(
            "business_model",
            "Unknown"
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

    ai = str(
        row.get(
            "ai_initiatives",
            "Unknown"
        )
    )

    cloud = str(
        row.get(
            "cloud_signal",
            "Unknown"
        )
    )

    database = str(
        row.get(
            "database_signal",
            "Unknown"
        )
    )


    # Lists from company patterns
    workloads = row.get(
        "workloads",
        []
    )

    if not isinstance(workloads, list):
        workloads = []


    reasons = []


    # Company profile
    if industry != "Unknown":
        reasons.append(
            f"Industry: {industry}"
        )


    if business_model != "Unknown":
        reasons.append(
            f"Business model: {business_model}"
        )


    # Workload intelligence
    if workloads:
        reasons.append(
            "Workloads: "
            + ", ".join(workloads)
        )


    # Technology signals
    technology = []

    if cloud != "Unknown":
        technology.append(cloud)

    if database != "Unknown":
        technology.append(database)

    if technology:
        reasons.append(
            "Technology signals: "
            + ", ".join(technology)
        )


    # Engineering maturity
    if engineering == "High":
        reasons.append(
            "Strong engineering organization"
        )


    # AI signals
    if ai != "Unknown":
        reasons.append(
            ai
        )


    if len(reasons) == 0:
        return (
            "Limited intelligence available. "
            "Additional enrichment recommended."
        )


    explanation = (
        "Potential Couchbase opportunity.\n\n"
        + "\n".join(
            "- " + r
            for r in reasons
        )
        + "\n\n"
        "Couchbase fit: "
        "Real-time applications requiring "
        "low latency data access, flexible schemas, "
        "and highly available operational databases."
    )


    return explanation
