import re


def normalize_account_name(name):

    if not isinstance(name, str):

        return ""


    name = name.lower()


    # Remove punctuation
    name = re.sub(
        r"[^a-z0-9\s]",
        "",
        name
    )


    # Remove common company suffixes
    suffixes = [

        " inc",
        " incorporated",
        " llc",
        " ltd",
        " limited",
        " lp",
        " corp",
        " corporation",
        " company",
        " co"

    ]


    for suffix in suffixes:

        if name.endswith(suffix):

            name = name.replace(
                suffix,
                ""
            )


    # Normalize whitespace

    name = re.sub(
        r"\s+",
        " ",
        name
    )


    return name.strip()
