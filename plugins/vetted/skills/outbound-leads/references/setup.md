# Setup: filling in the config

Run this when `outbound/config.md` is missing, still has `TODO` values, or the user asks to change their setup ("add a second sender", "change the approval channel"). It runs after the connection checks in `preflight.md`, because most answers can be looked up from Apollo and Slack instead of typed.

The aim is a short dialogue with sensible options, not a form. Look things up first, offer them as choices, and ask only what cannot be found. Never ask for passwords, API keys or tokens. Connections are made in Settings > Connectors, not here.

## 1. Look things up first

Use results already fetched in preflight where possible.

| Config field | Where to find it |
|---|---|
| sender mailboxes | `apollo_email_accounts_index`: each connected mailbox's email and id |
| sender name | `apollo_users_api_profile`: the user's first name |
| company_name, sending_domain | the mailbox domain (e.g. `acme.com` gives "Acme") |
| approval channel | ask (see below). Use `slack_list_user_channels` to offer the channels the user is already in |
| slack_user_id | `slack_search_users` with the sender's name or email |
| tracker canvas | ask. If the user pastes a canvas link, the ID is the part starting with `F` |

## 2. Ask in a dialogue

Use `AskUserQuestion`. It takes up to 4 questions per call, each with 2 to 4 options, and the user can always pick "Other" and type their own answer. Put the best guess first and mark it "(Recommended)". Use at most two rounds.

Round 1 (core):

1. **Sender mailbox**: "Which mailbox should the emails be sent from?" Options: the connected Apollo mailboxes (up to 4, default first).
2. **Sign-off name**: "What name should emails be signed with?" Options: the Apollo profile first name, the name before @ in the chosen mailbox.
3. **Approval channel**: "Which Slack channel should emails be posted to for approval?" Every team names this differently, so never assume one. Options: up to 3 channels the user is already in that look likely (sales, outbound, leads, prospects, growth), shown as `#name`, plus "Create a new channel". The user can also type any channel name under Other.
   - Typed a name: look it up with `slack_search_channels`. If it exists but the connected user isn't a member, ask them to join it (Claude can only post where they are a member). If it doesn't exist, offer to create it.
   - Create: ask for a name (suggest `#outbound-approvals`) and whether it should be private, then create it with `slack_create_conversation`.
   - Save both the channel name and its ID. The ID is what's used from then on, so renaming the channel later doesn't break anything.
4. **Opt-out line**: "Which opt-out line should end every email?" Options: `If this isn't relevant, reply "no" and I won't email again.` and `Not the right person? Just let me know and I won't follow up.`

Round 2 (only what is still missing):

1. **Second sender**: "Will anyone else send from this setup?" Options: "No, just me", plus "Yes: <mailbox>" for each other connected mailbox. If yes, ask for their sign-off name in the same round.
2. **Tracker canvas**: "Track batches in a Slack canvas?" Options: "Skip for now", "Create a new canvas in #<channel>". Other: paste a canvas link or ID. If they pick create, use `slack_create_canvas` titled "Leads Tracker".
3. **Products**: "What do you sell, in a sentence?" Options: anything found on the company's website homepage (read it once), or "I'll describe it". If the user has a product already in the brief, skip.
4. **Company name**: only if it couldn't be worked out from the domain.

## 3. Save and confirm

- Write the answers into `outbound/config.md`, keeping every other default as it is.
- If `outbound/contacted.csv` does not exist, create it with the header `date,campaign,sender,company,domain,first_name,last_name,email,apollo_contact_id,status`.
- Show a short summary of what was saved, then carry on to intake. Do not make the user restart the run.
