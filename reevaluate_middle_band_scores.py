# =====================================================
# REEVALUATE MIDDLE-BAND SCORES
# Couchbase Sales Intelligence Engine
#
# Purpose:
#
# Targets ONLY the middle band: verified accounts that cited real
# evidence (passed the ungrounded check) but had no extractable
# dollar figure or employee count for the magnitude-based code
# correction to grab onto. Confirmed via query_middle_band_size.py:
# this is 481 of 580 grounded accounts (83%) - the DOMINANT
# uncorrected category, not an edge case.
#
# Gives the model a second, narrower pass: instead of generating
# everything fresh again, it's shown its own prior fact and score
# and asked specifically whether they match - a different cognitive
# task than open-ended generation, which may behave differently.
#
# Real, small cost - this is a short, focused prompt (~400 tokens/
# call), not the full intelligence generation. Threaded and
# checkpointed the same way as everything else this session.
#
# IMPORTANT: only run when rerun_qualified_with_search.py is NOT
# actively running - a still-running process periodically overwrites
# the entire checkpoint file from its own in-memory snapshot,
# silently erasing whatever this script does (confirmed the hard
# way earlier this session).
#
# Usage:
#     python3 reevaluate_middle_band_scores.py
# =====================================================

import concurrent.futures
import time
import pandas as pd

from modules.llm_client import call_llm
from modules.llm_prompt_builder import build_score_reevaluation_prompt
from modules.sales_intelligence_pipeline import apply_magnitude_based_score_adjustment, determine_if_default_score, detect_ungrounded_score

CHECKPOINT_FILE = "output/llm_validation_results.xlsx"
MAX_WORKERS = 5
CHECKPOINT_EVERY = 25

COST_PER_1K_TOKENS = 0.00072


def is_true(value):
    if value is True:
        return True
    if isinstance(value, (int, float)) and value == 1.0:
        return True
    if isinstance(value, str) and value.strip().lower() == "true":
        return True
    return False


def reevaluate_one_account(row_dict):
    name = row_dict["Account Name"]
    fact = row_dict.get("llm_specific_fact", "")
    workload = int(row_dict.get("llm_workload_score", 0) or 0)
    realtime = int(row_dict.get("llm_realtime_score", 0) or 0)
    complexity = int(row_dict.get("llm_complexity_score", 0) or 0)

    prompt = build_score_reevaluation_prompt(name, fact, workload, realtime, complexity)

    try:
        result = call_llm(prompt)
    except Exception as e:
        return {"Account Name": name, "llm_reeval_error": str(e)}

    # Validate ranges - don't trust the model to stay in bounds
    for field, max_val in [("llm_workload_score", 40), ("llm_realtime_score", 30), ("llm_complexity_score", 30)]:
        try:
            value = int(result.get(field, 0))
        except (ValueError, TypeError):
            value = 0
        result[field] = max(0, min(max_val, value))

    result["llm_total_score"] = (
        result["llm_workload_score"] + result["llm_realtime_score"] + result["llm_complexity_score"]
    )
    result["Account Name"] = name
    result["llm_score_reevaluated"] = True
    result["llm_total_score_before_reeval"] = workload + realtime + complexity

    # Re-derive ungrounded status fresh using the NEW reasoning text,
    # then re-apply the code-enforced magnitude check on top - real,
    # extractable evidence still wins regardless of what this
    # re-evaluation concluded. Also sets the final, transparent
    # default-score label consistently for every account.
    result["llm_specific_fact"] = fact
    result["llm_recognition_verified"] = row_dict.get("llm_recognition_verified")
    result["llm_score_reasoning"] = result.get("llm_reeval_reasoning", "")
    detect_ungrounded_score(result)
    apply_magnitude_based_score_adjustment(result)
    determine_if_default_score(result)

    # Core rule: an INCREASE from re-evaluation only sticks if backed
    # by real dollar evidence. Confirmed necessary via real testing:
    # Tube City IMS went 65 -> 85 justified only by "80 customer
    # sites in 13 countries" - geographic/site-count claims that
    # sound impressive but don't reliably measure the thing we
    # actually care about (money/data volume moving through the
    # business), the same failure as the US Air Force case being
    # floored up on headcount alone. Decreases are NOT gated here -
    # "this sounds like a small, narrow operation" is a safer
    # inference to trust than "this sounds big," so only increases
    # need dollar-backed proof.
    before_total = result["llm_total_score_before_reeval"]
    after_total = result["llm_total_score"]

    if after_total > before_total and result.get("llm_magnitude_bucket") != "large":
        result["llm_workload_score"] = workload
        result["llm_realtime_score"] = realtime
        result["llm_complexity_score"] = complexity
        result["llm_total_score"] = before_total
        result["llm_increase_reverted"] = True
        result["llm_reeval_reasoning"] = (
            str(result.get("llm_reeval_reasoning", "")) +
            " [CODE-ENFORCED REVERT: re-evaluation tried to raise "
            "this score without citing a real dollar figure - "
            "reverted to the original score, since only revenue/"
            "assets/transaction-volume evidence is trusted to "
            "justify an increase.]"
        )
    else:
        result["llm_increase_reverted"] = False

    return result


print(f"Loading: {CHECKPOINT_FILE}")
df = pd.read_excel(CHECKPOINT_FILE)

validated = df[df["llm_validation"].apply(is_true)].copy()
# Widened to ALL verified accounts, not just the middle band -
# every account should go through the same consistent process
# (re-evaluation, then the code-enforced magnitude floor/ceiling as
# a final check on top of it). Unverified accounts are still
# correctly excluded - there's no real fact to re-evaluate against.
to_evaluate_pool = validated[validated["llm_recognition_verified"].apply(is_true)].copy()

if "llm_score_reevaluated" in df.columns:
    already_done_names = set(df[df["llm_score_reevaluated"].apply(is_true)]["Account Name"])
else:
    already_done_names = set()
    df["llm_score_reevaluated"] = False

to_process = to_evaluate_pool[~to_evaluate_pool["Account Name"].isin(already_done_names)]

print(f"All verified accounts: {len(to_evaluate_pool)}")
print(f"Already re-evaluated (resuming, skipping these): {len(already_done_names)}")
print(f"To process now: {len(to_process)}")

if len(to_process) == 0:
    print("Nothing left to process.")
    raise SystemExit()

results = []
completed = 0
total = len(to_process)
start_time = time.time()

TARGET_COLS = [
    "llm_workload_score", "llm_realtime_score", "llm_complexity_score",
    "llm_total_score", "llm_score_reevaluated", "llm_total_score_before_reeval",
    "llm_reeval_changed", "llm_reeval_reasoning", "llm_magnitude_bucket",
    "llm_score_is_default", "llm_increase_reverted",
]
for col in TARGET_COLS:
    if col in df.columns:
        df[col] = df[col].astype(object)
    else:
        df[col] = None

print(f"Running threaded re-evaluation ({MAX_WORKERS} concurrent, checkpoint every {CHECKPOINT_EVERY})...")

with concurrent.futures.ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
    futures = {
        executor.submit(reevaluate_one_account, row.to_dict()): row["Account Name"]
        for _, row in to_process.iterrows()
    }

    for future in concurrent.futures.as_completed(futures):
        name = futures[future]
        try:
            result = future.result()
        except Exception as e:
            result = {"Account Name": name, "llm_reeval_error": f"Worker exception: {e}"}

        results.append(result)
        completed += 1

        idx = df[df["Account Name"] == name].index
        if len(idx) > 0:
            for col in TARGET_COLS:
                if col in result:
                    df.at[idx[0], col] = result[col]

        if completed % CHECKPOINT_EVERY == 0 or completed == total:
            df.to_excel(CHECKPOINT_FILE, index=False)
            elapsed = time.time() - start_time
            print(f"[{completed}/{total}] checkpoint saved, {elapsed:.0f}s elapsed")

print(f"\nRe-evaluation complete: {completed}/{total}")

changed_count = sum(1 for r in results if r.get("llm_reeval_changed") is True)
print(f"Scores actually changed: {changed_count} / {completed} ({100*changed_count/completed:.1f}%)")

total_tokens = sum(r.get("llm_total_tokens", 0) or 0 for r in results)
total_cost = (total_tokens / 1000) * COST_PER_1K_TOKENS
print(f"Total tokens: {total_tokens:,}")
print(f"Total cost: ${total_cost:.4f}")

df.to_excel(CHECKPOINT_FILE, index=False)
print(f"\nSaved: {CHECKPOINT_FILE}")
