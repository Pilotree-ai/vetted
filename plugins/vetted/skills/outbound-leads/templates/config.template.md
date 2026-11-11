# Outbound config

Standing defaults for the outbound-leads skill. One file per workspace. You don't need to edit this by hand: on the first run the skill asks for every `TODO` in a short dialogue (see `references/setup.md`). You can still edit it at any time, or say "change my outbound config".

## Company

- company_name: TODO            # e.g. Acme
- sending_domain: TODO          # e.g. acme.com

## Products

What you sell, in a sentence or two each. Used in research prompts and when drafting copy.

```yaml
products:
  - name: TODO                  # e.g. Acme Insights
    description: TODO           # one or two plain sentences
    pricing_source: ""          # optional: where current prices live, so copy is checked against it
```

## Senders

One block per person who sends. The skill asks "which sender?" when there is more than one.

```yaml
senders:
  - key: a                      # short id used in sequence names and the ledger
    name: TODO                  # sign-off name, e.g. Sam
    mailbox: TODO               # e.g. sam@acme.com (must be connected in Apollo)
    slack_user_id: ""           # optional, for @-mentions in Slack
    daily_limit: ""             # optional, this mailbox's own daily limit if it differs from mailbox_daily_limit
```

## Slack

- approval_channel_name: TODO   # any channel you choose at setup, e.g. outbound-approvals
- approval_channel_id: TODO     # e.g. C0123456789
- tracker_canvas_id: ""         # e.g. F0123456789. Blank skips the canvas
- tracker_protected_rows: ""    # e.g. "Original rows 1 to 25 are never edited"
- approval_emoji: white_check_mark   # reaction that means "approved"
- approvers: any                # "any", or a list of Slack user IDs allowed to approve

## Apollo

- apollo_max_active_sequences: 2   # 2 on lower plans. Raise if your plan allows more
- sending_schedule_name: Normal Business Hours
- max_emails_per_day: 50          # cap for each new sequence
- mailbox_daily_limit: 150        # most emails one mailbox sends a day, across all its sequences. Match Settings > Mailboxes in Apollo. A sender can override it with daily_limit
- contact_location_default: "London, United Kingdom"   # set on every contact so sends follow UK hours
- benchmark_reply_rate: 0.02     # the reply rate a working sequence should reach. The overview judges zero-reply sequences against it

## Sequence shape

- steps: 4
- step_days: [0, 3, 7, 14]      # days after enrolment (Apollo waits 0, 3, 4, 7 between steps)
- steps_2_to_4_reply_in_thread: true
- include_signature: true       # the mailbox's Gmail signature is the footer
- stop_on_reply: true
- pause_on_out_of_office: true

## Voice

- language: British English
- banned: exclamation marks, em dashes, flattery, invented facts or numbers
- never_claim: results about the prospect nobody has checked (rankings, traffic, what a tool or AI assistant says about them)
- subject_max_chars: 60
- opt_out_line: TODO            # e.g. If this isn't relevant, reply "no" and I won't email again.

## Defaults for screening

- unclear_leads: hold_for_review   # sent to Slack with evidence; the approver keeps or drops
- screen_multiplier: 4             # screen about 4x the target to end up with enough qualifiers
- max_pages_per_site: 3

## Live dashboard

- dashboard: on                    # a private claude.ai page per campaign, updated after every step, plus one overview of every sequence. "off" to skip both

## A/B tests

- ab_tests: offer                   # offer (suggest a test at each intake) | off

## Reply alerts

A Slack alert for every reply, with a draft response. React :+1: or :-1: to record the outcome in Apollo (see `references/replies.md`).

- reply_alerts: on                 # on | off
- interested_list: Vetted - Interested
- not_interested_list: Vetted - Not interested

## Weekly loop

Run one standing campaign every week on a schedule. Set up by saying "set up the weekly loop" (see `references/loop.md`).

- loop: off                        # off | on | paused
- loop_campaign: ""                # slug of the standing campaign
- market_timezone: Europe/London   # the market's time zone, not yours. All loop times use it
- weekly_leads: 60                 # approved-ready emails to prepare each week
- weekly_credit_cap: 90            # most credits one week may spend without asking
- min_credit_balance: 200          # pause instead of enriching below this balance
- no_go_by_monday: hold            # hold (re-check each weekday) | skip (drop the week)
- max_bounce_rate: 0.05            # pause the loop if last week bounced above this

## Holds

Companies or people not to contact until something is checked. The search step excludes them.

```yaml
holds: []
#  - company: Example Ltd
#    reason: confirm whether this is the former Example Agency
```
