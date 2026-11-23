# Quick check (scheduled reply runs)

Most scheduled checks find nothing to do. This file settles that in a few turns, and the run reads `replies.md` and `guard.md` only when there is something to act on. Never print the saved documents or `cat` them: `scripts/quick_check.py` reads them.

## 1. Collect

Load `ArtifactData`, `apollo_analytics_sync_report` and `slack_get_reactions` in one `ToolSearch` call. Then make all of these calls in **one message**:

- `ArtifactData` `list` on `replies`, `guard_events`, `guard_pauses` and `held`, each with `query.limit` 1000 and `out_dir` `/tmp/replies/in`.
- `ArtifactData` `get` on `guard/state` with `out_dir` `/tmp/replies/in`. Note its version.
- `apollo_analytics_sync_report`: `date_range` `{"modality": "all_time"}`, `group_by: ["emailer_campaign_id"]`, metrics `num_emails_replied`, `num_emails_bounced`, `num_emails_sent`.
- `apollo_analytics_sync_report`: `date_range` `{"modality": "last_7_days"}`, `group_by: ["email_account_id"]`, metrics `num_emails_sent`, `num_emails_bounced`.

Save the two reports unchanged to `/tmp/replies/all_time.md` and `/tmp/replies/last_7.md`.

If the all-time report says "Showing first 50 of N rows", fetch it again with `filters.emailer_campaign_ids` in batches of 40 sequences, save each batch to its own file, and pass every file with its own `--all-time`.

## 2. Compare

```
python3 plugins/vetted/skills/outbound-leads/scripts/quick_check.py \
  --docs /tmp/replies/in --all-time /tmp/replies/all_time.md --last-7 /tmp/replies/last_7.md
```

Pass `--warning-pct`, `--hold-pct`, `--lift-pct` and `--min-sent` if the run's settings differ from 4, 3, 2 and 100.

**If it exits non-zero, don't conclude that nothing happened.** Follow the full check: `replies.md` sections 1 to 6.

## 3. Read the reactions

Call `slack_get_reactions` for every entry in `reactions_to_check`, all in one message. Only approvers' reactions count.

- `kind: "reply"`: there's something to record if exactly one of 👍 or 👎 is present and it differs from `outcome`, or if both are present.
- `kind: "pause"`: there's something to do if a ✅ is present.

## 4. Act only on what was found

| Found | Read and follow |
|---|---|
| `new_replies` | `replies.md` sections 1 and 2, and the "Email voice" section of `SKILL.md` |
| A reaction to record | `replies.md` section 3 |
| `new_bounces`, `rule3` not `none`, or a ✅ on a pause | `guard.md` "Every check" |
| `rule2_check` | `apollo_emailer_campaigns_show` for each listed sequence. If it's active, `guard.md` "Every check". If it's off, ignore it |
| `held_due` | `replies.md` section 6 |

The rules, Slack wording and allowed Apollo writes in those files apply unchanged.

## 5. Finish

If `guard.md` didn't run, update `guard/state` with `rate_7d`, `sent_7d` and `updated_at`, using the version from step 1. Post nothing in Slack.

End with the block from `replies.md` section 4, or when nothing changed:

```
No new replies or marks. Guard: 0 new problem emails · no new pauses · new batches <allowed | on hold> (<rate>% over 7 days, <bounced> of <sent> sent).
```
