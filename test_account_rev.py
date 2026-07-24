import pandas as pd
import openpyxl
import glob

closed_won_files = glob.glob("Closed*Won*.xlsx")
closed_won_path = closed_won_files[0]

wb = openpyxl.load_workbook(closed_won_path)
ws = wb["Closed Won"]

rows = []
for row in ws.iter_rows(min_row=14, values_only=True):
    owner = row[3]
    account = row[4]
    sales_stage = row[7]
    if owner and account and sales_stage and "Closed Won" in str(sales_stage):
        rows.append({
            "Account Name": row[4],
            "Amount": row[5],
            "Opportunity Name": row[6],
        })

df = pd.DataFrame(rows)

real_deals = df[
    ~df["Opportunity Name"].str.contains("CBC OD", na=False)
    & ~df["Opportunity Name"].str.contains("Capella Signup", na=False)
    & ~df["Opportunity Name"].str.contains("Capella Credit Card Signup", na=False)
]

# Total revenue per account (some accounts have multiple deals)
by_account = real_deals.groupby("Account Name")["Amount"].sum().sort_values(ascending=False)

total_revenue = by_account.sum()
n_accounts = len(by_account)

print(f"Total accounts: {n_accounts}")
print(f"Total revenue: ${total_revenue:,.2f}")
print()

for top_n in [5, 10, 20, 30]:
    top_revenue = by_account.head(top_n).sum()
    pct = (top_revenue / total_revenue) * 100
    print(f"Top {top_n} accounts by revenue: ${top_revenue:,.2f} ({pct:.1f}% of total)")

print()
print("=== Top 20 accounts by revenue ===")
for name, amount in by_account.head(20).items():
    print(f"  {name:50} ${amount:>15,.2f}")

print()
print("=== Bottom 20 accounts by revenue ===")
for name, amount in by_account.tail(20).items():
    print(f"  {name:50} ${amount:>15,.2f}")
