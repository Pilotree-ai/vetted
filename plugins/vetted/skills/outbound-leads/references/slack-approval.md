# Slack approval (step 6, Gate 3)

Every email is approved by a person in Slack before anything is created in Apollo. Claude posts as the connected Slack user, with "Sent using Claude" underneath. Claude can only post in channels that user is a member of.

## 1. Intro message (the fixed text)

Post one message in the approval channel (`approval_channel_id` from config) with `slack_send_message`. It shows everything that is the same for everyone, so the group messages only need the personal parts.

```
*<batch_label>*: <n> emails for approval
Sender: <sender name> (<mailbox>) · Sequence: 4 emails on days 0, 3, 7, 14
Audience: <one-line audience from the brief>
Rules: <one line per qualification rule>

*Step 1 template* (subject and first paragraph are personal, shown in each group):
> <step-1 template with {opener} marked>

*Follow-ups* (same for everyone, replies in the same thread):
Day 3: <text>
Day 7: <text>
Day 14: <text>

<if the brief has a test:> Test <id>: A "<text>" · B "<text>". Versions alternate, and each email shows its version.
<if Claude drafted the copy:> This copy is new. React :white_check_mark: here to approve the templates.
Groups follow below. Nothing is loaded into Apollo until a group has a :white_check_mark:.
```

Save the message `ts`. If Claude drafted the copy, the intro also needs a tick before any group is loaded.

## 2. One message per group of 10

Post each group as its own message in the channel, so each has its own reactions and thread. Number people continuously across groups (1 to 10, 11 to 20, ...). Qualifiers first, then unclear leads in their own clearly labelled group(s).

```
*<batch_label>, group <g> of <G>*
React :white_check_mark: to approve all, or reply in the thread with names to remove.

*1. Priya Shah*, Hart & Shah, priya@hartshah.co.uk
Subject: Local search for multi-site vet clinics
Opener: I read your October guide on local search for multi-site clinics, in particular the part about each branch competing with the others for the same searches.
Why: two co-founders run the agency, 9 staff · <evidence URL>

*2. ...*
```

- With a test, add `Version: A` or `Version: B` under the subject line. If an approver rewrites a closing ask, that person leaves the test (`references/ab-tests.md`).
- Add a `Flags:` line when there is one (catch-all (warn), site blocked, weaker opener).
- For unclear leads, add `Unclear: <rule>: <what was or was not found>`.
- Keep each message under Slack's 5,000-character limit. If a group does not fit, split it into two messages with the same group number and "(part 1 of 2)".

Save each group's `ts` and person numbers in `outbound/campaigns/<slug>/05-slack.json`:

```json
{
  "channel_id": "C0123456789",
  "intro_ts": "1730736000.000100",
  "template_needs_approval": false,
  "groups": [
    {"group": 1, "ts": "1730736010.000200", "people": [1,2,3,4,5,6,7,8,9,10], "status": "pending"}
  ]
}
```

Tell the user the groups are posted, link the intro message, and ask them to tell you "approved" when they have reacted. Do not create anything in Apollo until then.

## 3. Reading approvals

When the user says "approved" (or asks you to check):

1. For each pending group, call `slack_get_reactions` with the channel id and the group's `ts`.
2. A group is **approved** if it has the `approval_emoji` reaction from an allowed approver (`approvers` in config, "any" by default).
3. Call `slack_read_thread` on each group's `ts` (and the intro's) and apply what the replies say. Removals can be names, numbers or companies: "remove Priya", "drop 3 and 7", "not Hart & Shah". If a reply asks for an edit ("change 4's subject to ..."), make the edit, post the revised email as a reply in that thread, and ask for a fresh tick on that reply for that person.
4. If anything in a reply is ambiguous, ask the user rather than guessing.
5. Update `05-slack.json`: approved groups, removed people, who approved.

Report: "Groups 1 to 3 approved by <name>. Removed Priya Shah, #7 (<reason if given>). Group 4 has no tick yet."

Only approved groups, minus removals, move to the Apollo load. Unticked groups wait, even if the user says to carry on with "the rest". Point them to the group that still needs a tick. The approval lives in Slack so there is a visible record of who approved what.

After loading, reply in the intro thread: "Loaded <n> into Apollo sequence <name>. Removed: <list>."
