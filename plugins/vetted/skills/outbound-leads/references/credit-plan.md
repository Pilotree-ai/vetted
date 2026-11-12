# Monthly credit plan

Plan each credit cycle so that both limits hold: the Apollo lead credits (spent once per person, at enrichment) and the mailbox's daily sending limit (spent four times per person, over 14 days). The overview page works out the plan every time it refreshes and shows it in "This month". Read this file at intake, when setting up or changing the weekly loop, and when the user asks how many leads or credits they can use.

## Inputs

- **Credits.** `apollo_usage_stats_credit_usage_stats`: `lead_credit.limit`, `consumed` and `left_over`, plus `current_credit_cycle.start_date` and `end_date`. These are exact. Only ask the user if the call fails, and then ask for the number shown in Apollo under Settings > Plans & Billing.
- **Credits per lead.** Credits used this cycle divided by the people emailed in sequences created this cycle. When a workspace is available, count every approved email from `outbound/campaigns/*/` this cycle instead, including batches not yet loaded, because that's more accurate. Round to one decimal place, and keep it between 1.0 and 3.0. Stricter screening raises it, and looser screening lowers it.
- **Mailbox capacity.** The overview's forecast: for each sending day left in the cycle, the daily limit minus what the live sequences will already send. The limit comes from Apollo (`overview.md` step 5).
- **Sequence shape.** The steps and waits from config (default 4 emails, on days 0, 3, 7 and 14).

## The plan

One batch a week, launched on Monday. A batch of N people sends N on day 0 and N on day 3 (launch week), N on day 7 (the next week) and N on day 14 (the week after). Week by week, from the next Monday to the cycle's end:

1. Free sends this week = the week's capacity minus what the live sequences already send that week.
2. Minus the follow-ups that earlier planned batches send this week.
3. New leads this week = what's left ÷ the number of emails a new person gets in their launch week (2 for the default shape), at most a steady pace of 5 × daily limit ÷ emails per person, and at most what the remaining credits pay for.

The plan shows each week's free sends, new leads and credits, the total for the rest of the cycle, the credits left at the reset, and which limit is binding (mailbox or credits). It also shows a full month at the steady pace, so the next cycle can be planned too.

## Using it

- **Intake:** compare the batch size with this week's planned number. If it's bigger, say so and suggest the planned number, or the next week with room.
- **Weekly loop:** at setup and at each cycle reset, propose `weekly_leads` = the plan's steady weekly figure and `weekly_credit_cap` = that × credits per lead, rounded up. The user confirms in chat. A new cap needs a fresh confirmation (`loop.md`).
- **Cycle reset:** the first daily refresh of a new cycle posts the new month's plan in the approval channel: allowance, steady leads per week, credits per lead, and which limit is binding.
- **Credits will go unused:** if the mailbox is the binding limit and more than a quarter of the credits would be left at the reset, say so once and name the ways to use more: another mailbox (ideally on a separate sending domain) or a 3-step sequence.
- **Credits run out early:** if credits are the binding limit, say on which week they run out, and suggest smaller batches or stricter screening.

When the daily limit is raised, ramp up: about 80% of the new limit in the first week, then the full limit. The plan uses whatever limit Apollo reports, so set the mailbox's limit in Apollo itself.
