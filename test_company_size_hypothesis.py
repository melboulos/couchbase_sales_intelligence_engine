import pandas as pd
import openpyxl
import glob

# =====================================================
# LOAD RAW CLOSED-WON EXPORT
# =====================================================

closed_won_files = glob.glob("Closed*Won*.xlsx")
if not closed_won_files:
    raise FileNotFoundError("Could not find the Closed Won export in the project root")

closed_won_path = closed_won_files[0]
print(f"Reading: {closed_won_path}")

wb = openpyxl.load_workbook(closed_won_path)
ws = wb["Closed Won"]

rows = []
for row in ws.iter_rows(min_row=14, values_only=True):
    owner = row[3]
    account = row[4]
    sales_stage = row[7]
    if owner and account and sales_stage and "Closed Won" in str(sales_stage):
        rows.append({
            "Opportunity Owner": row[3],
            "Account Name": row[4],
            "Amount": row[5],
            "Opportunity Name": row[6],
            "Sales Stage": row[7],
        })

closed_won_df = pd.DataFrame(rows)
print(f"Total real opportunity rows: {len(closed_won_df)}")

# =====================================================
# FILTER OUT SELF-SERVE SIGNUPS AND BILLING ADJUSTMENTS
# =====================================================

real_deals = closed_won_df[
    ~closed_won_df["Opportunity Name"].str.contains("CBC OD", na=False)
    & ~closed_won_df["Opportunity Name"].str.contains("Capella Signup", na=False)
    & ~closed_won_df["Opportunity Name"].str.contains("Capella Credit Card Signup", na=False)
]

unique_won_accounts = set(
    real_deals["Account Name"].str.strip().str.lower()
)
print(f"Unique real sales-assisted closed-won accounts: {len(unique_won_accounts)}")
print()

# =====================================================
# JOIN AGAINST THE SCORED UNIVERSE
# =====================================================

scored = pd.read_excel("output/Enterprise_East_Scored.xlsx")
scored["name_lower"] = scored["Account Name"].str.strip().str.lower()

matches = scored[scored["name_lower"].isin(unique_won_accounts)]

print(f"Of {len(unique_won_accounts)} unique closed-won accounts, "
      f"{len(matches)} already exist in the scored universe")
print()

print("=== company_size breakdown among matched closed-won accounts ===")
print(matches["company_size"].value_counts(dropna=False))
print()

print("=== priority_tier breakdown among matched closed-won accounts ===")
print(matches["priority_tier"].value_counts(dropna=False))
print()

print("=== overall_coi stats among matched closed-won accounts ===")
print(matches["overall_coi"].describe())
print()

# Which won accounts are NOT even in the scored universe at all?
scored_names = set(scored["name_lower"])
never_scored = unique_won_accounts - scored_names
print(f"Closed-won accounts NOT present in the scored universe at all: {len(never_scored)}")
for name in sorted(never_scored):
    print(" ", name)
