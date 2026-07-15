import re


def normalize_account_name(name):

    if not isinstance(name, str):
        return ""

    name = name.lower()

    # remove punctuation
    name = re.sub(r'[^a-z0-9 ]', '', name)

    # remove common company suffixes
    remove_words = [
        "inc",
        "incorporated",
        "llc",
        "corp",
        "corporation",
        "company",
        "co"
    ]

    words = name.split()

    words = [
        word for word in words
        if word not in remove_words
    ]

    return " ".join(words).strip()
