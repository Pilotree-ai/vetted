# More than one sender

The supported setup is **one Apollo workspace, one Claude account with the Apollo and Slack connectors, and several sender mailboxes**. Each sender has a seat in Apollo and connects their own Gmail there. The skill asks "which sender?" at intake and keeps the streams apart.

## Why this setup

- A Claude account holds one connection per connector. Two different Apollo logins cannot both sit on one claude.ai account.
- Adding the same MCP server twice under different names in Claude Code (`apollo-a`, `apollo-b`) is unverified, and would not cover scheduled routines, which use the claude.ai connectors.
- If a sender wants a fully independent stream (own Apollo workspace, own Slack), they use their own Claude account with their own connectors and their own `outbound/` workspace.

## Keeping streams separate

- **Sender per run.** Never default silently when config lists more than one sender. Ask.
- **Names.** The sequence name, batch label and ledger rows all carry the sender (`<batch_label> - <sender name>`).
- **Copy.** The sign-off name in templates and openers is the sender's, not whoever set up the config.
- **Exclusions.** The ledger is shared, so the same company is never emailed by both senders. If a company is already in the ledger under the other sender, exclude it and say so.
- **Sequence cap.** The active-sequence limit is per Apollo workspace, shared by both senders. Preflight shows it, and both people need to agree on which sequences are live.
- **Slack.** Posts appear as the connected Slack user. That is fine. Approval works with a tick from whoever approves. Mention the sender in the intro message so approvers know whose stream it is.
