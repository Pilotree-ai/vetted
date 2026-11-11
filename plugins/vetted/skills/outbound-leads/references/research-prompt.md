# Research and openers (step 5)

For each enriched person, decide one last time whether to send, then write the first email's subject and opener. The rest of the email comes from the brief's step-1 template. Everything written here may be sent word for word, so it must be true, checkable and in the house voice. In past batches this step dropped about 15% of the list. That is normal.

## Inputs per person

- the brief: offer, product description (from config), step-1 template, the offer's **drop rules** and **opener pattern** (if the brief or its example has one)
- the person: Apollo id, first and last name, title, company, email
- the screen result: outcome, evidence and `opener_facts`
- the company site (read again only if `opener_facts` is thin, max about 3 pages in total, usually homepage, services, blog)

## Drop rules

Always drop if:

- not really the kind of company the brief targets
- the site is dead or dormant
- part of a big group, when the brief wants independents
- the person has left the company
- the email domain does not match the company and you cannot confirm the link

Then add the offer's own drop rules from the brief, for example "they already sell a competing product" or "offline-only businesses".

## The prompt (one per chunk of about 10 for subagents)

```
You are researching prospects for {company_name}'s outbound for {product_name}
({product_description}).

Offer: {offer}
Sender: {sender_name}

For EACH person below, read the company's own website, max ~3 pages each.
1. Decide "send" or "drop". Drop if: {drop_rules}
2. opener: 1-2 sentences, based on a REAL fact from their own site, linking it
   to {offer_link}.{opener_pattern_line}
3. subject: natural, specific to them, under 60 characters.
4. evidence: the URL the opener is based on.
5. why_fit: one sentence for the approver on why this company fits the brief.

Rules: British English. No invented facts or numbers. No flattery. No exclamation
marks. No em dashes. Never claim a result about them that
nobody has checked. Write the person's real first name, never a merge tag. Don't
contact anyone.

Screen evidence and facts already found, per company:
{screen_results}

People:
{people}

Return a JSON array only, one object per person, with: id, first, last, org,
short_name, email, decision, drop_reason, subject, opener, evidence, why_fit{extra_fields}.
```

- `{offer_link}` is what the opener should connect to, e.g. "the time their team spends on monthly client reporting".
- `{opener_pattern_line}`: if the brief has an opener pattern, add `\n   Follow this pattern: <pattern>`. Otherwise leave it out.
- `{extra_fields}`: any extra field the offer needs, e.g. `, buyer_question` when the opener pattern needs a likely customer question per company.
- `short_name` is how the company would naturally be named in a sentence ("Hart & Shah", not "Hart & Shah Digital Marketing Ltd"). Templates use it.

## Build the finished email

For each `send`, fill the step-1 template: first name, opener, short name, sender name, any template-specific rules (for example, the agency template changes its second paragraph's start depending on whether the opener mentions the product), and the opt-out line from config. Store it as:

```json
"full_step1": { "subject": "...", "body": "Hi Priya,\n\n<opener>\n\n<rest of template>\n\nSam\n\nIf this isn't relevant, reply \"no\" and I won't email again." }
```

This is exactly what the approver sees and what goes into the Apollo override.

**If the brief has a test**, split the people as "Splitting" in `references/ab-tests.md` describes: alternate A and B in posting order, use that version's closing ask in `full_step1`, and store `"variant": "A"` or `"B"` on the person. Nothing else in the email changes between versions.

## Self-check before saving

Go through each email and fix or drop it if any of these fail. It is much cheaper to catch them now than in Slack.

- Subject 60 characters or fewer.
- No `!`, no `—`, no `{` or `{{` left in subject or body.
- The opener's fact appears at the evidence URL.
- No claim about a result nobody has checked (their rankings, traffic, what a tool or AI assistant says about them).
- No prices in step 1 unless the brief allows it.
- Ends with the opt-out line from config.
- With a test: each email's closing ask is exactly its version's text, and A and B alternate.
- British spelling (organise, optimise, colour, programme where relevant).

If a site was bot-blocked and the opener is weak, keep it but add the flag `site blocked, weaker opener` so the approver can decide.

Save to `outbound/campaigns/<slug>/04-research.json`. Report how many are ready to send, how many dropped at this step, and the drop reasons.
