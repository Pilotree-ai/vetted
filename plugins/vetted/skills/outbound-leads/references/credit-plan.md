# Monthly credit plan

Every Vetted run starts with the month's plan, for whoever is using the skill. Two things limit outbound, and they run out at different rates:

- **Apollo lead credits** are spent once per person, when their email is found. They reset each billing cycle, and **unused credits expire**: Apollo doesn't carry them over, on monthly or annual plans.
- **Mailbox sends** are spent several times per person (4 emails over 14 days by default), and each mailbox has a daily limit set in Apollo.

The plan works out, week by week, how many new leads fit under both limits, and what to do with credits that would otherwise expire: **enrich ahead**. That means finding, screening, enriching, writing and approving next cycle's first batches in the last days of this cycle, then holding them and loading them after the reset.

Read this file in preflight (step 0), at intake (Gate 1), at load (step 7), when setting up or changing the weekly loop, and whenever the user asks how many leads or credits they can use.

## 1. Inputs (preflight)

- **Credits.** `apollo_usage_stats_credit_usage_stats`: `lead_credit.limit`, `consumed`, `left_over`, and `current_credit_cycle.start_date` / `end_date`. These are exact, so never estimate them. Only if the call fails, ask the user for the "lead credits remaining" and renewal date from Apollo (Settings > Plans & Billing), and say the plan uses their numbers.
- **Daily limit.** `apollo_analytics_sync_report` with `{"modality": "today"}`, `group_by: ["email_account_id"]`, metrics `email_daily_limit` and `num_emails_sent`, read by column header. Add up the limits of the sender mailboxes in config (Apollo rotates between them), and add up their sends today. If Apollo returns no limit, use `mailbox_daily_limit` from config.
- **Credits per approved lead.** This cycle's credits used, divided by the approved emails this cycle: count `outbound/campaigns/*/05-slack.json` approvals since the cycle started, held batches included. With no workspace history, use the people emailed in sequences created this cycle. With no history at all, use 1.5 and say it's a guess. Stricter screening raises it, and looser screening lowers it.
- **What's already booked.** The live sequences' queue (contacts waiting at each step). Use the overview's `overview/current` if it exists (save it with `ArtifactData` `get` and `out_dir`). Otherwise build the same shape from `apollo_emailer_campaigns_search` and `apollo_emailer_campaigns_show` (see `overview.md` section 2).
- **Sequence shape.** `step_days` from config, as waits (days 0, 3, 7, 14 become `0,3,4,7`).

## 2. Run the plan

```
python3 scripts/month_plan.py --credits-left <left> --credit-limit <limit> --cycle-end <end_date> \
  --daily-limit <sum of sender limits> --sent-today <sum> --per-lead <x> \
  --overview <saved overview/current.json> --waits 0,3,4,7 --tz <market_timezone> \
  --reserve <credit_reserve> --ahead-days <enrich_ahead_days> --ahead-weeks <enrich_ahead_weeks>
```

Leave out `--overview` if there's nothing to pass (a new account with no live sequences). Add `--json` to read the numbers yourself. The overview page runs the same method in "This month", so chat and page agree.

What it does: one batch a week, launched on Mondays. A new person gets the emails that fall in their launch week (2 by default), then one email in each later week. Each week's new leads are the free sends left after the live sequences and the earlier planned batches, capped at a steady pace of 5 × daily limit ÷ emails per person, and capped by the remaining credits. Credits still left after the weekly batches and a small reserve go to enriching ahead, at most `enrich_ahead_weeks` weeks of next cycle's sending. Anything beyond that would expire. The plan says so, and names another mailbox as the way to use it.

## 3. Show it (preflight report and Gate 1)

In the preflight report, one block:

```
This month (credits reset <date>)
- Credits: <left> of <limit> left · ~<x> per approved lead<, a guess>
- Mailbox: <limit> a day across <n> mailbox(es) · binding limit: <mailbox | credits>
- Room: <this week: n leads | next Monday: n leads> · rest of the cycle: <n> leads, ~<c> credits
- Enrich ahead: <n> leads, ~<c> credits, <from>–<to>, loading from <date> | not needed
- Expiring at the reset: ~<c> credits
```

At intake, size the batch against the plan before the read-back:

- **The one-liner asks for no more than the room:** go ahead, and say which week it uses.
- **It asks for more:** propose the room now and the rest as the next week's batch, or as a held batch when the cycle is ending. Never quietly shrink it. Ask.
- **Inside the enrich-ahead window, with credits that would expire:** offer it in the same question: "This cycle has ~<c> credits that will expire on <date>. Enrich <n> more leads now and hold them to load from <date>?"
- **Credits are the binding limit:** say which week they run out, and suggest a smaller batch or stricter screening.

The batch's plan goes in the brief's `## Batch` section (`templates/campaign-brief.md`): `Send: now (week of <date>)` or `Send: held until <date>`.

## 4. Held batches (enrich ahead)

A held batch runs steps 2 to 6 exactly as normal: search, screen, enrich (Gate 2 states the credits as usual), write, and Slack approval. The Slack intro says `Held batch: approved now, loads from <date>.` Then:

1. **Don't load it.** At step 7, record `06-load.json` with `{"status": "held", "load_from": "<date>"}`, and write `held/<slug>` on the overview page: `{"slug", "label", "people": <approved>, "credits": <spent>, "approved_at", "load_from", "status": "held"}`.
2. **Reminder.** The scheduled reply check (`replies.md` section 6) sets `status: "due"` on or after `load_from` and posts once in the approval channel: "Held batch <label> (<n> approved emails) is ready to load. Say "load the held batch" in Vetted."
3. **Re-check before loading.** When the user asks to load it, re-check every email first:
   - Open each person's evidence URL again. If the fact in their opener is still there, keep the email as approved.
   - If the fact has gone or changed, rewrite the opener from what the site says now (`research-prompt.md` rules), and post only the rewritten emails to Slack for a fresh ✅. Emails that didn't change keep their original approval.
   - Check the ledger and active sequences again, because someone else may have contacted them since. Run guard "Before a load".
4. **Load** as in `apollo-load.md` (overrides verified, then go-live), into a sequence with a daily cap that fits this cycle's plan. Set `held/<slug>` `status: "loaded"`.

Held batches use this cycle's credits and next cycle's mailbox. The plan for the new cycle counts their sends as already booked once they're loaded. Before then, the plan shows them in "Held batches" and keeps that many leads' worth of room free in the first weeks.

## 5. Weekly loop

At setup and at each cycle reset, propose `weekly_leads` = the plan's steady weekly figure, and `weekly_credit_cap` = that × credits per lead, rounded up. The user confirms in chat, and a new cap needs a fresh confirmation (`loop.md`). Scheduled runs never enrich ahead, because extra spending beyond the cap needs a person. When the enrich-ahead window opens, the prep phase adds one line to the Go message: "<c> credits expire on <date>. Say 'enrich ahead' in Vetted to use them for <date>'s batches."

## 6. Cycle reset

The first daily refresh of a new cycle posts the new month's plan in the approval channel (allowance, steady leads per week, credits per lead, binding limit, and any held batches due).

When the daily limit is raised, ramp up: about 80% of the new limit in the first week, then the full limit. The plan uses whatever Apollo reports, so set the mailbox's limit in Apollo itself.
