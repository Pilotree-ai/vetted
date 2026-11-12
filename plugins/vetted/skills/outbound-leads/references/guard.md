# Deliverability guard

Bounces and spam blocks hurt the whole sending domain, not just one sequence, and the damage grows with volume. Apollo pauses a sequence on its own only after 200 sends in 7 days, which small Vetted batches rarely reach. The guard fills that gap. It runs with the reply check (every two hours on weekdays) and acts on its own, because waiting hours for a person while a bad sequence keeps sending is the larger risk. Every action is reversible, every action is announced in the approval channel, and anything that would start sending again needs a person's ✅.

Read this file at the end of every reply check (`replies.md` section 5), before every load (`apollo-load.md` step 1), and when the user asks about spam, bounces or deliverability.

## What counts as a problem

- **Spam blocked:** the recipient's mail server refused the email as spam (`spam_blocked: true` on the message). It never arrived.
- **Hard bounce:** the address doesn't exist (an event of type `hard_bounce`).
- **Soft bounce:** a temporary failure (a full mailbox, a server down). The guard records these but never acts on them.

The guard can't see emails that were delivered into a junk folder: Apollo, and every other sender, only learns about refusals. If the user asks about junk-folder placement, explain this and suggest an inbox placement test (seed addresses at Gmail and Outlook) or Google Postmaster Tools for the sending domain.

## The three rules

| Rule | Trigger | Action |
|---|---|---|
| **1. Company** | Any new spam block or hard bounce | Stop the other contacts at the same company domain who are still active in any sequence. That company's filter has already flagged the sender, and more emails there only add complaints |
| **2. Sequence** | A sequence has 2 or more spam blocks or hard bounces, and they are at least `auto_pause.warning_pct` (4%) of its sent emails | Pause the whole sequence. Resume only on a ✅ |
| **3. Mailbox** | Over the last 7 days, bounces (Apollo counts spam blocks as bounces) are 3% or more of 100 or more sent emails | Put new batches on hold. Vetted loads nothing new until the rate falls below 2% |

Thresholds come from config `## Deliverability guard` and default to the values above.

## Where state lives

On the overview page's database (`overview.md`), so the scheduled check needs no workspace. Every write to an existing document passes its `if_version`.

- `guard_events/<emailer message id>`: one per problem email.

```json
{
  "message_id": "...", "type": "spam_blocked", "failed_at": "<ISO>", "reason": "Spam Blocked",
  "sequence_id": "...", "sequence_name": "...", "step": 2,
  "contact_id": "...", "name": "Sam Lee", "company": "Acme Payroll", "domain": "acmepayroll.com",
  "action": {"kind": "stopped_company", "stopped": [{"contact_id": "...", "name": "...", "sequence_id": "..."}], "note": ""},
  "slack": {"channel_id": "...", "ts": "..."}, "recorded_at": "<ISO>"
}
```

`action.kind` is `stopped_company`, `none` (nobody else was active there, or a free-mail domain), or `recorded` (a soft bounce).

- `guard_pauses/<sequence id>`: `{"sequence_id", "sequence_name", "status": "paused" | "resumed", "paused_at", "problems", "sent", "rate", "slack": {...}, "resumed_at", "resumed_by", "baseline_problems"}`.
- `guard/state`: `{"hold_new_loads": false, "reason": "", "since": "", "rate_7d": 0.004, "sent_7d": 385, "updated_at": "<ISO>"}`.

## Every check

1. **Read state.** `ArtifactData` `list` on `guard_events`, `guard_pauses` (`query.limit` 1000), and `get` on `guard/state`. Note every version.
2. **Find failures.** One `apollo_analytics_sync_report` call: `{"modality": "all_time"}`, `group_by: ["emailer_campaign_id"]`, metric `num_emails_bounced`. Read columns by header. For every sequence with more bounced emails than it has `guard_events`, call `apollo_emailer_messages_search` with that `emailer_campaign_id`, `emailer_message_stats: ["spam_blocked", "bounced"]` and `per_page` 50. Each message id without a document is new. Type: `spam_blocked` if `spam_blocked` is true, `hard_bounce` if an event has type `hard_bounce`, otherwise `soft_bounce`.
3. **Who and which step.** `apollo_contacts_search` with `emailer_campaign_ids: [sequence id]`, `per_page` 100 and `fields: [{"contacts": ["id", "first_name", "last_name", "email", "organization_name"]}]`, paged until the contact is found. The domain is the part of their email after `@`. The step comes from `variant.touch_id`, matched against `apollo_emailer_campaigns_show`'s `emailer_touches` as in `replies.md`.
4. **Rule 1, for each new spam block or hard bounce.**
   - Skip free-mail domains (gmail.com, outlook.com, hotmail.com, yahoo.com, icloud.com, aol.com, proton.me and similar) with `action.kind: "none"` and a note.
   - Find the others: `apollo_contacts_search` with `q_keywords: "<domain>"`, `per_page` 100 and `fields: [{"contacts": ["id", "first_name", "last_name", "email", "contact_campaign_statuses"]}]`. Keep only contacts whose email ends in `@<domain>`, other than the failed one, with a `contact_campaign_statuses` entry that is active or paused (not finished, so anyone who replied is left alone).
   - Stop them with `apollo_emailer_campaigns_remove_or_stop_contact_ids`: `mode: "stop"` (never `remove`), the contact ids, the sequences they are active in, and `stop_reason: "Vetted guard: an email to <domain> was refused as spam on <date>"` (or "bounced as a non-existent address").
   - Post in the approval channel:

```
:warning: *<Spam block | Hard bounce> at <company>* (<domain>)
<name>'s step <n> email in <sequence name> was <refused as spam | rejected: address doesn't exist> on <date>.
<Stopped <m> other contact(s) at <domain>: <names>. | Nobody else at <domain> was still active.>
Stopped contacts can be added back in Apollo if this was a one-off.
```

   - Save the event document as soon as its post is out, so a failed run never posts it twice. Record soft bounces silently (`action.kind: "recorded"`, no post).
5. **Rule 2, for each sequence.** Problems = its `guard_events` of type `spam_blocked` or `hard_bounce`. Sent = the sequence's `sent` from `apollo_emailer_messages_search` with `display_mode: "metadata_mode"`. If problems ≥ 2, problems ÷ sent ≥ `warning_pct` ÷ 100, the sequence is active, and it has no `guard_pauses` document with `status: "paused"` (or, after a resume, problems minus `baseline_problems` ≥ 2), pause it:
   - `apollo_emailer_campaigns_show` for the sequence. Then `apollo_sequences_update` with `id`, `active: false` and `emailer_steps` rebuilt **exactly** from the show response: every step with its `id`, `position`, `type`, `wait_time` and `wait_mode`, and every touch with its `id`, `type`, `status`, `include_signature` and `emailer_template` (`id`, `subject`, `body_html`). Change nothing else. The update treats the step list as the full intended state, so a missing step or touch would be deleted.
   - Call `apollo_emailer_campaigns_show` again and check that the sequence is inactive and that every step and touch id is still there. If anything is different, post that in the channel straight away and don't try again.
   - Post:

```
:octagonal_sign: *Paused <sequence name>*
<problems> of its <sent> emails were refused as spam or bounced (<rate>%), at or above Apollo's <warning_pct>% warning level. Nothing more sends from it.
Check the failed addresses on the overview, then react :white_check_mark: here to switch it back on.
```

   - Save the `guard_pauses` document (`status: "paused"`).
6. **Resume.** For each `guard_pauses` document with `status: "paused"`, read the ✅ reactions on its Slack post (`slack_get_reactions`). If an approver has reacted, switch the sequence back on: rebuild from `apollo_emailer_campaigns_show` exactly as in step 5 with `active: true`, verify, reply in the thread "Switched back on by <name>.", and set `status: "resumed"`, `resumed_at`, `resumed_by` and `baseline_problems` to the current problem count. The ✅ is the go-live confirmation: never switch a paused sequence on without it.
7. **Rule 3.** `apollo_analytics_sync_report` with `{"modality": "last_7_days"}`, `group_by: ["email_account_id"]`, metrics `num_emails_sent`, `num_emails_bounced` (read by header, add up the mailboxes). With 100 or more sent: a rate of 3% or more sets `hold_new_loads: true` (post once: ":no_entry: New batches are on hold: <rate>% of <sent> emails bounced or were refused as spam in the last 7 days. Running sequences carry on. Vetted loads nothing new until it's under 2%."), and a rate under 2% clears it (post once: "Hold lifted: bounces are back to <rate>%."). Between 2% and 3%, leave the state as it is. Always update `rate_7d`, `sent_7d` and `updated_at`.
8. **Report.** Add to the run's final block: `Guard: <n> new problem emails · <m> contacts stopped · <paused sequences or "no pauses"> · new batches <on hold | allowed> (<rate>% over 7 days)`.

## Before a load (apollo-load.md step 1)

Read `guard/state`. If `hold_new_loads` is true, stop and tell the user why. Load only if the user explicitly says to go ahead anyway in chat. Also don't enrol anyone at a domain with a `guard_events` spam block in the last 30 days, and say who was left out.

## Limits

- The guard only writes three things to Apollo: stopping contacts (rule 1), switching a sequence off (rule 2), and switching it back on after a ✅ (step 6). It never removes contacts, edits emails or spends credits.
- If a step's Apollo call fails, post nothing for that step, save nothing, and let the next check try again. Never retry a sequence update that changed something unexpected.
