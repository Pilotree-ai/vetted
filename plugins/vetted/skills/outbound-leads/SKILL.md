---
name: outbound-leads
description: Run a full cold-outbound lead campaign from one plain sentence using Apollo.io and Slack. Turns a description like "UK marketing agencies, up to 20 staff, partner-led, founder as contact, 40 leads, offer is a free site audit" into a confirmed campaign brief, then finds people in Apollo, screens each company's own website against the brief, enriches only qualifiers, writes a personal opener per person, gets every email approved in Slack, loads approved contacts into an Apollo sequence and tracks results. Use this skill whenever the user wants to find leads, build a prospect list, start an outreach or cold email batch, run a new outbound campaign, load approved emails into Apollo, check how an outbound batch is doing, see an overview of every sequence and how much mailbox capacity is left, or run outbound on a weekly loop or schedule, even if they do not mention Apollo, Slack or the word "campaign".
---

# Outbound leads

One sentence in, an approved and running outbound batch out. The process and safety rules are fixed and live here. The targeting, offer and copy change every run and live in a campaign brief.

**The core rule: nothing is sent without a human approving it in Slack.** Every step below is designed around that. Cold email goes out from a real person's mailbox on a real company domain. A wrong audience, an invented fact or a burst of volume can damage that domain's reputation for months, and it cannot be undone once sent.

## Where things live

- **Skill files** (this folder): process, prompts, formats. Read-only during a run.
- **Workspace** (the user's current directory, folder `outbound/`): everything specific to this user or team.
  - `outbound/config.md`: standing defaults (company, products, senders, Slack IDs, voice, holds). Created on first run from `templates/config.template.md`, and filled in through a short dialogue (`references/setup.md`). If the user asks to change their setup, run `setup.md` for the fields they name.
  - `outbound/offers/`: the user's saved offers (product, audience, terms, prices, four email steps, reply handling), one file each. Prices and terms only ever live here or in the brief, never in the skill.
  - `outbound/contacted.csv`: ledger of every company and person ever enrolled, across all senders. Used for exclusions.
  - `outbound/overview.html` and `outbound/00-overview.json`: the workspace's one overview page of every sequence, and its URL and version.
  - `outbound/campaigns/<slug>/`: one folder per batch with `brief.md` and the working files for each step, plus `dashboard.html` and `00-dashboard.json` (the live dashboard's page and its URL and versions).

## The run, step by step

Read each reference file when you reach its step, not before. Keep the user informed with one short line per step.

| # | Step | Read | Credits | Gate |
|---|---|---|---|---|
| 0 | Preflight: check Apollo, Slack and plan limits, fill any missing config in a short dialogue, then build this month's plan from the exact credit balance and mailbox limits | `references/preflight.md`, `references/setup.md`, `references/credit-plan.md` | Free | Stop if anything fails |
| 1 | Intake: sentence to brief, size the batch against the month's plan (send now, next week, or held as enrich-ahead), ask gaps, read back. On yes, create the live dashboard | `templates/campaign-brief.md`, `references/dashboard.md` | Free | **Gate 1: brief confirmed** |
| 2 | Apollo search: broad pull, exclusions | `references/apollo-search.md` | Free | |
| 3 | Website screen: qualify, drop or unclear with evidence | `references/qualify-rules.md` | Free | |
| 4 | Enrich qualifiers and unclears only | `references/apollo-search.md` (Enrich section) | **Costs credits** | **Gate 2: cost confirmed** |
| 5 | Research and openers | `references/research-prompt.md` | Free | |
| 6 | Slack approval | `references/slack-approval.md` | Free | **Gate 3: ticks in Slack** |
| 7 | Apollo load: contacts, sequence, overrides, go live | `references/apollo-load.md` | Free | **Gate 4: overrides verified, then go-live confirmed** |
| 8 | Track: ledger, canvas, daily report | `references/tracking.md` | Free | |

Also read `references/lessons-learned.md` once at the start of a run. It is short and explains most of the ways this has gone wrong before. If more than one sender is set up in config, read `references/multi-sender.md` at intake.

**Live dashboard.** As soon as the brief is confirmed, publish the campaign's private dashboard page (`references/dashboard.md`) and give the user its link. At the end of every step, and whenever a gate opens or is answered, update it with that step's people and totals, following the table in `dashboard.md`. It is a read-only mirror. The working files stay the source of truth, approvals stay in Slack, and a dashboard failure never stops the run. Skip it if `dashboard: off` is set in config or the Artifact tools aren't available.

**Outbound overview.** Besides the per-campaign dashboards, each workspace has one overview page of every Apollo sequence: queued, delivered, bounced and replied per sequence, follow-up days, active sequences, and the mailbox's daily slots left for new sequences (`references/overview.md`). Refresh it at the end of every status check and after a sequence goes live, and whenever the user asks how their sequences are doing or how much room is left. There is one per workspace, kept in `outbound/00-overview.json`. Never create a second one.

**A/B tests.** A batch can test one change to the first email, usually the closing ask. The two versions alternate across the batch, each person is put on an Apollo list for their version, and the overview shows which version gets more replies. A winner is only proposed once it's clearly ahead, and the default only changes when the user confirms in chat (`references/ab-tests.md`).

**Deliverability guard.** Every reply check also runs the guard (`references/guard.md`). It stops the other contacts at a company that refused an email as spam, pauses a sequence whose bounces and spam blocks pass Apollo's warning level (and resumes it only on a ✅), and holds new batches while the whole mailbox is bouncing. Every action is posted in the approval channel.

**Monthly credit plan (every run).** Credits and mailbox sends are both limited, and unused Apollo credits expire at the end of each cycle. Every run starts with the plan: preflight reads the exact credit balance, cycle dates and mailbox limits from Apollo, and `scripts/month_plan.py` works out the room week by week plus how many leads to **enrich ahead** with credits that would otherwise expire (`references/credit-plan.md`). Intake sizes the batch against it. Enrich-ahead batches are approved now, held, re-checked and loaded after the reset. The overview shows the same plan under "This month".

**Reply alerts.** When anyone replies to a sequence, post an alert in the approval channel with who replied, which email they answered and a draft response, and record the approver's 👍 or 👎 as an Apollo list on the contact (`references/replies.md`). A routine runs this every two hours on weekdays. Vetted never replies to a prospect itself.

The run can be resumed. Each step writes its output to the campaign folder, so if the user comes back later ("carry on with the agency batch", "check the Slack ticks"), read the brief and the latest working file and pick up from the next step. Do not redo steps that cost credits.

## Weekly loop

The same campaign can run every week on a schedule: prep at the weekend, approval in Slack, sending from Monday, then again the next weekend. When the user asks to set up, change, pause or check the loop, or when a scheduled run starts, read `references/loop.md` and follow it. In a scheduled run there is nobody to ask, so the gates work as that file describes.

## The four gates

Pause and wait for the user at each one. Do not treat silence, a vague "go on" given earlier, or approval of a previous batch as approval of this one. The only exception is the weekly loop's standing approvals, exactly as `references/loop.md` defines them.

1. **Brief.** Read back the full brief (audience, rules, offer, sender, batch size, exclusions) and wait for a clear yes. A vague sentence sent after the wrong audience wastes credits and burns goodwill with real people.
2. **Credits.** Before enriching, state the number of people and the maximum credit cost, plus the current balance. Use the confirmation wording Apollo's tool asks for.
3. **Slack approval.** Each group of 10 needs a tick reaction from an approver, and any removals named in the thread are honoured. No Apollo contacts or sequences are created for a group until it is ticked.
4. **Overrides, then go-live.** After enrolling, check that every contact's step-1 override was actually written. Remove anyone who was not personalised. Only then ask the user to confirm switching the sequence on.

## Choosing parallelism

This skill is built for Claude Code. The website screen and research steps are the slow ones, so run them with parallel subagents: about 10 companies per agent, up to 6 agents at once. Give each agent the brief's rules and the relevant prompt file, and have it return the structured output the prompt file defines. Save each agent's results as they come back, so nothing is lost if the session is interrupted.

## Email voice (applies to every word that might be sent)

These defaults can be changed in `outbound/config.md`. A brief can add rules but should not quietly remove them.

- The opener is based on a real, checkable fact from the prospect's own website. Keep the URL as evidence.
- No invented facts or numbers, no flattery, no exclamation marks, no em dashes.
- British English unless the brief says otherwise.
- Never claim a result about the prospect that nobody has checked (their rankings, traffic, what a tool or AI assistant says about them). Claiming it would be a fabrication.
- Subject under 60 characters.
- Every email ends with the opt-out line from config.
- Per-contact overrides are sent exactly as written. Write the finished text with real names, not merge tags.

## Finishing a run

When the sequence is live, tell the user: the sequence name, how many contacts are enrolled, the sender mailbox, when the first emails should go out, anyone removed and why, credits used, the canvas section that was added, the dashboard link and the overview link. Offer to set up or extend the daily report (`references/tracking.md`).
