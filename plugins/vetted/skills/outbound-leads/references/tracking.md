# Tracking (step 8)

## Ledger

`outbound/contacted.csv` is the source of truth for "have we contacted this company before", across every sender and batch. Update it at load time (enrolled, removed) and during status checks (replied, bounced, finished, opted out).

## Tracker canvas

If `tracker_canvas_id` is set in config:

1. `slack_read_canvas` to get the current section ids. Section ids change after every update, so read again right before each write.
2. Respect `tracker_protected_rows` from config (for example, original rows 1 to 25 are never edited).
3. Each batch gets its own section, appended at the end:

```
## <batch_label>
Sequence: <name> · Sender: <name> · Loaded: <date> · <n> contacts

| # | Name | Company | Email | Status | Last update |
|---|---|---|---|---|---|
| 1 | Priya Shah | Hart & Shah | priya@hartshah.co.uk | Enrolled | <date> |
```

4. Use `slack_update_canvas` with `append` after the last section for a new batch, and `replace` on that batch's table section for status updates. Never touch another batch's section.

## Status check (on demand or daily)

For each live sequence listed in the ledger:

- `apollo_emailer_campaigns_show` for the sequence's overall counts.
- `apollo_emailer_messages_search` or `apollo_emailer_campaigns_activity_feed` for each contact's state: sent step, opened, replied, bounced, finished, paused (out of office).

Claude cannot read reply content through Apollo. Replies land in the sender's Gmail. Reports only say who replied and point the sender to their inbox.

Post a summary to the approval channel:

```
*Outbound daily* <date>
<batch_label> (<sender>): <sent> sent · <replied> replied · <bounced> bounced · <ooo> out of office
New replies: Priya Shah (Hart & Shah), ... (check <sender>'s inbox)
Bounces: ... (catch-all flagged: <n>)
```

Order the summary: replies first, then bounces, then totals. Then update each batch's canvas section and the ledger.

To confirm what was actually sent, read a sent copy with `apollo_emailer_messages_get_content`.

If the batch's brief has reply handling, add one line per new reply with the suggested next step (for example "Yes: run the free check and send the result within a day"). Claude does not reply on the sender's behalf.

## Daily routine

If the weekly loop is on (`references/loop.md`), its `daily` phase already runs this check every weekday. Don't schedule a second routine for it.

Offer to schedule this as a weekday routine at 10:00:

- Claude Code: `/schedule`, with a prompt like "Use the outbound-leads skill to run the daily status check for every live batch and post the summary to Slack."
- claude.ai: claude.ai/code/routines. Attach the Apollo and Slack connectors.

The routine is read-only in Apollo. It never sends, edits or spends credits. On the canvas it updates only the Status column of the batch tables. When a new batch goes live, check that the routine covers it, so no batch is left unwatched.

Routines use the claude.ai connectors on the account, so they report on whichever Apollo and Slack are connected there. With two senders on one Apollo workspace, one routine covers both. Group the summary by sender.
