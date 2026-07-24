# =====================================================
# FULL TIER 4 REVIEW
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# The random 40-account sample already showed a real,
# systemic coverage gap (~25% of a random sample were
# unmistakable large enterprises with zero recognition).
# This script extracts the FULL Tier 4 population (all
# ~9,000+ accounts, not just a sample) and organizes it
# into a multi-sheet workbook, prioritized so the highest-
# value review happens first instead of scanning blind:
#
# Sheet 1 "Priority - Partial Signal": accounts that
#   already scored SOME points (overall_coi > 0). The
#   engine detected something but not enough to clear
#   Tier 3/40 points - these are the cheapest wins, since
#   partial recognition already exists and likely just
#   needs a stronger pattern/known_companies entry.
#
# Sheet 2 "Priority - Institutional Pattern": accounts
#   with ZERO signal, but whose NAME structurally suggests
#   a large institution (university, hospital, city/county/
#   state government, school district, etc.) - these don't
#   require recognizing the brand, just the naming pattern,
#   and institutions of this type are almost always real,
#   large, enterprise-caliber accounts.
#
# Sheet 3+ "Remaining - Chunk N": everything else, split
#   into manageable chunks (default 500 rows/sheet) and
#   sorted alphabetically, so a systematic scan is possible
#   instead of relying on random sampling.
#
# Usage:
#     python3 review_tier4_full.py
# =====================================================

import pandas as pd

INPUT_FILE = "output/precursor_review.xlsx"
OUTPUT_FILE = "output/tier4_full_review.xlsx"

CHUNK_SIZE = 500

DISPLAY_COLUMNS = [
    "Account Name",
    "industry",
    "financial_segment",
    "company_archetype",
    "workload_profile",
    "overall_coi",
    "gate_reason",
    "signals_found",
    "debug_text_sample",
]

# Naming patterns that structurally suggest a large
# institution regardless of brand recognition. Case-
# insensitive substring match against the account name.
INSTITUTIONAL_PATTERNS = [
    "university", "college", "school district",
    "hospital", "medical center", "health system",
    "healthcare system", "clinic",
    "city of", "county of", "state of", "town of",
    "department of", "ministry of", "government of",
    "public schools", "board of education",
]


def is_institutional(name):
    name_lower = str(name).lower()
    return any(pattern in name_lower for pattern in INSTITUTIONAL_PATTERNS)


print(f"Loading: {INPUT_FILE}")
accounts = pd.read_excel(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts")

if "priority_tier" not in accounts.columns:
    raise SystemExit(
        "No 'priority_tier' column found - is this really the "
        "precursor_review.py output file?"
    )

tier4 = accounts[accounts["priority_tier"] == "Tier 4 Monitor"].copy()
print(f"Tier 4 Monitor accounts: {len(tier4)}")

display_cols = [c for c in DISPLAY_COLUMNS if c in tier4.columns]
tier4 = tier4[display_cols]

# Dedupe on exact account name - keeps the review list
# shorter without losing anything (if truly the same name
# appears twice, reviewing it once is enough to flag the
# pattern gap).
before_dedup = len(tier4)
tier4 = tier4.drop_duplicates(subset="Account Name", keep="first")
print(f"After removing exact duplicate names: {len(tier4)} "
      f"(removed {before_dedup - len(tier4)} duplicates)")

# -----------------------------------------------------
# SPLIT INTO PRIORITY GROUPS
# -----------------------------------------------------

has_coi = tier4["overall_coi"].fillna(0) > 0 if "overall_coi" in tier4.columns else pd.Series([False] * len(tier4))
partial_signal = tier4[has_coi].sort_values("overall_coi", ascending=False)

remaining_after_signal = tier4[~has_coi]

institutional_mask = remaining_after_signal["Account Name"].apply(is_institutional)
institutional = remaining_after_signal[institutional_mask].sort_values("Account Name")

remaining = remaining_after_signal[~institutional_mask].sort_values("Account Name")

print()
print(f"Priority - Partial Signal (overall_coi > 0): {len(partial_signal)}")
print(f"Priority - Institutional Pattern:             {len(institutional)}")
print(f"Remaining (needs manual scan):                {len(remaining)}")

# -----------------------------------------------------
# WRITE MULTI-SHEET WORKBOOK
# -----------------------------------------------------

with pd.ExcelWriter(OUTPUT_FILE, engine="openpyxl") as writer:

    partial_signal.to_excel(
        writer, sheet_name="Priority - Partial Signal", index=False
    )

    institutional.to_excel(
        writer, sheet_name="Priority - Institutional", index=False
    )

    num_chunks = max(1, (len(remaining) + CHUNK_SIZE - 1) // CHUNK_SIZE)
    for i in range(num_chunks):
        chunk = remaining.iloc[i * CHUNK_SIZE : (i + 1) * CHUNK_SIZE]
        sheet_name = f"Remaining - Chunk {i + 1}"
        chunk.to_excel(writer, sheet_name=sheet_name, index=False)

print()
print(f"Saved: {OUTPUT_FILE}")
print(f"  - 1 sheet:  Priority - Partial Signal ({len(partial_signal)} accounts)")
print(f"  - 1 sheet:  Priority - Institutional ({len(institutional)} accounts)")
print(f"  - {num_chunks} sheet(s): Remaining - Chunk 1..{num_chunks} "
      f"({len(remaining)} accounts, {CHUNK_SIZE}/sheet)")
print()
print("REVIEW ORDER RECOMMENDATION:")
print("1. 'Priority - Partial Signal' first - these already have SOME")
print("   engine recognition (overall_coi > 0, sorted highest first).")
print("   Fastest, highest-confidence wins for pattern additions.")
print("2. 'Priority - Institutional' second - universities, hospitals,")
print("   government entities. Almost always real, large accounts,")
print("   regardless of whether you personally recognize the name.")
print("3. 'Remaining - Chunk N' sheets last, alphabetically sorted,")
print("   for a systematic scan of everything else.")
