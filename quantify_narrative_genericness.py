# =====================================================
# QUANTIFY NARRATIVE GENERICNESS
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# User observation, confirmed via manual sampling: LLM
# responses feel "very vanilla" - the same boilerplate phrases
# ("A distributed database with high availability, low
# latency...") appear across dozens of completely unrelated
# companies. This measures exactly how widespread that is,
# before deciding how much effort a fix deserves.
#
# Method: group accounts by the first ~8 words of
# couchbase_point_of_view (after stripping the account name so
# company-name substitution doesn't create false uniqueness),
# then report how many DISTINCT opening "signatures" exist
# across all qualified accounts, and what share of accounts
# fall under the most common ones.
#
# Usage:
#     python3 quantify_narrative_genericness.py
# =====================================================

import re
import pandas as pd

INPUT_FILE = "output/report1784905185024_Scored_FINAL.xlsx"
OUTPUT_FILE = "output/narrative_genericness_report.xlsx"

SIGNATURE_WORD_COUNT = 8


def make_signature(text, account_name):
    if not isinstance(text, str) or not text.strip():
        return ""
    # Remove the account name so "ensuring Netspend's core..." and
    # "ensuring Cleo's core..." are recognized as the same template
    # rather than counted as different signatures.
    cleaned = text.replace(str(account_name), "").lower()
    cleaned = re.sub(r"[^a-z0-9\s]", "", cleaned)
    words = cleaned.split()
    return " ".join(words[:SIGNATURE_WORD_COUNT])


print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)

qualified = accounts[accounts["llm_validation"] == True].copy()
# Only look at genuinely recognized accounts - caveated accounts all
# share the SAME caveat opening by design, which would just be noise
# here, not evidence of the model being generic when it does have
# real recognition.
verified = qualified[~qualified["llm_narrative_caveated"].isin([True, 1, 1.0])].copy()

print(f"Qualified accounts: {len(qualified)}")
print(f"Verified (non-caveated) accounts analyzed: {len(verified)}")

verified["pov_signature"] = verified.apply(
    lambda row: make_signature(row.get("couchbase_point_of_view", ""), row.get("Account Name", "")),
    axis=1
)

signature_counts = verified["pov_signature"].value_counts()

print()
print("=========================================================")
print("COUCHBASE POINT OF VIEW - OPENING SIGNATURE ANALYSIS")
print("=========================================================")
print(f"Distinct opening signatures: {len(signature_counts)}")
print(f"Total accounts analyzed: {len(verified)}")
print()

top_n = 15
print(f"Top {top_n} most common openings:")
cumulative = 0
for sig, count in signature_counts.head(top_n).items():
    pct = 100 * count / len(verified)
    cumulative += count
    print(f"  {count:>4} ({pct:>5.1f}%)  \"{sig}...\"")

cumulative_pct = 100 * cumulative / len(verified)
print()
print(f"Top {top_n} signatures together account for {cumulative} accounts "
      f"({cumulative_pct:.1f}% of all verified accounts)")

# Same analysis for engineering_implications first bullet, for
# comparison - is the narrative problem specific to the Couchbase
# POV section, or pervasive across all narrative fields?
import ast

def parse_field(value):
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value

def first_implication_signature(value, account_name):
    parsed = parse_field(value)
    text = parsed[0] if isinstance(parsed, list) and parsed else str(parsed)
    return make_signature(text, account_name)

verified["impl_signature"] = verified.apply(
    lambda row: first_implication_signature(row.get("engineering_implications", ""), row.get("Account Name", "")),
    axis=1
)
impl_counts = verified["impl_signature"].value_counts()

print()
print("=========================================================")
print("ENGINEERING IMPLICATIONS (first bullet) - SAME ANALYSIS")
print("=========================================================")
print(f"Distinct opening signatures: {len(impl_counts)}")
top_impl_cumulative = impl_counts.head(top_n).sum()
print(f"Top {top_n} signatures account for {top_impl_cumulative} accounts "
      f"({100*top_impl_cumulative/len(verified):.1f}%)")

verified[["Account Name", "priority_tier", "pov_signature", "impl_signature", "couchbase_point_of_view"]].to_excel(
    OUTPUT_FILE, index=False
)
print()
print(f"Saved full breakdown to: {OUTPUT_FILE}")
