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
# RETRY/BACKOFF (added 2026-07-30): confirmed via a real production
# run that a heavy, fast, 5-concurrent burst (main.py processing
# 1,527 accounts, each making its own live Serper call independent
# of serper_enrichment_pass.py's cache) caused a 100% silent
# failure rate for this batch - 0 of 1,511 accounts with a valid
# location got a search result, despite a manual retest immediately
# after the run succeeding on the first try with zero issues. This
# is consistent with a transient rate-limit/quota ceiling being hit
# during the burst, silently swallowed by the original single-
# attempt soft-fail design (which had no way to distinguish "no
# results" from "got rate-limited"). Retries with exponential
# backoff now happen specifically for network exceptions and
# 429/5xx responses (transient, worth retrying) - NOT for other
# 4xx responses like 401/400 (a real config problem, retrying
# won't help and just adds latency for no benefit).
#
# Usage:
#     from modules.web_search_client import search_company
#     context = search_company("Netspend")
# =====================================================

import os
import time
import requests

SERPER_URL = "https://google.serper.dev/search"
REQUEST_TIMEOUT_SECONDS = 10
MAX_SNIPPETS = 3

MAX_RETRIES = 3
RETRY_BACKOFF_BASE_SECONDS = 2  # 1s, 2s between attempts (2^0, 2^1)


def search_company(account_name, location=None):
    """
    Searches for the given company name and returns up to
    MAX_SNIPPETS clean text snippets, or None if the search failed
    for any reason (missing API key, network error, no results,
    or all retries exhausted on a transient failure).

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
    as before this feature existed. Transient failures (network
    errors, rate limits, server errors) get retried with backoff
    first; a genuine 4xx config error does not retry, since more
    attempts won't fix a bad API key or malformed request.
    """
    api_key = os.environ.get("SERPER_API_KEY")
    if not api_key:
        return None

    query = f"{account_name} company"
    if location:
        query = f"{account_name} {location} company"

    for attempt in range(MAX_RETRIES):
        is_last_attempt = attempt == MAX_RETRIES - 1

        try:
            response = requests.post(
                SERPER_URL,
                headers={"X-API-KEY": api_key, "Content-Type": "application/json"},
                json={"q": query},
                timeout=REQUEST_TIMEOUT_SECONDS,
            )
        except requests.exceptions.RequestException:
            if is_last_attempt:
                return None
            time.sleep(RETRY_BACKOFF_BASE_SECONDS ** attempt)
            continue

        if response.status_code == 429 or response.status_code >= 500:
            # Rate-limited or transient server error - worth retrying
            if is_last_attempt:
                return None
            time.sleep(RETRY_BACKOFF_BASE_SECONDS ** attempt)
            continue

        if response.status_code != 200:
            # Other 4xx (bad key, malformed request) - retrying won't help
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

    return None


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
