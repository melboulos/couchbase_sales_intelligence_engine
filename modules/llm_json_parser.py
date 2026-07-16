import json
import re


def extract_json(text):

    if isinstance(text, dict):
        return text


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


    return json.loads(
        json_text
    )
