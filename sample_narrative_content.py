# =====================================================
# RANDOM SAMPLE: FULL NARRATIVE CONTENT (rep-facing)
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Pulls a random sample of the ACTUAL Call Brief content a rep
# would read - engineering_implications, couchbase_point_of_view,
# and the discovery questions - not just the fact/score fields we
# already checked. This is the real deliverable per the mission
# statement's own framing: the score is a prioritization mechanism,
# the narrative is the actual seller intelligence.
#
# Usage:
#     python3 sample_narrative_content.py
# =====================================================

import ast
import pandas as pd

CHECKPOINT_FILE = "output/llm_validation_results.xlsx"
OUTPUT_FILE = "output/narrative_content_sample.xlsx"
SAMPLE_SIZE = 40
RANDOM_SEED = 7


def is_true(value):
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1.0:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


def parse_field(value):
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def flatten_implications(value):
    parsed = parse_field(value)
    if isinstance(parsed, list):
        return " | ".join(str(x) for x in parsed)
    return str(parsed)


def flatten_discovery(value):
    parsed = parse_field(value)
    if not isinstance(parsed, list):
        return str(parsed)
    lines = []
    for phase in parsed:
        if isinstance(phase, dict):
            obj = phase.get("objective", "")
            questions = phase.get("questions", [])
            lines.append(f"[{obj}] " + " / ".join(questions))
    return " || ".join(lines)


print(f"Loading: {CHECKPOINT_FILE}")
df = pd.read_excel(CHECKPOINT_FILE)

validated = df[df["llm_validation"].apply(is_true)]
verified = validated[validated["llm_recognition_verified"].apply(is_true)]

print(f"Total validated: {len(validated)}")
print(f"Verified: {len(verified)}")

sample_size = min(SAMPLE_SIZE, len(verified))
sample = verified.sample(n=sample_size, random_state=RANDOM_SEED).copy()

sample["implications_flat"] = sample["engineering_implications"].apply(flatten_implications)
sample["discovery_flat"] = sample["discovery_progression"].apply(flatten_discovery)

display_cols = [
    "Account Name", "llm_specific_fact", "implications_flat",
    "couchbase_point_of_view", "discovery_flat",
]
display_cols = [c for c in display_cols if c in sample.columns]
sample_out = sample[display_cols].reset_index(drop=True)
sample_out.to_excel(OUTPUT_FILE, index=False)

print(f"\nPulled {len(sample_out)} accounts. Saved to: {OUTPUT_FILE}\n")

for i, row in sample_out.iterrows():
    print(f"========== [{i+1}] {row['Account Name']} ==========")
    print(f"FACT: {row.get('llm_specific_fact')}")
    print(f"ENGINEERING IMPLICATIONS: {row.get('implications_flat')}")
    print(f"COUCHBASE POV: {row.get('couchbase_point_of_view')}")
    print(f"DISCOVERY: {row.get('discovery_flat')}")
    print()
