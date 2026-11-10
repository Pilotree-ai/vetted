# Apollo load (step 7, Gate 4)

Load only approved people (approved groups minus removals). The order below matters: the sequence stays off until every approved email is confirmed stored exactly as approved.

## 1. Final checks

- Re-check every approved email against `outbound/contacted.csv`. Another sender may have loaded the same company since this batch started.
- Count active sequences (`apollo_emailer_campaigns_search`). If this batch needs a new sequence and the limit in config is reached, stop and tell the user which sequences are active. They decide which to switch off.
- Mailbox room: if the overview exists (`overview.md`), refresh it and point the user to its "Room for a new sequence" panel with this batch's size and cap. If it shows the batch running more than 2 working days late, say so before enrolling, and suggest a smaller cap or a later start. The other live sequences already use part of the mailbox's daily limit.
- Volume: if the sender mailbox is new or has sent little, and this batch would start more than about 50 people, warn the user. 60+ cold emails on day one from a new mailbox puts the whole sending domain at risk. Suggest a second connected mailbox for rotation, or a lower daily cap.

## 2. Create contacts

`apollo_contacts_bulk_create`, up to 100 per call. For each person:

- `first_name`, `last_name`, `email`, `title`, `organization_name`, `website_url`
- `present_raw_address`: "<City>, United Kingdom" (or the brief's country). Use the person's city from Apollo if known, otherwise `contact_location_default` from config. Without this, Apollo may guess a US time zone and the email waits for US business hours.
- `label_names`: `["<batch_label>"]`

Bulk create updates existing contacts that match by email, and that overwrite cannot be undone. Check the returned list and note each `contact_id`. Report any contacts not matched to Apollo's person or company data in one line. Do not enrich them again.

## 3. Find or create the sequence

Sequence name: `<batch_label> - <sender name>`. Search first with `apollo_emailer_campaigns_search` (`q_name`). If it exists (a later group of the same batch), reuse it and skip to step 4.

Otherwise create it with `apollo_sequences_create`:

- `active: false`. Always create it switched off.
- `emailer_schedule_id`: look up `sending_schedule_name` from config ("Normal Business Hours") with `apollo_emailer_schedules_index`. Ask the user if it is not found.
- `max_emails_per_day`: from config (50).
- `mark_finished_if_reply: true`, `mark_paused_if_ooo: true`.
- `permissions: "team_can_use"`.
- Four `auto_email` steps. Apollo waits are relative to the previous step, so days 0, 3, 7 and 14 become `wait_time` 0, 3, 4 and 7 (`wait_mode: "day"`).
  - Step 1: `new_thread`. Template subject and body are the brief's step-1 template with a plain, neutral opener in place of the personal one. Every enrolled contact gets a per-contact override (below). This template is only a fallback, and step 5 makes sure nobody receives it.
  - Steps 2 to 4: `reply_to_thread` (no subject), bodies from the brief. Merge tags such as `{{first_name}}` do work in these shared templates.
  - `include_signature: true` on every step. The mailbox's Gmail signature is the footer.

Echo only the sequence id, name and a one-line step summary. Then call `apollo_emailer_campaigns_show` to get the step ids. You need step 1's `emailer_step_id`.

## 4. Enrol with step-1 overrides

Get the sender's mailbox id from `apollo_email_accounts_index`. Use the mailbox the brief names, not the default, if they differ.

Show one confirmation summary (Apollo requires it): sender mailbox, sequence name, number of contacts, enrolment status, and that the sequence is still switched off. Wait for a yes. This one confirmation covers every enrolment call for this job.

Call `apollo_emailer_campaigns_add_contact_ids` with:

- `id` and `emailer_campaign_id`: the sequence id
- `contact_ids`: the approved contacts
- `send_email_from_email_account_id`: the sender's mailbox id
- `step_content_overrides`: one entry per contact, with step 1's `emailer_step_id`, the approved `subject`, and `body_html` built from the approved body (each paragraph in `<p>…</p>`, line breaks as `<br>`). Overrides are sent exactly as written. No merge tags. The approved text, nothing added.
- `status`:
  - new sequence (still switched off): `"active"`. Nothing sends until the sequence is switched on.
  - existing sequence that is already live: `"paused"` with `auto_unpause_at` about 2 hours ahead. This gives time to verify the overrides before anything can send.

## 5. Verify the overrides (Gate 4, part 1)

Read `step_content_overrides_result` in the response:

- `written_contact_count` should equal `requested_contact_count`.
- Anyone in `not_written` or `skipped_contact_ids` is either not enrolled or enrolled without their personal email. Remove anyone enrolled but not personalised with `apollo_emailer_campaigns_remove_or_stop_contact_ids` straight away, so they cannot get the fallback. Report who and why (for example `enrollment_criteria_active_in_other_sequence`).
- Spot-check 2 or 3 contacts with `apollo_emailer_campaigns_step_content`. Confirm the stored subject and body match the approved text.

Save to `outbound/campaigns/<slug>/06-load.json`: sequence id, step ids, contact ids, written, removed, reasons.

## 6. Go live (Gate 4, part 2)

Only for a new sequence that is still switched off. Show:

```
Ready to switch on <sequence name>
- Sender: <mailbox>
- Contacts: <n> enrolled, all with their approved step-1 email
- Removed: <list or none>
- Schedule: <schedule>, max <n>/day, steps on days 0, 3, 7, 14
- First emails: next business-hours window in each contact's time zone
Switch it on?
```

On a clear yes, call `apollo_emailer_campaigns_approve` with the sequence id. Never switch it on without that yes.

## 7. Record

- Append every enrolled person to `outbound/contacted.csv` (status `enrolled`), and every removed one with status `removed`.
- Reply in the Slack intro thread with what was loaded and removed.
- Add the batch to the tracker (see `tracking.md`).
- Refresh the outbound overview (`overview.md`) so the new sequence shows there.
- Tell the user the result (see "Finishing a run" in SKILL.md).
