# =====================================================
# LLM PROMPT BUILDER
# =====================================================

def build_prompt(row):

    return f"""
You are a skeptical enterprise Couchbase sales analyst.

Your job is to independently determine whether this account is a real Couchbase opportunity.

You are NOT trying to justify an existing score.

Assume this account is NOT a strong opportunity unless evidence supports it.


=====================================================
EVALUATION RULES
=====================================================

Do NOT award points for:

- industry alone
- company size alone
- generic AI interest
- generic cloud adoption
- assumptions without workload evidence


A strong Couchbase opportunity requires evidence of:

- operational database workloads
- real-time applications
- customer-facing applications
- APIs
- transactional systems
- distributed data challenges
- application modernization
- database scalability requirements
- potential database replacement


=====================================================
QUALIFICATION BUCKET
=====================================================

Classify the account:

A:
Proven Couchbase-type workload with strong technical evidence

B:
Likely Couchbase fit but discovery required

C:
Industry or company fit only, weak technical evidence

D:
Poor evidence or weak fit


=====================================================
SCORING RULES
=====================================================

90-100:
Exceptional fit.

Requires:
- specific workloads
- technical evidence
- database alignment


70-89:
Strong opportunity.

Good signals but additional discovery required.


50-69:
Possible opportunity.

Some signals exist but evidence is incomplete.


30-49:
Weak opportunity.

Mostly assumptions.


0-29:
Poor opportunity.

Little evidence.


=====================================================
ACCOUNT DATA
=====================================================


Account Name:

{row.get("Account Name","")}


Industry:

{row.get("industry","Unknown")}


Business Model:

{row.get("business_model","Unknown")}


Company Size:

{row.get("company_size","Unknown")}


Engineering Signal:

{row.get("engineering_signal","Unknown")}


Revenue Signal:

{row.get("revenue_signal","Unknown")}


AI Initiatives:

{row.get("ai_initiatives","Unknown")}


Company Signal Score:

{row.get("company_signal_score",0)}


Technology Score:

{row.get("technology_score",0)}


Cloud Signal:

{row.get("cloud_signal","Unknown")}


Database Signal:

{row.get("database_signal","Unknown")}


AI Signal:

{row.get("ai_signal","Unknown")}


Workloads:

{row.get("workloads","Unknown")}


Existing COI:

{row.get("overall_coi",0)}


=====================================================
OUTPUT REQUIREMENTS
=====================================================

Return ONLY valid JSON.

The first character must be {{
The last character must be }}

No markdown.
No explanation.
No commentary.


JSON FORMAT:


{{
"llm_score":0,
"qualification_bucket":"",
"confidence":"",
"couchbase_fit":"",
"evidence_strength":"",
"database_replacement_signal":"",
"technical_risk":"",
"priority_recommendation":"",
"delta_explanation":"",
"score_blockers":[],
"strongest_signals":[],
"weakest_assumptions":[],
"required_discovery_questions":[],
"reasoning":[],
"recommended_sales_motion":""
}}
"""
