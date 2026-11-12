# Weekly loop

The same campaign, run every week without anyone at the keyboard. Prep happens at the weekend, approval happens in Slack, sending starts on Monday, and the next weekend it starts again. All times are in the **market's time zone** (`market_timezone` in config), not the user's.

Read this file when the user asks to set up, change, pause or check the loop, and at the start of every scheduled run.

## The week

| When (market time) | Phase | What happens | Apollo |
|---|---|---|---|
| Saturday 09:00 | `prep` | Search, screen, enrich (within the weekly cap), write, post groups and the Go message to Slack | Read only. Nothing is created |
| Sunday 18:00 | `remind` | If any group or the Go message has no tick, reply once in the Go thread | None |
| Monday 07:00 | `load` | If Go is ticked: load the ticked groups, verify every override, switch sending on | Contacts and enrolment |
| Weekdays 10:00 | `daily` | Status report, load groups ticked late, retry a held load, update the dashboard | Read only, plus late loads |

Emails never go out at the weekend. Nothing is loaded on a Saturday or Sunday, and the sequence's sending schedule (`sending_schedule_name`, "Normal Business Hours") only sends on weekdays in each contact's own time zone.

## Settings (config.md, `## Weekly loop`)

- `loop`: `off` (default), `on` or `paused`.
- `loop_campaign`: slug of the standing campaign the loop runs.
- `market_timezone`: IANA name, e.g. `Europe/London`. Taken from the brief's country at setup.
- `weekly_leads`: target number of approved-ready emails per week.
- `weekly_credit_cap`: the most Apollo credits one week may spend without asking.
- `min_credit_balance`: pause the loop instead of enriching if the balance would fall below this.
- `no_go_by_monday`: `hold` (default) or `skip`.
- `max_bounce_rate`: pause if last week's batch bounces above this (default 5%).

## Standing approvals replace the chat gates

A scheduled run has nobody to ask, so the four gates in SKILL.md work like this in loop mode. These are the only exceptions to "do not treat approval of a previous batch as approval of this one".

1. **Brief.** Confirmed once, in chat, when the loop is set up, and saved as the campaign's `brief.md`. Every week reuses it unchanged. A scheduled run never edits the brief, its rules, the offer or the copy. Changes happen in chat, and need a fresh confirmation.
2. **Credits.** The user confirms `weekly_credit_cap` once, in chat, at setup. That acceptance is recorded in `loop.json` (`cap_accepted_at`, `cap`). A week stops enriching when it reaches the cap. Waterfall enrichment and phone reveals are never used in a scheduled run.
3. **Slack ticks.** Unchanged. Each group needs a tick from an approver.
4. **Go-live.** A tick from an approver on that week's **Go message** stands in for the chat "switch it on?". The override check (apollo-load.md step 5) still runs in full, and anyone not personalised is still removed.

If any step needs a decision that isn't covered above, do not guess. Post the question in the Go thread, save state, and end the run. The next run picks up the answer.

## State

- Standing campaign: `outbound/campaigns/<slug>/brief.md`, `00-dashboard.json`, `dashboard.html`, `loop.json`, `seen.csv`.
- Each week: `outbound/campaigns/<slug>/weeks/<YYYY-Www>/` with the usual working files `01-search.csv` to `06-load.json`. The week label is the ISO week of the Monday the batch is for, in market time.
- `seen.csv`: every company domain the loop has screened, with `week,domain,outcome`. Search excludes these as well as the ledger, so a company dropped once is not screened again every week. A company marked unclear and not approved can come back after 12 weeks.
- `loop.json`:

```json
{
  "status": "active",
  "paused_reason": "",
  "cap": 90, "cap_accepted_at": "2026-11-06T14:00:00Z",
  "sequence": {"id": "", "name": ""},
  "weeks": [
    {"week": "2026-W47", "status": "awaiting_go", "go_ts": "1731700000.000100",
     "groups_loaded": [], "credits_used": 61, "prepped_at": "2026-11-14T09:20:00Z"}
  ]
}
```

A week's `status` is one of `prepping`, `awaiting_go`, `held`, `loaded`, `skipped`, `failed`.

## Every scheduled run

1. `git pull`. Read config, `loop.json` and the latest week.
2. If `loop` is not `on`, or `loop.json.status` is `paused`: check the latest Go thread for a "resume" reply from an approver (step 3), otherwise end the run without posting anything.
3. **Control replies.** Read the latest Go thread (`slack_read_thread`). From an approver (config `approvers`), a reply that is just "pause" sets `status: paused` and is answered with "Loop paused. Reply resume to restart." A reply that is just "resume" sets `status: active` and is answered with "Loop resumed. Next prep: <date>." Ignore anything else here. Approval is only ever a reaction.
4. Work out the phase from the current time in `market_timezone`, or use the phase named in the run's prompt (for test runs):
   - Saturday 06:00 to 23:59 → `prep`
   - Sunday 17:00 to 23:59 → `remind`
   - Monday 06:00 to 09:59 → `load`
   - Monday to Friday, any other time → `daily`
   - Otherwise end the run.
5. Run preflight (`preflight.md`), quietly. If Apollo or Slack fails, post one line in the approval channel if Slack works, set `paused_reason`, and end the run. Do not pause for a single failed run, only report it. Pause after two failures in a row.
6. Run the phase.
7. Update the dashboard if it exists and the tools allow it (`dashboard.md`). Never stop on a dashboard error.
8. Commit `outbound/` and push to `main`: `git add outbound && git commit -m "loop: <phase> <week>" && git push`. If the push is rejected, `git pull --rebase` and push once more. If it still fails, post the failure in the Go thread.

Never wait inside a run. Post, save, commit and end. Waiting happens between runs.

## Phase: prep (Saturday)

Skip with one line in the channel if the previous week is still `awaiting_go` or `held`. One batch waits at a time.

1. **Last week's health.** If last week's batch has bounced above `max_bounce_rate`, pause the loop, post the numbers, and stop. A high bounce rate can damage the sending domain.
2. **Credits.** Read the balance. If balance minus `weekly_credit_cap` is below `min_credit_balance`, pause the loop and post why.
3. **Search** (`apollo-search.md` part 1) for about `weekly_leads x screen_multiplier`, excluding the ledger, `seen.csv`, holds and anyone already in a sequence. If nothing new is found, pause with "No new companies match the brief. Widen the brief in chat to continue."
4. **Screen** (`qualify-rules.md`), and append every screened domain to `seen.csv`.
5. **Enrich** (`apollo-search.md` part 2) qualifiers first, then unclear leads, and stop once `weekly_credit_cap` would be passed. Record `credits_used`. State the cost and the balance in the week's notes. This was accepted when the loop was set up.
6. **Write** (`research-prompt.md`), with the full self-check.
7. **Post** the intro and groups (`slack-approval.md`), adding "Week <label> · for Monday <date>" to the intro. Then post the **Go message** last:

```
*Go for Monday? <batch_label>, week <label>*
<n> emails in <G> groups above. React :white_check_mark: here to load the ticked groups into <sequence name> on Monday at 07:00 (<market_timezone>) and keep the weekly loop running.
No tick by then: nothing is sent, and I check again each weekday morning.
Reply "pause" to stop the loop, or "resume" to restart it.
```

8. Save `go_ts`, set the week to `awaiting_go`.

A running A/B test continues every week unchanged (`ab-tests.md`, "In the weekly loop"). If it has become clearly ahead, add its one line to the Go message.

If qualifiers fall short of `weekly_leads`, post the shortfall with the top drop reasons. Never loosen the rules to make up numbers.

## Phase: remind (Sunday)

For the `awaiting_go` week, check the reactions on each group and the Go message. If anything has no tick, reply once in the Go thread: "Reminder: <groups 3 and 5 | the Go message> still need a :white_check_mark: before Monday 07:00." If everything is ticked, post nothing.

## Phase: load (Monday)

For the `awaiting_go` or `held` week:

1. Read the reactions (`slack-approval.md` section 3) on the Go message and every group, and apply thread removals.
2. **No tick on Go:**
   - `hold`: set the week to `held`, reply "Not loaded: the Go message has no tick. I'll check again each weekday at 10:00." in the Go thread, and stop.
   - `skip`: set the week to `skipped`, reply "Skipped this week. Nobody from this batch was contacted.", and stop. Those people are not added to the ledger, so a later week may find them again.
3. **Go ticked:** load only the ticked groups, minus removals, with `apollo-load.md`:
   - The loop uses **one sequence for the whole campaign** (`loop.json.sequence`), so the active-sequence limit is not used up week by week. The first week creates it switched off, then switches it on after step 5 of apollo-load.md (the Go tick is the go-live approval). Every later week enrols into the live sequence as `paused` with `auto_unpause_at` 2 hours ahead, then verifies the overrides inside that window.
   - Anyone whose override did not save is removed before anything can send, exactly as in apollo-load.md.
4. Reply in the Go thread with what was loaded, who was removed and why, and which groups were not ticked. Set the week to `loaded`, update the ledger and tracker.

Groups ticked later in the week are loaded by the `daily` phase, as long as the Go message is ticked.

## Phase: daily (weekdays)

1. If a week is `held`: re-run the load phase checks. Load once Go has a tick.
2. If a week is `loaded` and some groups were not ticked on Monday: load any that now have a tick.
3. Status check and daily summary (`tracking.md`), one summary covering every live week.

## Setting up the loop (in chat)

Say what's happening in one line per step. It runs in the workspace repo (see the README's "Weekly loop" section), because scheduled runs only see what is committed there.

1. Run a normal intake and Gate 1 for the standing brief. Create the campaign folder and the dashboard.
2. Ask, with `AskUserQuestion`: weekly leads, weekly credit cap, and what to do when Go has no tick by Monday. Derive `market_timezone` from the brief's country and confirm it in the same question set. Suggest the weekly leads and cap from the monthly plan (`credit-plan.md`). Show the credit cap as a standing approval: "Each week may spend up to <cap> credits on enrichment without asking."
3. Write the `## Weekly loop` settings, `loop.json` (`cap_accepted_at` now) and an empty `seen.csv`. Set `loop: on`.
4. Commit and push to `main`.
5. Create the scheduled routine with the `/schedule` skill: the workspace repo, the Apollo and Slack connectors, and these triggers in the market time zone (shown for `Europe/London`):

```
CRON_TZ=Europe/London 0 9 * * 6      prep
CRON_TZ=Europe/London 0 18 * * 0     remind
CRON_TZ=Europe/London 0 7 * * 1      load
CRON_TZ=Europe/London 0 10 * * 1-5   daily
```

If one routine cannot hold several schedules, create one routine per line, with the phase named in its prompt. The prompt:

> Run the outbound-leads skill's weekly loop for campaign `<slug>`. Read `.claude/skills/outbound-leads/references/loop.md` and follow "Every scheduled run". Work out the phase from the current time in the market time zone. Commit and push `outbound/` to `main` at the end. Never wait for input inside this run.

6. Offer a test run of the `prep` phase now, with `weekly_leads` temporarily set to 10, so the user sees the Slack messages and the dashboard before the first real Saturday.

To change the loop later (size, cap, time zone, brief), do it in chat in the workspace, confirm, commit and push. A changed cap needs a fresh confirmation and a new `cap_accepted_at`.
