# =====================================================
# LLM PROMPT TEST
# Couchbase Sales Intelligence Engine
#
# Debug Purpose:
#
# Track:
# - deterministic gate decision
# - qualification LLM execution
# - intelligence LLM execution
# - token usage
# - RAW LLM JSON returned
#
# NOTE:
# This test re-runs company_intelligence.analyze_company()
# and scoring_engine.calculate_coi() live for each test
# account, rather than trusting the values already sitting
# in Enterprise_East_Scored.xlsx. That file is a static
# snapshot from a prior pipeline run and will not reflect
# any fixes made to enrichment or scoring logic since it
# was generated. Account identity fields (Account Name,
# industry raw source data, etc.) still come from the
# snapshot; workload/COI/tier fields are recomputed fresh.
# =====================================================


import pandas as pd
import json


from modules.sales_intelligence_pipeline import validate_account
from modules.company_intelligence import analyze_company
from modules.scoring_engine import calculate_coi

import modules.deterministic_gate as deterministic_gate_module


# =====================================================
# TEST-ONLY GATE OVERRIDE
#
# Some of the most useful calibration test accounts
# (small regional banks) are normally, correctly,
# excluded by the real deterministic gate before ever
# reaching the LLM. That's the right behavior in
# production, but it means we can't observe how the LLM
# scores them without forcing them through for this test.
#
# This monkeypatches deterministic_gate.deterministic_gate
# ONLY inside this test process, so run_llm is forced True
# for the accounts below regardless of what the real gate
# logic would decide. It never modifies the real
# modules/deterministic_gate.py file on disk.
# =====================================================

FORCE_LLM_OVERRIDE = [
    "Trumid Financial",
    "United Community Bank",
    "Members 1st Federal Credit Union"
]

_real_deterministic_gate = deterministic_gate_module.deterministic_gate


def _test_deterministic_gate(row):
    gate_result = _real_deterministic_gate(row)

    if row.get("Account Name") in FORCE_LLM_OVERRIDE:
        gate_result = dict(gate_result)
        gate_result["run_llm"] = True
        gate_result["gate_reason"] = (
            str(gate_result.get("gate_reason", "")) +
            " [TEST OVERRIDE: forced through gate for "
            "calibration testing]"
        )

    return gate_result


deterministic_gate_module.deterministic_gate = _test_deterministic_gate


# =====================================================
# FILES
# =====================================================


INPUT_FILE = (
    "output/"
    "report1784905185024_Scored_FINAL.xlsx"
)


OUTPUT_FILE = (
    "output/"
    "llm_prompt_test.xlsx"
)



# =====================================================
# TEST ACCOUNTS
# =====================================================


TEST_ACCOUNTS = [

    "Netspend",

    "Paytronix Systems",

    "Cleo",

    "Redox",

    "Staywell",

    "PeopleAdmin",

    "OpenKey",

    "Members 1st Federal Credit Union",

    "United Community Bank",

    "Trumid Financial"

]



# =====================================================
# LOAD
# =====================================================


print(
    "Loading accounts..."
)


accounts = pd.read_excel(
    INPUT_FILE
)



test_accounts = accounts[

    accounts["Account Name"]
    .isin(TEST_ACCOUNTS)

]



print(
    f"Testing {len(test_accounts)} accounts"
)



# =====================================================
# RUN
# =====================================================


results = []



for _, row in test_accounts.iterrows():


    row = row.to_dict()


    # =================================================
    # RE-RUN ENRICHMENT + SCORING LIVE
    #
    # INPUT_FILE is a static snapshot from a prior run.
    # Re-running these here ensures we test against
    # current company_intelligence.py / scoring_engine.py
    # logic, not stale pre-fix data.
    # =================================================

    enrichment = analyze_company(row)

    row.update(enrichment)


    coi_result = calculate_coi(row)

    row.update(coi_result)



    print()

    print(
        "=========================="
    )

    print(
        "ACCOUNT:",
        row["Account Name"]
    )


    print(
        "COI:",
        row.get(
            "overall_coi",
            ""
        )
    )


    print(
        "TIER:",
        row.get(
            "priority_tier",
            ""
        )
    )


    print(
        "WORKLOAD PROFILE:",
        row.get(
            "workload_profile",
            ""
        )
    )


    print(
        "WORKLOAD STRENGTH:",
        row.get(
            "workload_strength",
            ""
        )
    )


    print(
        "DATABASE INTENSITY:",
        row.get(
            "database_intensity",
            ""
        )
    )


    print(
        "OPERATIONAL COMPLEXITY:",
        row.get(
            "operational_complexity",
            ""
        )
    )


    print(
        "REALTIME REQUIREMENT:",
        row.get(
            "realtime_requirement",
            ""
        )
    )


    print(
        "Calling validate_account..."
    )



    result = validate_account(
        row
    )



    # =================================================
    # RAW RESULT
    # =================================================


    print()

    print(
        "---------- RAW RETURNED JSON ----------"
    )


    print(

        json.dumps(

            result,

            indent=4,

            default=str

        )

    )


    print(
        "---------------------------------------"
    )



    # =================================================
    # DEBUG
    # =================================================


    print()

    print(
        "---------- DEBUG ----------"
    )


    debug_fields = [

        "gate_decision",

        "gate_reason",

        "gate_score",

        "qualification_result",

        "qualification_score",

        "qualification_reason",

        "llm_validation",

        "llm_error",

    ]



    for field in debug_fields:


        print(

            f"{field}:",

            result.get(
                field,
                "NOT_RETURNED"
            )

        )



    print()


    print(
        "QUALIFICATION TOKENS"
    )


    print(
        "Input:",
        result.get(
            "qualification_input_tokens",
            0
        )
    )


    print(
        "Output:",
        result.get(
            "qualification_output_tokens",
            0
        )
    )


    print(
        "Total:",
        result.get(
            "qualification_total_tokens",
            0
        )
    )



    print()


    print(
        "INTELLIGENCE TOKENS"
    )


    print(
        "Input:",
        result.get(
            "intelligence_input_tokens",
            0
        )
    )


    print(
        "Output:",
        result.get(
            "intelligence_output_tokens",
            0
        )
    )


    print(
        "Total:",
        result.get(
            "intelligence_total_tokens",
            0
        )
    )



    print()


    print(
        "TOTAL TOKENS:",
        result.get(
            "llm_total_tokens",
            0
        )
    )


    print(
        "--------------------------"
    )



    results.append(

        {

            "Account Name":

                row["Account Name"],


            "overall_coi":

                row.get(
                    "overall_coi",
                    ""
                ),


            "priority_tier":

                row.get(
                    "priority_tier",
                    ""
                ),


            "workload_profile":

                row.get(
                    "workload_profile",
                    ""
                ),


            "workload_strength":

                row.get(
                    "workload_strength",
                    ""
                ),


            "database_intensity":

                row.get(
                    "database_intensity",
                    ""
                ),


            "operational_complexity":

                row.get(
                    "operational_complexity",
                    ""
                ),


            "realtime_requirement":

                row.get(
                    "realtime_requirement",
                    ""
                ),


            **result

        }

    )



# =====================================================
# SAVE
# =====================================================


df_results = pd.DataFrame(
    results
)



TOKEN_COLUMNS = [

    "qualification_input_tokens",

    "qualification_output_tokens",

    "qualification_total_tokens",

    "intelligence_input_tokens",

    "intelligence_output_tokens",

    "intelligence_total_tokens",

    "llm_total_tokens"

]



for col in TOKEN_COLUMNS:


    if col not in df_results.columns:

        df_results[col] = 0



df_results.to_excel(

    OUTPUT_FILE,

    index=False

)



# =====================================================
# TOKEN SUMMARY
# =====================================================


print()

print(
    "=========================="
)

print(
    "TOKEN USAGE SUMMARY"
)

print(
    "=========================="
)



for col in TOKEN_COLUMNS:


    total = (

        df_results[col]
        .fillna(0)
        .sum()

    )


    print(

        col,

        ":",

        int(total)

    )



print()

print(
    "Accounts tested:",
    len(df_results)
)



print(
    "Completed"
)


print(
    "Saved:"
)


print(
    OUTPUT_FILE
)


print(
    "=========================="
)
