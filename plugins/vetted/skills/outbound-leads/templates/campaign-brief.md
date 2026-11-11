# Campaign brief: intake

Use this to turn the user's sentence into a brief, ask only about what is missing, and read it back. Save the confirmed brief to `outbound/campaigns/<slug>/brief.md` using the template at the bottom.

## 1. Parse the sentence

Pull out whatever the sentence gives you for each field. Do not invent values for fields the user did not mention. Mark them as gaps.

| Field | Notes |
|---|---|
| audience | industry or keywords, e.g. "marketing agencies", "SEO agencies" |
| company_size | headcount range, e.g. 1 to 20 |
| location | country or region |
| contact_titles | who to email, e.g. founder, managing partner, MD |
| qualification | plain-language criteria that need a website check, e.g. "partner-led" |
| offer | what is offered, e.g. a free site audit |
| product | which product from config, if relevant |
| offer_file | a saved offer in `outbound/offers/`, if the user names one ("use the agency offer") |
| drop_rules | offer-specific reasons to drop at research, e.g. "already sells their own tracking software" |
| opener_pattern | optional shape for the opener, e.g. the brand example's buyer-question pattern |
| email_copy | pasted template, a saved example name, or "draft it" |
| reply_handling | optional: what to do with yes, call, price and no replies |
| test | optional A/B test of one part of email 1, usually the closing ask (`references/ab-tests.md`) |
| sender | which sender key from config |
| batch_size | target number of approved leads |
| batch_label | e.g. "Agency pilot batch 3". Suggest one if missing |
| exclusions | anything beyond the defaults (ledger, active sequences) |

## 2. Turn each qualification phrase into a testable rule

Users write criteria the way they would say them to a colleague. Work out what they mean and write it as a rule you can check on a website, with clear qualify, drop and unclear cases. Then read the rule back so the user can correct it. Do not apply a fixed definition.

Example. The user writes "partner-led". They mean a small firm run by the people who started it together, such as two friends who co-founded an agency and now run it as partners. The title on the website might be partner, co-founder, founding partner or director. Turn it into:

- **Qualify:** the site names two or more people who co-founded or jointly run the firm (any of: partner, co-founder, founding partner, joint MD), or the firm calls itself a partnership or LLP.
- **Drop:** a single founder or owner with staff underneath, or the firm is part of a larger group or holding company.
- **Unclear:** the site does not name the leadership, or names only one person without saying whether others co-own it.

Other examples of phrases that need a rule: "independent" (not owned by a group), "growing" (hiring now, new office, recent launches), "does SEO in-house", "B2B only". Headcount limits like "under 20" also get a rule, because Apollo headcounts are often out of date: check the team page.

## 3. Ask only about gaps that matter

Ask in one go, with suggested defaults, using AskUserQuestion when available. The usual gaps:

- **Sender.** Which sender from config, if there is more than one. Never guess this.
- **Offer and copy.** If no template is given, list the user's saved offers in `outbound/offers/` and offer to use one, or draft new copy from the offer, using `templates/example-pilot-offer.md` or `templates/example-free-audit.md` as the shape. A saved offer brings its own filters, drop rules, opener pattern, four steps and reply handling, so the brief can just reference it and note any changes. Drafted copy gets approved in the Slack intro message. Once it has been approved, offer to save it to `outbound/offers/<name>.md` so it can be reused.
- **Qualification rule.** The rule you wrote in step 2. Ask "is this what you meant?"
- **Unclear leads.** Default from config is hold for review. Mention it, do not ask unless the brief suggests otherwise.

- **A/B test.** Follow "At intake" in `references/ab-tests.md`: continue a running test for this campaign, use a decided test's winner, or offer a new test of the closing ask with a suggested version B. The user can decline.

Do not ask about things config already answers (voice, Slack channel, sequence shape).

## 4. Read back and wait for a yes (Gate 1)

Show the brief in the template format below, plus:

- the screening plan: "I'll pull about <batch_size x screen_multiplier> people from Apollo, screen their websites, and expect roughly <batch_size> qualifiers."
- the worst-case credit cost: about one credit per qualifier and unclear lead.

Wait for a clear yes. If the user changes anything, update and read back again.

## Brief template

```markdown
# <batch_label>

Status: confirmed <date>
Slug: <slug>
Sender: <sender name> <mailbox> (key <key>)

## Audience
- Companies: <audience>
- Size: <range> employees
- Location: <location>
- Contacts: <titles>

## Qualification rules
### <criterion name, e.g. Partner-led>
- Qualify: ...
- Drop: ...
- Unclear: ...
### Headcount
- Qualify: team page or about page shows <range>
- Unclear: no team page

## Offer
<offer in one or two sentences, what they get, what we ask in return>

## Research
- Drop rules: <defaults> + <offer-specific>
- Opener: <what it should connect to> <pattern, if any>

## Email copy
Source: <pasted | saved offer: outbound/offers/<name>.md | draft for Slack approval>
<the 4 steps, or "to be drafted">

## Reply handling
<from the example, or "none set">

## Test
<"none", or:>
- Test id: <id> (<new | continuing, A <n> / B <n> people so far>)
- What changes: <closing ask of the first email>
- A: "<current text, exactly>"
- B: "<challenger text, exactly>"
- Split: alternate A and B in posting order

## Batch
- Target approved leads: <n>
- Screen about: <n x multiplier>
- Unclear leads: hold for review
- Exclusions: ledger, active Apollo sequences, <extra>
```
