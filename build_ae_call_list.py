# =====================================================
# BUILD AE CALL LIST
# Couchbase Sales Intelligence Engine
#
# DEBUG VERSION — checkpoint prints added after every
# major step to pinpoint exactly where execution stops.
# =====================================================

import sys
import pandas as pd
import ast
from openpyxl import load_workbook
from openpyxl.styles import Font, Alignment, PatternFill, Border, Side
from openpyxl.utils import get_column_letter
from openpyxl.formatting.rule import ColorScaleRule
from openpyxl.chart import BarChart, Reference


def checkpoint(msg):
    print(f">>> CHECKPOINT: {msg}", flush=True)


INPUT_FILE = "output/Enterprise_East_Scored.xlsx"
OUTPUT_FILE = "output/AE_Call_List.xlsx"


def parse_field(value):
    if isinstance(value, (list, dict)):
        return value
    if not isinstance(value, str) or not value.strip():
        return []
    try:
        return ast.literal_eval(value)
    except (ValueError, SyntaxError):
        return value


def flatten_bullet_list(value):
    parsed = parse_field(value)
    if isinstance(parsed, list):
        if not parsed:
            return "(none noted)"
        return "\n".join(f"\u2022 {item}" for item in parsed)
    if isinstance(parsed, str) and parsed.strip():
        return parsed
    return "(none noted)"


def flatten_discovery_progression(value):
    parsed = parse_field(value)
    if not isinstance(parsed, list) or not parsed:
        return "(none noted)"
    lines = []
    for phase in parsed:
        if not isinstance(phase, dict):
            continue
        phase_label = phase.get("phase", "")
        objective = phase.get("objective", "")
        questions = phase.get("questions", [])
        lines.append(f"{phase_label} \u2014 {objective}")
        for q in questions:
            lines.append(f"    \u2022 {q}")
        lines.append("")
    return "\n".join(lines).strip()


checkpoint("Script started")

print("Loading scored accounts...", flush=True)
accounts = pd.read_excel(INPUT_FILE)
print(f"Loaded {len(accounts)} accounts", flush=True)

checkpoint("Loaded input file")

has_intelligence = accounts["engineering_implications"].notna() & (
    accounts["engineering_implications"].astype(str).str.strip() != ""
)
call_list = accounts[has_intelligence].copy()
call_list = call_list.sort_values("overall_coi", ascending=False).reset_index(drop=True)
print(f"Accounts with validated LLM intelligence: {len(call_list)}", flush=True)

checkpoint("Filtered call_list")

HEADER_FONT = Font(name="Arial", bold=True, color="FFFFFF", size=13)
HEADER_FILL = PatternFill(start_color="2F5496", end_color="2F5496", fill_type="solid")
TITLE_FONT = Font(name="Arial", bold=True, size=16, color="FFFFFF")
TITLE_FILL = PatternFill(start_color="1F3864", end_color="1F3864", fill_type="solid")
KPI_LABEL_FONT = Font(name="Arial", size=12, color="595959")
KPI_VALUE_FONT = Font(name="Arial", bold=True, size=26, color="1F3864")
LABEL_FONT = Font(name="Arial", bold=True, size=12, color="2F5496")
BODY_FONT = Font(name="Arial", size=12)
LINK_FONT = Font(name="Arial", size=13, color="0563C1", underline="single")
WRAP = Alignment(wrap_text=True, vertical="top")
CENTER = Alignment(horizontal="center", vertical="center")
THIN_BORDER = Border(bottom=Side(style="thin", color="D9D9D9"))

checkpoint("Styles defined")

industry_summary = (
    accounts
    .groupby("industry")
    .agg(
        total_accounts=("Account Name", "count"),
        avg_coi=("overall_coi", "mean"),
        tier_1=("priority_tier", lambda s: (s == "Tier 1 Strategic").sum()),
        tier_2=("priority_tier", lambda s: (s == "Tier 2 Strong Target").sum()),
        tier_3=("priority_tier", lambda s: (s == "Tier 3 Nurture").sum()),
        tier_4=("priority_tier", lambda s: (s == "Tier 4 Monitor").sum())
    )
    .reset_index()
)

checkpoint("industry_summary computed")

industry_summary["avg_coi"] = industry_summary["avg_coi"].round(1)
industry_summary = industry_summary.sort_values("tier_1", ascending=False).reset_index(drop=True)
industry_summary = industry_summary.head(15)
industry_summary = industry_summary.rename(columns={
    "industry": "Industry",
    "total_accounts": "Total Accounts",
    "avg_coi": "Avg COI",
    "tier_1": "Tier 1",
    "tier_2": "Tier 2",
    "tier_3": "Tier 3",
    "tier_4": "Tier 4"
})

checkpoint("industry_summary formatted, about to write initial xlsx")

industry_summary.to_excel(OUTPUT_FILE, index=False, sheet_name="Summary", startrow=6)

checkpoint("Initial pandas to_excel write complete")

wb = load_workbook(OUTPUT_FILE)
checkpoint("Reloaded workbook with openpyxl")

ws_summary = wb["Summary"]
checkpoint("Got Summary worksheet handle")

ws_summary.merge_cells("A1:G1")
title_cell = ws_summary["A1"]
title_cell.value = "Couchbase Sales Intelligence \u2014 Account Landscape Summary"
title_cell.font = TITLE_FONT
title_cell.fill = TITLE_FILL
title_cell.alignment = Alignment(vertical="center", indent=1)
ws_summary.row_dimensions[1].height = 32

checkpoint("Title bar written")

total_scored = len(accounts)
total_qualified = len(call_list)
total_tier1 = int((accounts["priority_tier"] == "Tier 1 Strategic").sum())
total_tier2 = int((accounts["priority_tier"] == "Tier 2 Strong Target").sum())

kpis = [
    ("Total Accounts Scored", total_scored),
    ("Qualified for AE Call List", total_qualified),
    ("Tier 1 Strategic", total_tier1),
    ("Tier 2 Strong Target", total_tier2)
]

kpi_col = 1
for label, value in kpis:
    label_cell = ws_summary.cell(row=3, column=kpi_col)
    value_cell = ws_summary.cell(row=4, column=kpi_col)
    label_cell.value = label
    label_cell.font = KPI_LABEL_FONT
    label_cell.alignment = CENTER
    value_cell.value = value
    value_cell.font = KPI_VALUE_FONT
    value_cell.alignment = CENTER
    ws_summary.merge_cells(start_row=3, start_column=kpi_col, end_row=3, end_column=kpi_col + 1)
    ws_summary.merge_cells(start_row=4, start_column=kpi_col, end_row=4, end_column=kpi_col + 1)
    ws_summary.row_dimensions[4].height = 34
    kpi_col += 2

checkpoint("KPI row written")

header_row = 7
n_cols = len(industry_summary.columns)
for col_idx in range(1, n_cols + 1):
    cell = ws_summary.cell(row=header_row, column=col_idx)
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = CENTER
ws_summary.row_dimensions[header_row].height = 22

summary_widths = {"A": 28, "B": 16, "C": 13, "D": 11, "E": 11, "F": 11, "G": 11}
for col, width in summary_widths.items():
    ws_summary.column_dimensions[col].width = width

first_data_row = header_row + 1
last_data_row = header_row + len(industry_summary)

for row_idx in range(first_data_row, last_data_row + 1):
    ws_summary.row_dimensions[row_idx].height = 20
    for col_idx in range(1, n_cols + 1):
        cell = ws_summary.cell(row=row_idx, column=col_idx)
        cell.font = BODY_FONT
        if col_idx > 1:
            cell.alignment = CENTER

checkpoint("Summary table styled")

if last_data_row > first_data_row:
    avg_coi_range = f"C{first_data_row}:C{last_data_row}"
    ws_summary.conditional_formatting.add(
        avg_coi_range,
        ColorScaleRule(
            start_type="min", start_color="FFFFFF",
            mid_type="percentile", mid_value=50, mid_color="FFEB84",
            end_type="max", end_color="C00000"
        )
    )
    for col_letter in ["D", "E", "F", "G"]:
        cell_range = f"{col_letter}{first_data_row}:{col_letter}{last_data_row}"
        ws_summary.conditional_formatting.add(
            cell_range,
            ColorScaleRule(
                start_type="min", start_color="FFFFFF",
                mid_type="percentile", mid_value=50, mid_color="FFEB84",
                end_type="max", end_color="C00000"
            )
        )

checkpoint("Conditional formatting applied")

chart = BarChart()
chart.type = "bar"
chart.title = "Tier 1 Strategic Accounts by Industry"
chart.style = 10
chart.y_axis.title = "Industry"
chart.x_axis.title = "Tier 1 Account Count"
chart.height = 10
chart.width = 20

data = Reference(ws_summary, min_col=4, max_col=4, min_row=header_row, max_row=last_data_row)
categories = Reference(ws_summary, min_col=1, max_col=1, min_row=first_data_row, max_row=last_data_row)
chart.add_data(data, titles_from_data=True)
chart.set_categories(categories)
chart.legend = None

chart_anchor_row = last_data_row + 3
ws_summary.add_chart(chart, f"A{chart_anchor_row}")

checkpoint("Chart added")

ws_summary.freeze_panes = f"A{first_data_row}"

checkpoint("About to create Overview sheet")

ws_overview = wb.create_sheet("Overview")

overview_headers = ["Account Name", "COI Score", "Priority Tier", "Industry", "Business Model"]
for col_idx, header in enumerate(overview_headers, start=1):
    cell = ws_overview.cell(row=1, column=col_idx)
    cell.value = header
    cell.font = HEADER_FONT
    cell.fill = HEADER_FILL
    cell.alignment = Alignment(vertical="center")
ws_overview.row_dimensions[1].height = 24

overview_widths = {"A": 28, "B": 13, "C": 22, "D": 24, "E": 24}
for col, width in overview_widths.items():
    ws_overview.column_dimensions[col].width = width

account_brief_rows = []

for i, row in call_list.iterrows():
    excel_row = i + 2
    ws_overview.row_dimensions[excel_row].height = 20
    ws_overview.cell(row=excel_row, column=2, value=row.get("overall_coi", "")).font = BODY_FONT
    ws_overview.cell(row=excel_row, column=3, value=row.get("priority_tier", "")).font = BODY_FONT
    ws_overview.cell(row=excel_row, column=4, value=row.get("industry", "")).font = BODY_FONT
    ws_overview.cell(row=excel_row, column=5, value=row.get("business_model", "")).font = BODY_FONT
    for col_idx in range(2, 6):
        ws_overview.cell(row=excel_row, column=col_idx).alignment = CENTER

ws_overview.freeze_panes = "A2"

checkpoint(f"Overview sheet built with {len(call_list)} rows")

ws_briefs = wb.create_sheet("Call Briefs")
ws_briefs.column_dimensions["A"].width = 26
ws_briefs.column_dimensions["B"].width = 95

FIELD_ORDER = [
    ("Industry", lambda r: r.get("industry", "")),
    ("Business Model", lambda r: r.get("business_model", "")),
    ("Workload Profile", lambda r: r.get("workload_profile", "")),
    ("Engineering Implications", lambda r: flatten_bullet_list(r.get("engineering_implications", ""))),
    ("Couchbase Point of View", lambda r: r.get("couchbase_point_of_view", "") or "(none noted)"),
    ("Technical Risks to Validate", lambda r: flatten_bullet_list(r.get("technical_risks_to_validate", ""))),
    ("Discovery Questions", lambda r: flatten_discovery_progression(r.get("discovery_progression", ""))),
    ("Missing Information", lambda r: flatten_bullet_list(r.get("missing_information", "")))
]

current_row = 1
checkpoint("Starting Call Briefs loop (this is the biggest step — 320 accounts)")

for i, row in call_list.iterrows():
    if i % 50 == 0:
        checkpoint(f"Call Briefs progress: {i}/{len(call_list)}")

    title_row = current_row
    account_brief_rows.append((row.get("Account Name", ""), title_row))

    ws_briefs.merge_cells(start_row=title_row, start_column=1, end_row=title_row, end_column=2)
    title_cell = ws_briefs.cell(row=title_row, column=1)
    title_cell.value = (
        f"{row.get('Account Name', '')}   "
        f"\u2014  COI {row.get('overall_coi', '')}  "
        f"\u2014  {row.get('priority_tier', '')}"
    )
    title_cell.font = TITLE_FONT
    title_cell.fill = TITLE_FILL
    title_cell.alignment = Alignment(vertical="center", indent=1)
    ws_briefs.row_dimensions[title_row].height = 30

    current_row += 1

    for label, getter in FIELD_ORDER:
        label_cell = ws_briefs.cell(row=current_row, column=1)
        value_cell = ws_briefs.cell(row=current_row, column=2)

        label_cell.value = label
        label_cell.font = LABEL_FONT
        label_cell.alignment = Alignment(vertical="top", wrap_text=True)
        label_cell.border = THIN_BORDER

        value_cell.value = getter(row)
        value_cell.font = BODY_FONT
        value_cell.alignment = WRAP
        value_cell.border = THIN_BORDER

        text_len = len(str(value_cell.value))
        line_estimate = max(1, text_len // 70 + str(value_cell.value).count("\n") + 1)
        ws_briefs.row_dimensions[current_row].height = min(max(20, line_estimate * 18), 320)

        current_row += 1

    current_row += 1

checkpoint("Call Briefs loop complete")

ws_briefs.freeze_panes = "A2"

checkpoint("About to write hyperlinks")

for i in range(len(call_list)):
    row_num = i + 2
    account_name, brief_row = account_brief_rows[i]
    name_cell = ws_overview.cell(row=row_num, column=1)
    name_cell.value = account_name
    name_cell.hyperlink = f"#'Call Briefs'!A{brief_row}"
    name_cell.font = LINK_FONT

checkpoint("Hyperlinks written")

checkpoint("About to save workbook — this may take a moment")

wb.save(OUTPUT_FILE)

checkpoint("Workbook saved successfully")

print(f"Saved: {OUTPUT_FILE}", flush=True)
print(f"Summary: {len(industry_summary)} industries, {total_scored} accounts scored", flush=True)
print(f"Overview + Call Briefs: {len(call_list)} qualified accounts", flush=True)

checkpoint("Script finished")
