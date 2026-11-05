# Website screen (step 3)

Apollo did the broad pull. Now read each company's own website and decide, against the rules in the brief, whether it fits. This is where judgement happens, so it has to be careful and evidenced. The approver in Slack will see the evidence and trust it.

## Three outcomes

- **qualify**: the site clearly meets every rule.
- **drop**: the site clearly fails at least one rule.
- **unclear**: the site does not say enough to decide. Never guess. A guess presented as a fact is worse than an honest "unclear", because the approver cannot tell the difference.

Unclear leads are held for review by default (`unclear_leads` in config). They are enriched with the qualifiers and shown in Slack in their own section, with whatever evidence was found, so the approver keeps or drops each one.

## How to screen one company

1. Open the homepage. Then open at most 2 more pages that are most likely to answer the rules: usually About, Team, People, Our story, Contact. Stay within `max_pages_per_site` (default 3).
2. Apply each rule from the brief separately. For each rule, record the outcome and the evidence.
3. Evidence is always the URL and a short quote or close paraphrase of the line that supports the decision. "Team page lists Sam Hart and Priya Shah as Founding Partners" is evidence. "Looks like a partnership" is not.
4. The company outcome is: drop if any rule is drop, otherwise unclear if any rule is unclear, otherwise qualify.
5. Note one or two real facts from the site that could support an opener later (a recent project, a specialism, a client sector, a stated belief). This saves re-reading in step 5.

If the site is blocked to bots, redirects somewhere unrelated, is a holding page, or is nearly empty: mark the relevant rules unclear with a note such as "site blocked" or "single-page site, no team info". Do not fill the gap from memory or from other sources unless the brief allows it.

## Common pitfalls

- **Small firms often do not state their structure.** That is unclear, not drop.
- **Title inflation.** Some agencies call everyone a partner, or call a single owner "founding partner". Read the rule's intent from the brief: a co-founder pair running the firm, not a title on a business card.
- **Group-owned firms** often look independent on their own site. Check the footer and About page for "part of" or "a <group> company".
- **Headcount.** Count people on the team page if there is one. Apollo's number is often out of date. No team page means headcount is unclear, not a fail.
- **A strict screen drops many.** That is expected. If qualifiers are running well below target after half the list, tell the user and offer to pull more from Apollo rather than loosening the rules silently.

## Output per company

Return one JSON object per company. Subagents return a JSON array of these.

```json
{
  "company": "Hart & Shah",
  "domain": "hartshah.co.uk",
  "outcome": "qualify",
  "rules": [
    {
      "rule": "Partner-led",
      "outcome": "qualify",
      "evidence_url": "https://hartshah.co.uk/about",
      "evidence": "About page: 'Sam and Priya started Hart & Shah in 2019 and still run every account together.'"
    },
    {
      "rule": "Headcount 1 to 20",
      "outcome": "qualify",
      "evidence_url": "https://hartshah.co.uk/team",
      "evidence": "Team page shows 9 people."
    }
  ],
  "opener_facts": [
    "Specialises in SEO for UK veterinary practices (homepage)",
    "Published a guide to local search for multi-site clinics, Oct 2026 (/insights)"
  ],
  "notes": ""
}
```

## Subagent brief (Claude Code)

When delegating a chunk of about 10 companies, give each agent:

- the qualification rules section of the brief, verbatim
- this file's "How to screen one company" and "Output per company" sections
- its list of companies with domains
- the instruction: "Use WebFetch to read each site. Return only the JSON array. Do not guess. If a page does not load, mark the affected rules unclear and say why."

## After the screen

Merge into `outbound/campaigns/<slug>/02-screen.json`. Report:

"Screened <n> companies: <q> qualify, <u> unclear, <d> drop. Top drop reasons: <...>. Enriching <q+u> people next will cost up to <q+u> credits."

Then go to Gate 2 in `apollo-search.md`.
