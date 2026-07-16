import json
import re


def extract_json(text):

    if isinstance(text, dict):
        return normalize_llm_result(text)


    text = str(text)


    text = (
        text
        .replace("：", ":")
        .replace("\r", "")
        .replace("```json", "")
        .replace("```", "")
        .strip()
    )


    # Remove llama headers
    text = re.sub(
        r"<\|.*?\|>",
        "",
        text,
        flags=re.DOTALL
    ).strip()


    # Find JSON object
    match = re.search(
        r"\{.*\}",
        text,
        flags=re.DOTALL
    )


    if not match:

        raise ValueError(
            f"No JSON found. Raw response: {text[:500]}"
        )


    json_text = match.group(0)


    result = json.loads(
        json_text
    )


    return normalize_llm_result(
        result
    )



def normalize_llm_result(result):

    list_fields = [
        "reasoning",
        "score_blockers",
        "strongest_signals",
        "weakest_assumptions",
        "required_discovery_questions"
    ]


    for field in list_fields:

        value = result.get(
            field
        )


        if isinstance(
            value,
            str
        ):

            if (
                value.startswith("[")
                and
                value.endswith("]")
            ):

                try:

                    result[field] = json.loads(
                        value.replace(
                            "'",
                            '"'
                        )
                    )

                except Exception:

                    result[field] = [
                        value
                    ]

            else:

                result[field] = [
                    value
                ]


    return result
