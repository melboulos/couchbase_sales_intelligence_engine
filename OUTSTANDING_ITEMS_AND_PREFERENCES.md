# Couchbase Sales Intelligence Engine — Outstanding Items & Working Preferences

## Outstanding: Top 20 Accounts sheet

- Move the Tier Distribution pie chart back to sitting BELOW the table, not beside it.
- Revert "Why Couchbase" back to the full first sentence — the 15-word truncation was tried and rejected.
- Widen the "Recommended First Contact" column — currently too narrow.
- Header row needs to accommodate "Recommended First Contact" properly — currently cramped/cut off, needs more height or to wrap.
- Both charts (pie + bar) are too small — labels and text run into each other. Needs bigger dimensions and more spacing between the two charts so they don't collide.
- "Top Opportunity Drivers" percentages are getting cut off — column too narrow for the text.

## Outstanding: Full Landscape sheet

- **Avg COI (Actionable) "looks too low."** Verified twice with real data: the math is correct — it excludes Tier 4 and averages only Tier 1-3. Confirmed root cause: in most industries, Tier 3 vastly outnumbers Tier 1+2 combined (e.g., Technology/SaaS: 1,400 Tier 3 vs. 5 combined Tier 1+2), so the "actionable" average is mostly a Tier 3 average by volume, which reads as unimpressively middling even though it's mathematically honest. **Proposed fix, not yet built or agreed upon: add a second column, "Avg COI (Tier 1-2 only)," so a rep can see both "how strong are our very best accounts" and "how big is the broader pipeline" separately, instead of one blended number trying to answer both.** This was mid-discussion when the session ended — needs to actually be discussed and agreed on, not just built.
- Conditional formatting colors (white→yellow→red) need to be lighter/softer.
- The title bar/border at the top doesn't extend over the Tier 1/Tier 2 KPI boxes — needs to be widened so the whole KPI row sits under one cohesive header, and the table below should align to the same width so nothing looks disjointed.

## Outstanding: Overview sheet

- Widen the Account Name column.
- Add a visible box/border around Account Name for better visibility.
- Add some kind of confidence/verification tag (e.g., whether the LLM score is web-grounded vs. a default) — currently Overview shows no confidence indicator at all, unlike Call Briefs which already has "Web-Verified" / "NOT COMPANY-VERIFIED" badges. Exact placement/format not yet agreed.

## Already confirmed correct (don't re-relitigate without new evidence)

- Actionable % column values are mathematically verified correct against real per-industry tier counts.
- The "Web-Verified" badge on Call Briefs is present and correct for 3,577 of 3,579 accounts (99.9%) — confirmed via a full, corrected scan of the real file, not a partial or buggy one.
- Insurance's Tier 3 count (46 accounts) is a real, correct result of two legitimate mechanisms compounding (classification pre-pass recognizing previously-Unknown large companies + the pre-existing scale-tier +1 nudge for "above_typical" companies) — not a bug.

## Working style — what actually needs to change

- **Discuss before building, every time it's asked for — not just once, then drift back into building.** Today included multiple points where "let's discuss first" was said explicitly and the response was still a proposal or a code change.
- **Don't repeat the same explanation of something already verified.** If a number has been checked twice and confirmed correct, asking a third time deserves a request for a specific new data point, not a third retelling of the same math.
- **Don't guess at ambiguous short replies ("no," "why," "stop") — but also don't go silent as an overcorrection.** Ask one direct, specific clarifying question, or acknowledge the ambiguity plainly, without either assuming intent or refusing to engage at all.
- **A fix living in code is not the same as a fix reaching real, current data.** This was a genuine, costly failure earlier in this session (a rating fix sat correct in a file for days without `main.py` ever being re-run) and is worth remembering as a standing risk on this specific codebase.
- **Verify claims against real output before stating them as fact**, especially anything involving "is this data still there" or "did this actually get applied."
