# =====================================================
# OWNERSHIP SIGNAL DETECTOR
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Confirmed via real data (2026-07-31): 511 of 9,750 cached account
# search snippets (5.2%) already contain a real ownership-change or
# rebrand signal phrase - Cardtronics/NCR Atleos, PrimePay/CoAd,
# GroupM/WPP Media, DSC Logistics/CJ Logistics America, and
# Business & Decision/Mi-Case were all found as real, confirmed
# examples this session, not hypothetical cases.
#
# This is a free, deterministic text-scan over data already paid
# for by serper_enrichment_pass.py's cache - no new search cost,
# no new LLM cost. Deliberately kept as a standalone module rather
# than folded into company_intelligence.py's already-large
# industry/business_model matching cascade, since this answers a
# genuinely different question ("who owns this account right now")
# that has nothing to do with what industry or workload category
# an account falls into.
#
# Runs unconditionally on every account with cached search data,
# regardless of whether industry/business_model classification
# succeeded via name or web-search fallback - ownership status is
# an independent question from industry fit.
#
# Usage:
#     from modules.ownership_signal_detector import detect_ownership_signal
#     result = detect_ownership_signal(row)
# =====================================================

OWNERSHIP_SIGNAL_PHRASES = [
    "is now ",
    "now part of",
    "now operates as",
    "now known as",
    "rebrand",
    "was acquired by",
    "acquired by",
    "merged with",
    "now a division of",
    "formerly known as",
]


def detect_ownership_signal(row):
    """
    Scans the row's cached web_search_snippets (populated by
    serper_enrichment_pass.py, merged into the accounts DataFrame
    by main.py) for ownership-change/rebrand signal phrases.

    Returns a dict with:
      - ownership_signal_detected (bool)
      - ownership_signal_note (str): a short excerpt of surrounding
        context around the first matched phrase, or empty string
        if nothing was found. Deliberately returns only the FIRST
        match, not every match, to keep the note short and scannable
        on a Call Brief rather than a wall of matched fragments.

    Deliberately simple, deterministic, no LLM involved - this is
    NOT asking a model to judge or summarize anything, just a plain
    substring scan over already-retrieved text.
    """
    snippet = str(row.get("web_search_snippets", "") or "")
    snippet_lower = snippet.lower()

    for phrase in OWNERSHIP_SIGNAL_PHRASES:
        idx = snippet_lower.find(phrase)
        if idx != -1:
            start = max(0, idx - 40)
            end = min(len(snippet), idx + len(phrase) + 60)
            context = snippet[start:end].strip()
            return {
                "ownership_signal_detected": True,
                "ownership_signal_note": context,
            }

    return {
        "ownership_signal_detected": False,
        "ownership_signal_note": "",
    }
