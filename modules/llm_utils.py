from datetime import datetime, timezone


LLM_RUN_ID = datetime.now(
    timezone.utc
).strftime(
    "%Y%m%d_%H%M%S"
)


def get_usage_value(response, key):

    if not response:
        return 0

    if key in response:
        return response.get(
            key,
            0
        )

    usage = response.get(
        "usage",
        {}
    )

    return usage.get(
        key,
        0
    )


def get_model_name(response):

    if not response:
        return "Unknown"

    return (
        response.get("model_id")
        or response.get("model")
        or response.get("modelId")
        or "Unknown"
    )
