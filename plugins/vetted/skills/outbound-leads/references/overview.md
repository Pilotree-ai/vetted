# Outbound overview (all sequences)

One private claude.ai page per workspace that shows every Apollo sequence at once. It answers six questions:

- **Which sequence is not working:** a verdict for each sequence (Hurting deliverability, Not sending, Not working, Lagging, Too early, Working, Off) with the reason and the next step. Zero replies only counts as "not working" once enough people have been emailed: the page works out the chance of seeing no replies at the expected reply rate, which the viewer can change on the page.
- **Capacity:** how many sequences there are and which are active, each one's daily cap and follow-up days, what is queued, and how much of the mailbox's daily limit is left for a new sequence.
- **Which campaign is working:** batches of the same offer grouped together, with reply rate, interested count and bounce rate.
- **Which step gets the replies:** replies and reply rate for steps 1 to 4 across all sequences.
- **Deliverability:** the mailbox's bounce rate over the last 7 days, and each sequence's bounces and spam blocks against Apollo's warning and auto-pause levels.
- **Daily activity:** emails sent per day against the daily limit, with replies and bounces, from a history that grows by one record a day.

The per-campaign dashboards (`dashboard.md`) stay as they are. This page sits above them.

There is only ever **one** overview per workspace, at one fixed URL. Each refresh overwrites its data and adds one history record. Never create a second page in a later session.

Read this file when the user asks for the overview ("show my sequences", "how much room is left for a new sequence", "outbound dashboard", "how are my outbound sequences doing?", "which campaign is working?"), at the end of every status check (`tracking.md`), and after a sequence goes live (`apollo-load.md` step 7).

## When to skip it

The same rules as `dashboard.md`: skip silently if `dashboard: off` is set in config. If the `Artifact` or `ArtifactData` tool is missing, say so once and carry on. If any overview call fails, say so in one line and carry on. An overview failure never stops a run or a status check.

## 1. Find or create it

1. Read `outbound/00-overview.json` (`{"url": "...", "versions": {"overview/current": 3, "history/2026-11-10": 1}}`). If it exists, use that URL.
2. If it doesn't exist, ask the user once: "Do you already have a Vetted overview page? Paste its link, or I'll create one." Use a pasted link and save it. A new session must never quietly create a second page.
3. To create it, copy `templates/overview-dashboard.html` to `outbound/overview.html` and publish it with `Artifact`:
   - `file_path`: `outbound/overview.html`
   - `icon`: `"chart"`
   - `description`: "Every Apollo sequence in one place: which campaign gets replies, replies by step, deliverability, daily activity, and the mailbox capacity left for new sequences."
   - `capabilities`: `{"db": {"rules": [{"path": "", "read": "view", "write": "admin"}]}}`
4. Save `outbound/00-overview.json` with the URL and an empty `versions`, then backfill the history (section 3) from the earliest sequence's `created_at` to today. Give the user the link in one line.

If the page needs republishing after a skill update, read it first with `Artifact` `action: "read"` and `url`, then publish the new copy of the template with that `url`. Leave out `capabilities` and `icon`.

## 2. Collect the data (read-only, free)

Every call here is read-only and costs no credits.

Apollo's analytics reports come back as a markdown table, and Apollo picks the column order itself, not the order the metrics were asked for. Always read a value by its column header ("Num emails sent", "Email daily limit" and so on), never by position. A swapped column once recorded a daily limit of 17 with 150 sent.

1. `apollo_emailer_campaigns_search` (`per_page` 100, page through all of them). Skip `archived: true`. For each sequence, keep `id`, `name`, `sequence_url`, `active`, `created_at`, `last_used_at`, `max_emails_per_day`, `user_id`, `emailer_steps` (position, `wait_time`) and `unique_delivered`.
2. For each sequence, `apollo_emailer_messages_search` with `emailer_campaign_id` and `display_mode: "metadata_mode"`. From `status_counts`, read `scheduled` (queued), `delayed` (scheduled but held back by a sending limit), `sent`, `delivered`, `bounced`, `replied`, `spam_blocked` and `demoed` (interested). A missing status means 0.
3. **By step.** One `apollo_analytics_sync_report` call: `date_range` `{"modality": "all_time"}`, `group_by: ["emailer_step_id"]`, metrics `num_emails_sent`, `num_emails_replied`, `num_emails_bounced`. Each row is labelled `<sequence name>: Step <n>`. Match rows to sequences by exact name and step number.
4. **Queue by step.** For each **active** sequence, `apollo_emailer_campaigns_show`, keeping only the top-level `emailer_steps[].counts.active` (contacts waiting at each step), `emailer_campaign.contact_statuses`, `emailer_campaign.auto_pause_config` and `sending_diagnostics.issues`. These responses are large because they include the templates. With more than 5 active sequences, give the `show` calls to one subagent and ask it for exactly those fields as compact JSON. For a sequence that is off, the step counts aren't needed.
5. **Mailbox limit and today's sends.** `apollo_analytics_sync_report` with `date_range` `{"modality": "today"}`, `group_by: ["email_account_id"]` (rows are labelled with the mailbox address), metrics `email_daily_limit`, `num_emails_sent`. Don't group by `send_from_email`: Apollo rejects `email_daily_limit` with it. Query one day only, because over a longer range `email_daily_limit` comes back summed. If Apollo returns no limit, use the sender's `daily_limit` from config, else `mailbox_daily_limit` (default 150).
6. **Daily history.** `apollo_analytics_sync_report` with `range_start` the day after the last history date in `00-overview.json` (or the earliest sequence's `created_at` on a backfill) and `range_end` today, `group_by: ["smart_datetime_day"]`, metrics `num_emails_sent`, `num_emails_delivered`, `num_emails_replied`, `num_emails_bounced`, `email_daily_limit`. Always include yesterday and today again, because their numbers change during the day.
7. `apollo_email_accounts_index` to match each sender's mailbox to its Apollo `user_id`.
8. **A/B tests.** Always list the page's `tests` collection (`ArtifactData` `list`, `collection: "tests"`). If it has any document with `status: "running"`, one `apollo_analytics_sync_report` call: `date_range` `{"modality": "all_time"}`, `group_by: ["contact_label_ids"]`, metrics `num_contacts_emailed`, `num_contacts_replied`. Update each running test's `results` as "Results" in `ab-tests.md` describes, in the same batch as the other writes.
9. **Credits.** `apollo_usage_stats_credit_usage_stats`: save `credits` as `{"limit": lead_credit.limit, "used": lead_credit.consumed, "left": lead_credit.left_over, "cycle_start": current_credit_cycle.start_date, "cycle_end": current_credit_cycle.end_date, "checked_at": "<ISO>"}`. The page builds the monthly plan from it (`credit-plan.md`). With a workspace, also set `credits.per_lead` as `credit-plan.md` describes. On the first refresh after `cycle_end` has passed, post the new month's plan in the approval channel if Slack is available.

## 3. Write it

Write everything in one `ArtifactData` `action: "batch"`: the `overview/current` document, plus one `history/<YYYY-MM-DD>` document per day from step 6. Pass each document as a `file_path` (build the JSON in `outbound/.overview-cache/`). Every entry for a document that already exists needs its `if_version` from `versions` in `00-overview.json`. Leave it out only when creating one. Save every version from the result back to `versions`. If a write is refused for a version mismatch, `get` that document's current version and redo the batch.

`overview/current`:

```json
{
  "updated_at": "2026-11-10T13:05:00Z",
  "timezone": "Europe/London",
  "max_active_sequences": null,
  "senders": [{"name": "Sam", "mailbox": "sam@acme.com", "user_id": "<apollo user id>", "daily_limit": 150, "sent_today": 4, "limit_source": "apollo"}],
  "new_sequence": {"daily_cap": 50, "waits": [0, 3, 4, 7]},
  "auto_pause": {"warning_pct": 4, "pause_pct": 6, "window_days": 7, "min_volume": 200},
  "benchmark_reply_rate": 0.02,
  "credits": {"limit": 3040, "used": 583, "left": 2457, "cycle_start": "<ISO>", "cycle_end": "<ISO>", "checked_at": "<ISO>"},
  "sequences": [{
    "id": "<apollo id>", "name": "UK agencies, partner-led - batch 2 - Sam", "url": "<sequence_url>",
    "campaign": "UK agencies, partner-led",
    "active": true, "archived": false, "owner_user_id": "<user_id>", "created_at": "<ISO>", "last_used_at": "<ISO>",
    "daily_cap": 50,
    "steps": [
      {"position": 1, "wait": 0, "active": 25, "sent": 25, "replied": 1, "bounced": 0},
      {"position": 2, "wait": 3, "active": 25, "sent": 0, "replied": 0, "bounced": 0}
    ],
    "emails": {"queued": 50, "delayed": 0, "sent": 25, "delivered": 25, "bounced": 0, "replied": 1, "spam_blocked": 0, "interested": 0},
    "reached": 25, "contacts_total": 50,
    "contact_statuses": {"active": 50, "paused": 0, "finished": 0, "bounced": 0, "failed": 0},
    "issues": ["schedule_owned_by_another_user"],
    "dashboard_url": ""
  }]
}
```

- `campaign`: the batch label from the campaign's `brief.md` when the sequence came from a Vetted campaign. Otherwise leave it out, and the page groups by sequence name, dropping endings such as "- batch 2", "- US batch 1" and "- <sender>".
- `timezone`: `market_timezone` from config.
- `senders[]`: `daily_limit` and `sent_today` from step 5, with `limit_source` `"apollo"` or `"config"`.
- `max_active_sequences`: `apollo_max_active_sequences` from config, or `null` if the plan allows more than are in use.
- `new_sequence`: `max_emails_per_day` and the `step_days` from config, turned into Apollo waits (days 0, 3, 7, 14 become 0, 3, 4, 7).
- `auto_pause`: from `auto_pause_config` (`warning_threshold_pct`, `auto_pause_threshold_pct`, `evaluation_window_days`, `min_volume`) of any active sequence. They are account settings.
- `benchmark_reply_rate`: `benchmark_reply_rate` from config (default 0.02). The verdicts judge zero replies against it.
- `last_used_at`: when the sequence last sent, from the search. With emails queued and nothing sent for 2 working days, the page calls the sequence "Not sending".
- `contact_statuses`: from `show`, numbers only (leave out any value Apollo returns as "loading").
- `steps[]`: `active` from step 4 (0 for a sequence that is off), and `sent`, `replied` and `bounced` from step 3.
- `reached`: step 1's `sent`, the number of people who got the first email. `contacts_total`: sum of `contact_statuses` values that are numbers.
- `dashboard_url`: the campaign dashboard URL from `outbound/campaigns/<slug>/00-dashboard.json`, where that campaign's sequence name matches. Otherwise `""`.
- Include sequences that Vetted didn't create too. The mailbox limit counts every email the mailbox sends.

The page also reads `held/<slug>` documents (held enrich-ahead batches, written at load time, see `credit-plan.md` section 4), and an optional `plan_settings` field on `overview/current` (`{"reserve": 50, "ahead_days": 10, "ahead_weeks": 2}` from config). Leave `plan_settings` out to use those defaults.

The page also reads the guard's `guard_events`, `guard_pauses` and `guard/state` (`guard.md`) to list every blocked or bounced email, the automatic stops and pauses, and any hold on new batches. The overview refresh never writes those.

The page also reads the `replies` collection, which reply alerts write (`replies.md`). It lists every reply and counts the ones marked 👍 as interested. The overview refresh never writes to `replies`.

`history/<YYYY-MM-DD>` (document id is the date, in the market time zone):

```json
{"date": "2026-11-10", "sent": 4, "delivered": 4, "replied": 0, "bounced": 0, "daily_limit": 150, "queued": 363, "partial": true}
```

- `queued`: total queued across all sequences, only on today's record (it is a snapshot taken at the refresh).
- `partial: true` on today's record. The next refresh rewrites it with the final numbers.
- History covers the whole Apollo workspace. With more than one sender it isn't split by mailbox.

**Refresh from Apollo button.** The page can also refresh itself: anyone who can edit it gets a Refresh from Apollo button that makes the same read-only calls as section 2 with the viewer's own Apollo connection, then writes `overview/current`, the last two `history` days and running tests' `results` in the same shape. It needs the page published with `capabilities` `{"db": {"rules": [{"path": "", "read": "view", "write": "admin"}]}, "user": {}, "mcp": {"servers": [{"server": "<Apollo connector>", "tools": ["apollo_emailer_campaigns_search", "apollo_emailer_messages_search", "apollo_emailer_campaigns_show", "apollo_analytics_sync_report", "apollo_email_accounts_index"]}]}}`. When this section's fields change, change the page's refresh code to match (`refreshFromApollo` in the template).

The page does every calculation itself (slots left, the forecast, the largest batch that fits, campaign grouping, rates), so the documents hold only facts from Apollo and config.

## 4. Report in chat

One short block, then the link:

```
Outbound overview (<date>)
- Sequences: <n> (<a> active) · Mailbox limit <limit>/day, <sent_today> sent today
- Queued <q> · Delivered <d> · Replied <r> · Bounced <b>
- Best campaign: <name>, <replied> replies from <reached> people (<rate>)
- Needs attention: <sequences the page would mark Hurting deliverability, Not sending, Not working or Lagging, or "none">
- Replies by step: <s1> · <s2> · <s3> · <s4>
- Tests: <id>: A <r>/<n>, B <r>/<n>, <verdict from scripts/ab_test.py> (one line per running test, or leave out)
<url>
```

Add one line only when it applies:
- Any sequence's bounces are at or above `auto_pause.warning_pct`, or the mailbox's 7-day bounce rate is above 2%: name them.
- The active sequences' caps add up to more than the mailbox limit: the mailbox limit decides the pace, and slots left are on the page.

Don't work out the forecast in chat. The page's numbers are the reference.

## Scheduled refresh (no workspace)

A daily cloud routine can refresh the overview with only this skill's repo and the Apollo connector, without an `outbound/` folder. In that case:

- The routine's prompt gives the overview URL and the config values that would otherwise come from `outbound/config.md`: time zone, fallback daily limit, new-sequence cap and step days, senders, and the active-sequence limit.
- Read the versions from the page itself instead of `00-overview.json`: `ArtifactData` `get` on `overview/current`, and `list` on `history` (`query.limit` 1000, `out_dir` a temp folder). The latest history date is where step 6 starts.
- Build the JSON files in a temp folder and write them exactly as in section 3.
- Leave out `campaign` and `dashboard_url`, which need the workspace files.
- Never create a page and never republish one. If the `ArtifactData` tool is missing or a write is refused, end the run and say why in the final message.
- Read-only everywhere else. No Slack posts, no commits, no Apollo writes, no credits.
- Finish with the chat block from section 4 as the run's final message.

## Privacy

The overview holds sequence names, counts and mailbox addresses, but no prospect names or emails. It is private when created. If the user wants to share it, suggest sharing it inside their organisation only.
