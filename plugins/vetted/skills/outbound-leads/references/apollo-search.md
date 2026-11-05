# Apollo search and enrichment

Two parts: a free broad search (step 2) and a paid enrichment of qualifiers only (step 4). Screening the website in between means credits are only spent on people worth emailing.

## Part 1: Search (step 2, free)

### Turn the brief into filters

Apollo can match titles, seniority, keyword tags, location and employee-count buckets. It cannot judge anything subtle, so cast a wide net here and let the website screen do the judging.

| Brief field | Apollo filter (`apollo_mixed_people_api_search`) |
|---|---|
| audience | `q_organization_keyword_tags`, e.g. `["marketing agency", "digital agency", "seo"]`. Use 3 to 6 tags to widen the pull |
| company_size | `organization_num_employees_ranges`. Buckets are fixed: `"1,10"`, `"11,20"`, `"21,50"`, `"51,100"`, `"101,200"`, `"201,500"`, ... Pick the buckets that cover the range, plus one above if headcounts are often stale |
| location | `person_locations` **and** `organization_locations`, e.g. `["United Kingdom"]`. Setting only one returns people abroad and wastes credits later |
| contact_titles | `person_titles`. Set `include_similar_titles: false` when the brief says "strict" or lists exact titles. Otherwise leave it true and add `person_seniorities` such as `["owner", "founder", "c_suite", "partner"]` if useful |
| verified emails only | `contact_email_status: ["verified"]`. Use this by default so credits are not spent on people with no deliverable email |
| industries to exclude | `not_organization_naics_codes`, e.g. `["5418", "5416"]` to keep agencies and consultancies out of a brand search |

Show the filters in the Gate 1 read-back so the user confirms them along with the brief. If the brief is too vague to map onto filters with confidence, or results are thin, use `apollo_agent_find_prospects` with the brief's plain-language audience instead. It knows Apollo's filter values better.

### Pull and dedupe

- Use `per_page` 100 and page until you have about `batch_size x screen_multiplier` people (from config, default 4), or results run out.
- Keep one or two people per company: the best title match first. The screen is per company, so do not screen the same company twice.
- From each result keep: Apollo person id, name, title, company name, company domain or website, LinkedIn URL, location.
- If a result has no company domain, look it up with `apollo_mixed_companies_search` by company name, or a quick web search. Mark it if you cannot find one. It cannot be screened without a website.

### Exclusions

Remove before screening, and record why:

1. **Ledger.** Any domain or email in `outbound/contacted.csv`, from any sender. The same company should never get two cold emails from the same domain.
2. **Already in Apollo sequences.** Check with `apollo_contacts_search` by company domain or name where practical. Enrolment also refuses people active in other sequences, but it is cheaper to catch them now.
3. **Tracker canvas.** If config has a tracker canvas, read it and exclude companies listed there.
4. **Holds.** Any company or person under `holds` in config.
5. **Brief exclusions.** Anything extra the brief names.

### If people search is blocked

On a free Apollo plan, Claude cannot search people. The workaround: the user searches in the Apollo web app and saves the people to a list (label). Read that list with `apollo_contacts_search` and continue from the exclusions.

Save to `outbound/campaigns/<slug>/01-search.csv` with columns:
`apollo_person_id,first_name,last_name,title,company,domain,linkedin_url,location,excluded,exclude_reason`

Tell the user: "Pulled <n> people at <m> companies. Excluded <k> (<reasons>). Screening <m-k> company websites next."

## Part 2: Enrich (step 4, costs credits)

Only people at companies marked **qualify** or **unclear** in the screen are enriched. Dropped companies cost nothing.

### Gate 2: confirm the cost

Use the balance from preflight (or call `apollo_users_api_profile` with `include_credit_usage=true` if it is stale). Then say exactly:

> Found <N> contacts. Enriching all will use up to <N> credits. You have <X> credits remaining. Do you want to proceed?

Format the balance with thousands separators. Wait for a yes. If the response carries an `mcp_credits` block, show it.

### Enrich

- Work email only. No phone reveal, no personal emails. Do not run waterfall enrichment unless the user asks for it, because its cost varies and can be much higher.
- Use `apollo_people_bulk_match` with the Apollo person `id` only, 10 per call, without re-confirming between batches. For large jobs `apollo_agent_bulk_enrich` does the same in one request.
- Report progress and credits used as you go.

### Check each email

| Result | Action |
|---|---|
| Verified email on the company's domain | Keep |
| Email domain does not match the company's website | **Drop.** It is usually a different company, a group parent or an old employer |
| Catch-all domain | Keep, flag `catch-all (warn)`. Usually delivers, but bounces show here first |
| No email found, or unverified | Drop. No credit is charged for no match |

Save to `outbound/campaigns/<slug>/03-enriched.csv` (the search columns plus `email,email_status,flag`). Report: "Enriched <n>, <k> emails found, <d> dropped for domain mismatch, <c> catch-all, <u> credits used, <X> left."
