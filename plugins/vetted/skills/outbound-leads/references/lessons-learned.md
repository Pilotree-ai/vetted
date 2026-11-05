# Lessons learned

Things that have gone wrong before, and what the skill does about them.

- **Free Apollo plan.** Claude cannot search people on the free plan. Use a paid plan, or search in the Apollo web app and save the people to a list Claude can read.
- **Mailbox limits.** A new mailbox should send 50 to 75 a day at most, with 2 to 3 minutes between emails (set in Apollo, Settings > Mailboxes). The default of about 10 minutes only fits around 20 emails into an afternoon.
- **Sequence limit.** Lower Apollo plans allow only 2 active sequences per workspace, shared by everyone on it. Check before building another.
- **Overrides are sent exactly as written.** Merge tags such as `{{first_name}}` are not filled in inside per-contact overrides, so write the finished text. Shared follow-up templates (steps 2 to 4) do fill merge tags.
- **Time zones.** A contact with no location, or one Apollo guessed as US, waits for US business hours. Set "City, United Kingdom" (or the right country) on every contact.
- **Volume and spam risk.** 60+ emails on day one from a new mailbox risks the whole sending domain. Keep the daily cap, and use a second connected mailbox so Apollo can rotate sends.
- **Catch-all domains.** Marked "catch-all (warn)". Usually deliver, but bounces show there first.
- **Email domain mismatch.** If the email's domain is not the company's website, drop the person. It is usually a parent group or a previous employer. (Batch 2 dropped three agencies for this.)
- **Bot-blocked sites.** Weaker evidence and a weaker opener. Mark it and let the approver decide. Do not fill gaps from memory.
- **Research before credits.** Enriching before screening wasted credits on companies that were then dropped. Search is free, so screen first, then enrich.
- **Strict screens drop a lot.** To end up with 40 qualified leads, screen 150 or more.
- **Slack identity.** Claude's posts appear as the connected Slack user, with "Sent using Claude" underneath. Claude can only post where that user is a member.
- **Replies.** Replies arrive in the sender's Gmail. Claude cannot read reply content through Apollo, so reports only say who replied.
