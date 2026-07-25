# =====================================================
# CLASSIFICATION PROMPT BUILDER
# Couchbase Sales Intelligence Agent
#
# Purpose:
#
# For accounts the deterministic pipeline couldn't classify at
# all (industry == "Unknown", no workload_profile match), this
# builds a deliberately NARROW prompt: classify the named
# company into one of the existing workload_profile categories,
# or say "none" if the company isn't genuinely recognized.
#
# This is NOT a scoring prompt. It does not ask for COI, does
# not ask for engineering narrative. Its only job is to feed a
# real signal into the SAME, already-tuned deterministic
# scoring engine that everything else runs through - so a
# verified classification here gets scored exactly the same
# way a pattern-matched account would, including today's
# insurance_platform/pharma_device_platform rating fix.
#
# Same fact-verification discipline as the independent score
# (llm_specific_fact / llm_company_recognized): the model must
# name a genuine, checkable fact about the SPECIFIC company,
# not an industry guess from the name alone. Validated in code
# by validate_classification() in classification_pipeline.py -
# this prompt's own instructions are not trusted at face value.
# =====================================================

VALID_WORKLOAD_PROFILES = [
    "insurance_platform",
    "pharma_device_platform",
    "utilities_platform",
    "media_platform",
    "customer_application",
    "logistics_platform",
    "retail_platform",
    "saas_platform",
    "telecom_platform",
    "media_entertainment_platform",
    "api_platform",
    "mobile_application",
    "payment_platform",
]


def build_classification_prompt(account_name):
    profiles_list = "\n".join(f"- {p}" for p in VALID_WORKLOAD_PROFILES)

    return f"""
You are classifying ONE company by name, for a sales intelligence
pipeline. This is a classification task ONLY - you are not scoring
anything, not writing engineering analysis, not generating
discovery questions.

Account name: {account_name}

Do you specifically, genuinely recognize this named company - not
just a guess at its industry from how the name sounds, but the
actual company itself? To answer yes, you must be able to state
one concrete, checkable fact about it: a real product or platform
name, a real scale figure, a real market position, a known
acquisition, or similar.

A fact is NOT acceptable if it's really just an industry guess
restated ("this sounds like a logistics company", "likely a small
business"). If you cannot produce a genuine specific fact, you do
not recognize this company - say so plainly and do not guess.

If you genuinely recognize the company, choose the SINGLE
best-matching category from this exact list (copy the key exactly
as written, all lowercase with underscores). Only choose a category
if the company's actual TYPE of business fits it - a university,
law firm, accounting firm, meatpacking company, construction
company, or similar is essentially never a fit for ANY of these
categories, even if it is a large, well-known organization. Use
"none" for the category in that case too.
{profiles_list}

If you assigned a real category above, also judge: does this
SPECIFIC company's actual scale and technical sophistication put it
clearly ABOVE typical for that category, clearly BELOW typical, or
is it a TYPICAL example of that category? Base this on the same
concrete fact you already gave - do not introduce a new claim here.
Most companies are "typical" - only choose above/below if you have
real, specific evidence the company is unusually large/sophisticated
or unusually small/simple for its category.

Return ONLY this JSON, nothing else, no markdown, no explanation:
{{
  "llm_specific_fact": "one concrete fact about this named company, or the literal string NONE - not specifically recognized",
  "llm_company_recognized": true or false,
  "llm_workload_profile": "one of the exact category keys above, or none",
  "llm_scale_tier": "above_typical, below_typical, or typical"
}}
"""
