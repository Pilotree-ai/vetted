# Preflight

Run this first, every time. The skill cannot sign in to anything. It can only check that connections already set up by the user are working, and stop clearly if they are not.

## 1. Workspace

Look for `outbound/config.md` in the current directory.

- Missing: copy `templates/config.template.md` to `outbound/config.md`. After the connection checks below, run `setup.md` to fill it in with the user.
- Present but contains `TODO`: run `setup.md` for just those fields after the connection checks.
- Complete: read it and carry on.

Setup runs after the connection checks because most of its answers (mailboxes, names, channels) are looked up from Apollo and Slack.

## 2. Apollo

Call `apollo_users_api_profile` with `include_credit_usage=true` and `include_waterfall_capability=true`.

- Fails or tool missing: stop. Say: "Apollo isn't connected. Add it in claude.ai Settings > Connectors (or `/mcp` in Claude Code), then run this again."
- Note the user's name, the credit balance and the waterfall flags. Reuse them for the rest of the run rather than calling again.

Call `apollo_email_accounts_index`.

- Confirm that the sender mailbox(es) in config appear in the list and are active. Note each one's id.
- No mailbox connected: stop. The mailbox has to be connected in the Apollo web app (Settings > Mailboxes) by the user.

Call `apollo_emailer_campaigns_search` (no filter, `per_page` 50) and count active sequences.

- Compare with `apollo_max_active_sequences` in config (default 2 on lower Apollo plans). If the limit is already reached, warn the user before intake: a new sequence cannot go live until another is switched off or the plan is upgraded.

People search permission is checked in step 2. A free Apollo plan fails there with an upgrade error. If that happens, stop and explain that a paid plan is needed for people search through Claude.

## 3. Slack

Call `slack_search_channels` for the approval channel name in config, or read the channel by its ID with `slack_read_channel` (limit 1).

- Fails or tool missing: stop. Say Slack needs connecting in claude.ai Settings > Connectors.
- Channel not found or not readable: the connected Slack user is probably not a member. Ask them to join the channel. Claude can only post where that user is a member.

If a tracker canvas ID is set, call `slack_read_canvas` to confirm it is readable. If not, tracking still works through the ledger file, and the canvas can be added later.

Read the credit cycle with `apollo_usage_stats_credit_usage_stats` (lead credits used, left and the cycle's end date) for the report and the monthly plan (`credit-plan.md`).

## 4. Report

Give one short status block, then move to intake:

```
Preflight
- Apollo: connected as <name>, <balance> credits left, <n>/<max> active sequences
- Sender mailboxes: <list> (connected)
- Slack: #<channel> OK, tracker canvas OK
- Config: <complete | missing: ...>
```

If anything failed, stop after the report and list exactly what the user needs to do. Do not carry on with a partial setup.

If the connections are fine but config is incomplete, go to `setup.md` now, then on to intake.
