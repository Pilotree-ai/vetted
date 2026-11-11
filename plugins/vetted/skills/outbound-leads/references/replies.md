# Reply alerts and marking (Slack)

Replies are rare, and a fast, relevant answer is what turns one into a call. This file does two things:

1. **Alert.** When someone replies to any sequence, post an alert in the approval channel. It says who replied, their company, which email they answered and what that email promised, with a draft response in the thread.
2. **Mark.** An approver reacts 👍 (interested) or 👎 (not interested) on the alert. Vetted records the outcome in Apollo as a list on the contact, and on the overview page.

Read this file when the user asks to set up or check reply alerts, when they ask "any replies?", and at the start of every scheduled reply check.

**Vetted never replies to a prospect.** The alert and draft are for the sender, who reads the real reply in their own inbox and answers it themselves. Claude can't see what the prospect wrote: Apollo only records *that* they replied. Say so in every alert.

## Where state lives

The alerts are tracked in the overview page's database (`overview.md`), so the scheduled check needs no workspace. Collection `replies`, one document per reply, with the Apollo email message id as the document id:

```json
{
  "message_id": "<apollo emailer_message id>",
  "sequence_id": "<apollo id>", "sequence_name": "UK agencies - batch 2 - Sam",
  "contact_id": "<apollo contact id>",
  "first_name": "Priya", "last_name": "Shah", "title": "Founding Partner",
  "company": "Hart & Shah", "domain": "hartshah.co.uk", "location": "Bristol, United Kingdom",
  "step": 2, "step_summary": "Asked them to reply with the formats their clients send, offering a one-page outline back",
  "detected_at": "<ISO>",
  "slack": {"channel_id": "C0123456789", "ts": "1731700000.000100"},
  "outcome": "pending",
  "marked_by": "", "marked_at": "",
  "apollo_list": ""
}
```

`outcome` is `pending`, `interested` or `not_interested`. Every write to an existing document needs its `if_version` (the overview's rules in `overview.md` section 3). Write all changed documents in one `ArtifactData` `batch`.

## Settings (config.md, `## Reply alerts`)

- `reply_alerts`: `on` (default) or `off`.
- `interested_list`: Apollo list name for 👍. Default `Vetted - Interested`.
- `not_interested_list`: Apollo list name for 👎. Default `Vetted - Not interested`.
- `approvers`: from `## Slack`. Only their reactions count. `any` means anyone in the channel.

The approval channel is `approval_channel_id` from config.

## 1. Find new replies

1. Read the existing `replies` documents: `ArtifactData` `list`, `collection: "replies"`, `query.limit` 1000, `out_dir` a temp folder. Note every `message_id` and its version.
2. One `apollo_analytics_sync_report` call: `date_range` `{"modality": "all_time"}`, `group_by: ["emailer_campaign_id"]`, metric `num_emails_replied`. Only sequences with more replies than they have documents need step 3.
3. For each of those sequences, `apollo_emailer_messages_search` with `emailer_campaign_id`, `emailer_message_stats: ["replied"]` and `per_page` 50. Any message id with no document is a new reply.
4. For each new reply:
   - **Who.** `apollo_contacts_search` with `emailer_campaign_ids: [sequence id]`, `per_page` 100, and `fields: [{"contacts": ["id", "first_name", "last_name", "title", "organization_name", {"account": ["domain"]}, "city", "country"]}]`. Page through until the message's `contact_id` is found.
   - **Which email.** `apollo_emailer_campaigns_show` for the sequence (once per sequence per run). The message's `variant.touch_id` matches an `emailer_touches[].id`. Its `emailer_step_id` gives the step position, and its template gives that step's text.
   - **What they were sent.** For step 1, Vetted sends every person their own email, so read it with `apollo_emailer_campaigns_step_content` (`id` the sequence, `contact_ids: [contact id]`, `emailer_step_id` step 1's id). For later steps, the template text is what they got, with their first name filled in.
   - **Workspace extras (when `outbound/` exists).** The campaign's `brief.md` reply handling, and the person's screening evidence from `02-screen.json` and `04-research.json`. Leave them out in a scheduled run without a workspace.

## 2. Post the alert

One message per new reply in the approval channel, with `slack_send_message`:

```
*New reply:* <first name> <last name>, <title> at <company> (<city>, <country>)
Sequence: <sequence name> · replied to step <n>
Step <n> said: "<one sentence: the email's ask or promise, quoted or closely paraphrased>"
Read their reply in <sender mailbox>. Vetted can't see what they wrote.
React :+1: if they're interested or :-1: if not. Vetted records it in Apollo and on the overview.
```

Then reply in that message's thread with the draft:

```
*Draft response* (not sent, edit it to fit what they actually said):
<the draft>
```

Draft rules:
- Follow the email voice rules in SKILL.md: no invented facts or numbers, no flattery, no exclamation marks, no em dashes. Use the config language unless the prospect's country clearly uses another variety of English.
- Keep to 60 to 120 words, and write it as the next message in the same thread, signed with the sender's name.
- Deliver what the email they replied to promised, or the next step it asked for. If step 2 offered "a one-page outline", the draft says the outline is coming and asks the one question needed to write it. If step 1 asked for a call, the draft offers two concrete time windows and a short alternative.
- Because the reply itself is unknown, write it so it still works whether they said "yes", "tell me more" or asked a question. No assumptions about what they said.
- Use the brief's reply handling when the workspace has it.

Save the document (`outcome: "pending"`, the Slack `channel_id` and `ts` from the post). Save each document as soon as its alert is posted, so a failed run never posts the same alert twice.

If Slack fails, don't save the document, so the next run tries again.

## 3. Read the marks

For every document whose `outcome` is `pending`, or that was marked in the last 14 days:

1. `slack_get_reactions` on its `slack.channel_id` and `slack.ts`.
2. Count only reactions from approvers. `+1` (or `thumbsup`) means interested, `-1` (or `thumbsdown`) means not interested.
3. Exactly one of them present, and different from the stored outcome:
   - `apollo_labels_add_entity_ids_to_label_names` with `entity_ids: [contact_id]`, `modality: "contacts"`, `label_names` the matching list. If the contact was on the other list, also remove it with `apollo_labels_remove_entity_ids_from_label_names`. Never use `apollo_contacts_update` for this, because it replaces all of a contact's lists.
   - Update the document (`outcome`, `marked_by` with the reacting user's name, `marked_at`, `apollo_list`).
   - Reply in the alert's thread: "Marked interested in Apollo (list: Vetted - Interested)." or "Marked not interested in Apollo (list: Vetted - Not interested)."
4. Both present: leave it, and reply in the thread once: "Both :+1: and :-1: are on this one. Remove one and I'll record the other." Don't repeat this on later runs.
5. Neither present: nothing to do.

These two list writes are the only Apollo writes this file makes, and each one happens only after a person's reaction.

## 4. Report

End with one short block:

```
Replies (<date> <time>)
- New: <n> (<names and companies>) · alerts posted in #<channel>
- Marked: <n> interested, <n> not interested
- Waiting for a mark: <n>
```

If nothing changed, a one-line "No new replies or marks."

## Scheduled check (no workspace)

A cloud routine runs this file every two hours on weekdays, with the Apollo and Slack connectors and this skill's repo. Its prompt gives the overview URL, the approval channel id and name, the sender's name and mailbox, the approvers and the list names. In that case:

- Read and write the `replies` documents exactly as above, and leave out the workspace extras.
- Post only in the approval channel named in the prompt. Write to Apollo only the list changes in section 3.
- Never wait inside a run. Post, save and end.
- Finish with the section 4 block as the run's final message.

## Setting it up (in chat)

1. Confirm the approval channel, approvers and list names, and save the `## Reply alerts` settings.
2. Make sure the overview page exists (`overview.md`), since the alerts are stored there.
3. Create the routine with the `/schedule` skill: the skill's repo, the Apollo and Slack connectors, and cron `0 7-21/2 * * 1-5` (UTC, every two hours on weekdays). The prompt:

> Run the outbound-leads skill's reply check. Read `plugins/vetted/skills/outbound-leads/references/replies.md` and follow "Scheduled check (no workspace)" and sections 1 to 4. Overview URL: <url>. Approval channel: #<name> (<id>). Sender: <name>, mailbox <mailbox>. Approvers: <any | ids>. Lists: Vetted - Interested, Vetted - Not interested. Never wait for input.

4. Offer a test run straight away. The first run posts alerts for every reply so far that has no document yet. If the user wants only new replies alerted, first save documents for the existing replies with `outcome: "pending"` and no `slack`, and the alert step skips them.
