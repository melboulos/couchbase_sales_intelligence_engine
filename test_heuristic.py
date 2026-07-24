# =====================================================
# TEST AGAINST REAL CLOSED-WON DEALS
# Filtered to exclude Capella self-serve signups and
# CBC OD billing/usage adjustment line items — this is
# the list of accounts that actually went through a real,
# sales-assisted deal process.
# =====================================================

from modules.company_intelligence import analyze_company

ACCOUNTS = """ADT LLC
AGCO Corporation
Age of Learning, Inc.
All Web Leads, Inc.
American Airlines, Inc.
American Express AZ
American Honda Motor Co., Inc.
Aptos, LLC
Arrivia, Inc.
At Your Service Systems, Inc.
Australia and New Zealand Banking Group Limited
AutoZone Parts, Inc.
BNSF Railway Company
BTG Pactual
Baker Hughes Company
Banco BS2
Banco Daycoval S.A.
Best Buy Canada Ltd
Bradesco
Bread Financial
Breakdown Services, Ltd.
Brightly Software, Inc.
BroadJump, LLC.
Broadridge Financial Solutions
CJ Mart Co., Ltd.
CQR Technologies, Inc.
Central Bancompany, Inc.
ClearCaptions LLC
Cochlear Limited
Comcast Cable Communications Management, LLC
Computer Know How, LLC
Crowdstar
Cvent, Inc.
D.H. Pace Company
DIRECTV, LLC
DISH Network L.L.C
DaVita Inc.
Defence Science & Technology Agency DSTA
Disney Parks Technology Services Co., LLC
DreamWorks Animation LLC.
Emeco Holdings Limited
Energy Transfer LP (ET)
Enmax Corporation
Evertec
FBM Gaming
Fastenal Company
Federal Home Loan Bank of Topeka
Five 9 Inc.
Flipspaces Technology Labs Private Limited
Florida Department of Highway Safety and Motor Vehicles
Fun Pass LLC
Global Mobility Apex S.A.
Grubtech Software Design LLC
It's Never 2 Late, LLC, DBA LifeLoop
Ivolution
JM Information Limited
JPOP Pro
Jedi Management
John Wiley & Sons, Inc
Kawan Lama Group
Klook Travel Technology Limited
LevelChanger Inc.
LivePerson, Inc.
Marriott International Administrative Services, Inc.
Matrix Medical Network
Mavenir Systems, Inc.
MoneyGram Payments Systems Inc
Motorola Solutions, Inc.
Multi Media LLC
NBCUniversal
NCS Pearson, Inc.
NOV Inc.
NSA
National Oceanic and Atmospheric Administration
NetDocuments Software, Inc.
Nielsen Consumer LLC
North Key Systems
Northrop Grumman Systems Corporation
Nymble Commerce LLC
ON24, Inc.
P.J. Lhuillier, Inc.
PT Prudential Life Assurance
PT Telekomunikasi Selular
PT. Logistar Cakra Solusi
Parallon Business Solutions, LLC
PepsiCo, Inc.
Personal Collection Direct Selling Inc
PetIQ, LLC
Pfizer Inc.
Pixability, Inc.
Playgon Games Inc.
ProSites Inc.
Process & Safety Solutions LLC
Proctor U Inc.
Prudential Services Singapore Pte Ltd
Pulsora Inc.
QVC, Inc.
Resideo USA LLC
Royal Caribbean Cruises, Ltd.
Sabre GLBL, Inc
Samsung Telecommunications America, LLC
Sandals Resorts
Snapser Inc.
Solea Energy LLC
Sonover Inc
Staples, Inc.
Starhub Ltd
State Street Bank
SwarmFarm Robotics Australia
TOTVS
TTX Company
Talentsky, Inc.
Tara Group of Companies LLC
Telstra Limited
Telus Communications Inc.
Tengku Permaisuri Norashikin Hospital (Hospital Kajang)
The Chamberlain Group, LLC
Tixr Inc.
Tractor Supply Company
TransUnion
Triumvirate Environmental, LLC
Unisys Corporation
United Airlines
United Parcel Service Oasis Supply Corporation
Uptodate, Inc.
Valet Manager Inc
Verizon Communications Inc.
Virgin Voyages
Wawa, Inc.
Western Union Financial Services, Inc.
Wind Creek Hospitality
Wintrust Financial Corporation
Yahoo Inc.
Yum Restaurant Services Group, LLC
Zerofox, Inc.
bizZone Inc.
doTERRA International, LLC
i3 Verticals, LLC
rapidBizApps.com, LLC dba GroundHog Apps.""".strip().split("\n")

matched = []
unmatched = []

for name in ACCOUNTS:
    name = name.strip()
    row = {"Account Name": name, "normalized_account_name": name.lower()}
    result = analyze_company(row)
    reason = result.get("company_signal_reason", "")

    if reason:
        matched.append((name, reason, result.get("workload_profile", "")))
    else:
        unmatched.append(name)

print(f"Total real closed-won accounts tested: {len(ACCOUNTS)}")
print(f"Matched: {len(matched)}")
print(f"Unmatched: {len(unmatched)}")
print()

print("=== MATCHED ===")
for name, reason, profile in matched:
    print(f"  {name!r:50} -> {reason} ({profile})")

print()
print("=== UNMATCHED (these are REAL closed-won deals our system would have missed) ===")
for name in unmatched:
    print(f"  {name}")
