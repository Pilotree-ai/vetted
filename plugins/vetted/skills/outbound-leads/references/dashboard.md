# Live campaign dashboard

One private claude.ai page per campaign, created as soon as the brief is confirmed and updated at the end of every step. It shows where the run is, what is waiting on the user, the totals at each step, and every person with their screen evidence, email and status. Read this file at Gate 1, and come back to the "What to write at each step" table after each step.

**The dashboard is a mirror, never the source of truth.** The working files in `outbound/campaigns/<slug>/` are what the run reads and resumes from. Never read a decision (an approval, a removal, a go-live) from the dashboard. Approval still happens only in Slack.

## When to skip it

- `dashboard: off` in config. Skip silently.
- The `Artifact` or `ArtifactData` tool is not available (not signed in with a claude.ai account, or a surface without artifacts). Say once: "Live dashboard isn't available here, carrying on without it." Then carry on.
- Any dashboard call fails during a run. Say so in one line and carry on. A dashboard failure never stops or delays the campaign.

## 1. Create it (right after Gate 1)

The brief gives the dashboard its name, so it is created the moment the brief is confirmed. That is the first thing the run does after the user says yes.

1. Copy `templates/campaign-dashboard.html` to `outbound/campaigns/<slug>/dashboard.html`, replacing `__CAMPAIGN_TITLE__` with the batch label (plain text, no `<` or `&`). The Artifact tool only publishes files under the working directory, so always publish this copy, never the skill's own file.
2. Publish it with the `Artifact` tool:
   - `file_path`: `outbound/campaigns/<slug>/dashboard.html`
   - `icon`: `"chart"`
   - `description`: "Live status of the <batch label> outbound campaign."
   - `capabilities`: `{"db": {"rules": [{"path": "", "read": "view", "write": "admin"}]}}`. Only the owner and editors can write. Anyone it is shared with can only read.
3. Save `outbound/campaigns/<slug>/00-dashboard.json`: `{"url": "<artifact url>", "versions": {}}`.
4. Write the first data (below) and tell the user in one line: "Live dashboard: <url>. It updates after every step."

On a resumed run, read the URL from `00-dashboard.json`. Never create a second dashboard for the same campaign. If the page itself ever needs republishing (for example after a skill update), first read it with `Artifact` `action: "read"` and `url`, then publish the new copy with that `url`. Omit `capabilities` and `icon` on a republish.

## 2. Data model

Three places in the artifact's database. Write with `ArtifactData` `action: "batch"` (up to 50 writes, 1 MiB per call). For large bodies, write the JSON to a file in the campaign folder and pass `file_path` instead of `data`.

### `run/summary` (one document)

```json
{
  "label": "UK agencies, partner-led",
  "slug": "uk-agencies-partner-led",
  "sender_name": "Sam", "sender_mailbox": "sam@acme.com",
  "audience": "UK marketing agencies, 1 to 20 staff, founder or managing partner",
  "offer": "Free site audit, no call needed",
  "target": 40,
  "rules": [{"name": "Partner-led", "qualify": "...", "drop": "...", "unclear": "..."}],
  "stage": "screen",
  "waiting_on": "",
  "counts": {
    "pulled": 0, "excluded": 0, "screened_companies": 0, "qualify": 0, "unclear": 0, "drop": 0,
    "enriched": 0, "emails_found": 0, "written": 0, "write_dropped": 0,
    "posted": 0, "approved": 0, "removed": 0, "enrolled": 0, "sent": 0, "replied": 0, "bounced": 0
  },
  "credits": {"estimate": null, "used": 0, "balance": 0},
  "slack": {"channel_name": "outbound-approvals", "intro_url": ""},
  "sequence": {"name": "", "active": false},
  "updated_at": "2026-11-06T10:42:00Z"
}
```

- `stage` is one of `brief`, `search`, `screen`, `enrich`, `write`, `approve`, `load`, `live`, `done`. Set it to the step that is now running.
- `waiting_on` is the gate the run is stopped at, in plain words, for example "Confirm up to 46 credits for enrichment" or "Tick groups 3 and 4 in #outbound-approvals". Set it when a gate opens and clear it to `""` once the user answers. This is the line the user sees first.
- Leave a count out, or `null`, until its step has run. The page shows `–` for missing numbers.

### `run/activity` (one document)

`{"items": [{"at": "<ISO time>", "text": "Screened 152 companies: 38 fit, 11 unclear, 103 drop"}]}`. Newest first, at most 30 items. Drop the oldest when adding. Use the same one-line report the step already gives the user.

### `people/<apollo_person_id>` (one document per person)

```json
{
  "first_name": "Priya", "last_name": "Shah", "title": "Founding Partner",
  "company": "Hart & Shah", "domain": "hartshah.co.uk",
  "linkedin_url": "", "location": "Bristol, United Kingdom",
  "stage": "posted",
  "drop_reason": "",
  "screen": {"outcome": "qualify", "rules": [{"rule": "Partner-led", "outcome": "qualify", "evidence": "...", "evidence_url": "https://..."}]},
  "email": "priya@hartshah.co.uk", "email_status": "verified", "flags": ["catch-all (warn)"],
  "subject": "...", "body": "<the full step-1 email, exactly as in 04-research.json>",
  "evidence_url": "https://...", "why_fit": "...",
  "slack_group": 1, "approval": "pending", "approved_by": "",
  "apollo_contact_id": "", "override_written": null,
  "sequence_status": "",
  "updated_at": "<ISO time>"
}
```

`stage` is one of:

| Stage | Set when |
|---|---|
| `excluded` | removed at search (ledger, existing sequence, hold, brief exclusion). Put the reason in `drop_reason` |
| `found` | pulled from Apollo, not yet screened |
| `qualify` / `unclear` / `drop` | screen outcome for their company |
| `no_email` | enrichment found no usable email, or the domain did not match |
| `enriched` | verified email found |
| `write_drop` | dropped at research |
| `ready` | email written and self-checked |
| `posted` | posted to Slack, waiting for a tick |
| `approved` / `removed` | ticked in Slack, or removed in the thread |
| `enrolled` | in the Apollo sequence with their personal email saved |
| `not_personalised` | taken out of the sequence because the override did not save |
| `sent` / `replied` / `bounced` / `finished` / `opted_out` | from status checks |

Write only fields that are known. Use the same Apollo person id the working files use as the document id.

## 3. Versions

Every write to a document that already exists must carry its current `if_version`. Keep them in `00-dashboard.json` under `versions`, keyed `"<collection>/<doc_id>"`, and update them from every write result. Creating a document needs no version.

If a write is refused for a version mismatch, or the versions are missing on a resumed run, read the current ones with `ArtifactData` `action: "list"` (`collection: "people"`, `query.limit: 1000`, `out_dir: outbound/campaigns/<slug>/.dashboard-cache`), and `get` for `run/summary` and `run/activity`. Then redo the write. Do not dump the documents into the conversation.

## 4. What to write at each step

At the end of each step, one or more batches: the step's people documents, then `run/summary` (stage, counts, `waiting_on`, `updated_at`) and a new `run/activity` item.

| Step | People | Summary |
|---|---|---|
| After Gate 1 | none | create `run/summary` with the brief fields, `stage: "search"`; create `run/activity` |
| 2 Search | create every pulled person, `found` or `excluded` | `pulled`, `excluded`; `stage: "screen"` |
| 3 Screen | `screen` and `stage` (`qualify`, `unclear`, `drop`) | `screened_companies`, `qualify`, `unclear`, `drop`; `stage: "enrich"`; `waiting_on` the Gate 2 credit question; `credits.estimate`, `credits.balance` |
| Gate 2 answered | none | clear `waiting_on` |
| 4 Enrich | `email`, `email_status`, `flags`, `stage` (`enriched` or `no_email` with reason) | `enriched`, `emails_found`, `credits.used`, `credits.balance`; `stage: "write"` |
| 5 Write | `subject`, `body`, `evidence_url`, `why_fit`, `stage` (`ready` or `write_drop` with reason) | `written`, `write_dropped`; `stage: "approve"` |
| 6 Posted to Slack | `slack_group`, `approval: "pending"`, `stage: "posted"` | `posted`, `slack.channel_name`, `slack.intro_url` (the intro message permalink, if known); `waiting_on` "Tick each group in #<channel>" |
| 6 Approvals read | `approval`, `approved_by`, `stage` (`approved` or `removed`); edited emails get their new `subject`/`body` | `approved`, `removed`; `waiting_on` lists the groups still without a tick, or `""` |
| 7 Load | `apollo_contact_id`, `override_written`, `stage` (`enrolled` or `not_personalised`) | `enrolled`, `sequence.name`; `stage: "load"`; `waiting_on` the go-live question |
| Gate 4 answered | none | `sequence.active: true`, `stage: "live"`, clear `waiting_on` |
| 8 Status check | `stage` and `sequence_status` for anyone whose state changed | `sent`, `replied`, `bounced`; `stage: "done"` once every contact has finished |

The daily routine updates the dashboard too, if `00-dashboard.json` exists and the routine has the `ArtifactData` tool. If not, it skips it. The ledger and Slack summary are what matter there.

## Privacy

The dashboard holds prospects' names, work emails and the emails written to them. It is private when created. If the user wants to share it, suggest sharing it inside their organisation only (for example with the approvers), never by public link. Don't share it on the user's behalf.
