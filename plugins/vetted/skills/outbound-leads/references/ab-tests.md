# A/B tests

Each batch can test one change to the first email: two versions, alternated across the people in the batch, each person labelled in Apollo with their version. The overview shows which version gets more replies. When one is clearly ahead, Vetted proposes it as the new default at the next batch, and the user confirms in chat. Nothing about a test changes the approval rules: every email is still approved in Slack exactly as it will be sent.

Read this file at intake (Gate 1), at step 5 (writing), at step 6 (Slack), at step 7 (load), in the overview refresh, and whenever the user asks how a test is going.

## What a test is

- **One change only.** By default the **closing ask** of the step 1 email: the sentence or two before the sign-off that asks for something ("Worth 20 minutes?" against "Send me the formats your clients use and I'll send back a one-page outline"). Other allowed changes: the subject line pattern, or the offer framing in one sentence. Never test two things at once, or the result can't say which one mattered.
- **Version A is the current default.** Version B is the challenger. Both are written out in full in the brief and confirmed at Gate 1, and both follow the email voice rules.
- **Test id:** `<campaign short slug>-<what>-<n>`, for example `ukg-ask-1`. It stays the same across batches until the test is decided, so several batches add up to one result.
- **Apollo lists:** `Vetted test <id> A` and `Vetted test <id> B`.

## At intake (Gate 1)

- If the campaign has a running test (a `tests` document on the overview page, `status: "running"`, same campaign), keep running it unchanged. Say so in the read-back: "Test ukg-ask-1 continues: A <n> people, B <n> people so far."
- If the campaign has a decided test, use the winner as the default ending, and offer a new test against it.
- Otherwise, offer a test of the closing ask, with a suggested B. Base the suggestion on evidence where there is some (for example "replies so far came from the email that asked for information, not a call"). The user can say no. No test is fine.
- Add the `## Test` section to the brief (see `templates/campaign-brief.md`).

## Splitting (step 5)

After drops, put the people in the order they will be posted to Slack (qualifiers first, then unclear leads) and alternate A, B, A, B. Both versions then appear in every Slack group, and in both qualifiers and unclear leads, so neither version gets the better leads by accident. Record `"variant": "A"` or `"B"` on each person in `04-research.json`, and use that version's closing ask when building `full_step1`. Everything else in the email stays identical.

If people are removed in Slack, the split can end up uneven. That's fine, as long as no group was skewed on purpose.

## In Slack (step 6)

- Intro message: one line per version, `Test <id>: A "<text>" · B "<text>". Versions alternate, and each email shows its version.`
- Each email gets a `Version: A` or `Version: B` line under its subject.
- An approver may edit or remove any email as usual. If they rewrite a closing ask, that person leaves the test: record `"variant": ""` and leave them off both lists.

## At load (step 7)

1. After the contacts are created, add them to lists with `apollo_labels_add_entity_ids_to_label_names` (`modality: "contacts"`): the A people to `Vetted test <id> A`, the B people to `Vetted test <id> B`. Use this call, not `label_names` on contact creation, which Apollo doesn't reliably keep.
2. Check with `apollo_labels_index` that each list's `cached_count` grew by the number added. Counts can take a minute to update. If one is still short, add the missing contacts again. Adding is idempotent.
3. Create or update the test's document on the overview page (`overview.md`), collection `tests`, document id = test id:

```json
{
  "id": "ukg-ask-1",
  "campaign": "Pilotree UKG payroll conversion",
  "element": "Closing ask of the first email",
  "status": "running",
  "started_at": "<ISO>",
  "batches": ["<batch label>"],
  "variants": [
    {"key": "A", "list": "Vetted test ukg-ask-1 A", "text": "<closing ask A, exactly>", "contact_ids": ["..."]},
    {"key": "B", "list": "Vetted test ukg-ask-1 B", "text": "<closing ask B, exactly>", "contact_ids": ["..."]}
  ],
  "results": {"A": {"emailed": 0, "replied": 0}, "B": {"emailed": 0, "replied": 0}, "updated_at": ""},
  "decision": null
}
```

On a later batch of the same test, append the batch label and the new contact ids. Pass `if_version` on every write to an existing document.

## Results (overview refresh)

In every overview refresh (the daily routine and the page's Refresh button), for every `tests` document with `status: "running"`:

- One `apollo_analytics_sync_report` call covers all tests: `date_range` `{"modality": "all_time"}`, `group_by: ["contact_label_ids"]`, metrics `num_contacts_emailed`, `num_contacts_replied`. Rows are labelled with the list name. Match `Vetted test <id> A` and `B`.
- Update `results` (`emailed`, `replied` per version, `updated_at`). Interested counts aren't stored here: the page works them out from the `replies` collection (👍 marks) and each version's `contact_ids`.

## Reading a result

Compare the versions with `scripts/ab_test.py`, which the page mirrors:

```
python3 scripts/ab_test.py <A emailed> <A replied> <B emailed> <B replied>
```

It prints the chance that B's real reply rate is higher than A's, and a verdict:

| Verdict | When |
|---|---|
| Too early | either version has fewer than 30 people emailed |
| Clearly ahead | one version has at least a 95% chance of being better |
| Leaning | one version has at least an 80% chance |
| No clear difference | anything else |

At typical cold-email reply rates (1 to 5%), a clear result usually needs 100 to 200 people per version, so a test usually runs across several batches. Say this when the user asks why a test isn't decided yet. Never call a winner on fewer than 30 people per version, however lopsided it looks.

## Proposing the winner

At the next intake for the same campaign, or when the user asks how a test is going:

- **Clearly ahead:** "Version B (<text>) is clearly ahead: <r> replies from <n> against <r> from <n>, a <p>% chance it's better. Make it the default closing ask for this batch and the saved offer?" On a clear yes: set version B as the brief's step 1 ending, update the saved offer in `outbound/offers/` if the campaign uses one, set the test document's `status: "decided"` and `decision: {"winner": "B", "decided_at": "<ISO>", "by": "chat"}`, and offer a new test against the winner. On no, keep the test running or stop it, as the user says (`status: "stopped"`).
- **Leaning or no clear difference:** report the numbers and keep the test running in the next batch.
- Never change the default without that yes in chat.

## In the weekly loop

A scheduled run never changes the brief. A running test continues week after week, alternating as above. When a test becomes clearly ahead, the prep phase adds one line to the Go message ("Test ukg-ask-1: B is clearly ahead. Confirm in chat to make it the default.") and keeps running both versions until the user confirms in chat.
