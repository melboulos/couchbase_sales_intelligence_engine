# =====================================================
# WEB SEARCH CLIENT
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Gives the LLM real, retrieved information about a company
# instead of relying purely on training-data memory. Confirmed
# via real testing this session: word-and-structure-level prompt
# constraints cannot fix genericness for accounts where the model
# has no real facts to draw from - the underlying problem is a
# lack of real INPUT, not insufficiently strict OUTPUT rules.
#
# Uses Serper.dev (a Google Search API wrapper). The API key is
# read from the SERPER_API_KEY environment variable - never
# hardcoded, never logged, never passed as a function argument
# from calling code that might print it.
#
# Usage:
#     from modules.web_search_client import search_company
#     context = search_company("Netspend")
# =====================================================

import os
import requests

SERPER_URL = "https://google.serper.dev/search"
REQUEST_TIMEOUT_SECONDS = 10
MAX_SNIPPETS = 3


def search_company(account_name, location=None):
    """
    Searches for the given company name and returns up to
    MAX_SNIPPETS clean text snippets, or None if the search failed
    for any reason (missing API key, network error, no results).

    location, if given (e.g. the account's State/Province field,
    already present in the raw data but previously unused), is
    appended to the query to disambiguate common company names.
    Confirmed necessary via real testing: "United Community Bank"
    returned a result for a DIFFERENT small Louisiana bank with the
    same generic name, not the actual ~100-branch southeastern
    regional bank the account refers to.

    Deliberately fails soft, not hard: a search failure should
    never crash the pipeline or block an account from being
    processed - it should just fall back to no web context, same
    as before this feature existed.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return None

    query = f"{account_name} company"
    if location:
        query = f"{account_name} {location} company"

    try:
        response = requests.post(
            SERPER_URL,
            headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
            json={"q": query},
            timeout=REQUEST_TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException:
        return None

    if response.status_code != 200:
        return None

    try:
        data = response.json()
    except ValueError:
        return None

    organic_results = data.get("organic", [])
    if not organic_results:
        return None

    snippets = []
    for result in organic_results[:MAX_SNIPPETS]:
        title = result.get("title", "").strip()
        snippet = result.get("snippet", "").strip()
        if title or snippet:
            snippets.append(f"{title}: {snippet}" if title and snippet else (title or snippet))

    return snippets if snippets else None


def format_web_context(snippets):
    """
    Formats search snippets into a block suitable for inserting
    directly into the intelligence prompt. Returns an empty string
    if there's nothing to format, so calling code can always safely
    concatenate the result without checking for None first.
    """
    if not snippets:
        return ""

    lines = "\n".join(f"- {s}" for s in snippets)
    return (
        "\n\nVERIFIED WEB SEARCH RESULTS (real, retrieved just now - "
        "treat as more reliable than your own training-data memory "
        "of this company):\n"
        f"{lines}\n"
    )
