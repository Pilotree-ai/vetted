# Vetted

**One sentence in. An approved, personalised outbound campaign out.**

Vetted is a plugin for [Claude Code](https://claude.com/claude-code). It handles the whole outbound process: finding prospects, checking they really fit, writing a personal first email for each one, getting a person on your team to approve it in Slack, loading it into an Apollo sequence and tracking the results. You stay in control at every step that costs money or sends an email.

```
> UK marketing agencies, up to 20 employees, partner-led, founder or managing
  partner as the contact, 40 leads, offer is a free site audit.
```

Three steps later, 40 people at the right companies each have an email that starts with something true and specific about their business. Each one has been approved by a person on your team and is queued to go out from your own mailbox.

---

## Why it exists

Outbound done properly is slow. Done fast, it is usually generic and risky.

- **Apollo filters are blunt.** They match job titles and headcount bands. They cannot tell whether an agency is run by its co-founders, is independent, or does SEO in-house. So lists are full of poor fits.
- **Credits go on the wrong people.** Enriching first and checking fit second means paying for emails you then throw away.
- **Personal openers take ages.** Reading every prospect's website and writing a real first line by hand does not scale past a handful a day.
- **One bad batch is expensive.** An invented fact, the wrong audience or a burst of volume from a new mailbox can hurt your domain's reputation for months.

Vetted does the slow parts (reading websites, judging fit, writing openers) in parallel, and leaves the decisions to people.

---

## How it works

```
  "UK marketing agencies, partner-led, 40 leads..."
                     │
   1  Brief          Turns your sentence into a campaign brief, asks only about gaps,
                     and reads it back.                                   ◆ you confirm
                     │
   2  Search         Broad pull from Apollo. Skips anyone you've already contacted.   free
                     │
   3  Screen         Reads each company's own website and checks it against your
                     rules: qualify, drop or unclear, always with evidence.            free
                     │
   4  Enrich         Verified work emails for qualifiers only.        ◆ you confirm cost
                     │
   5  Write          One personal opener and subject per person, based on a real
                     fact from their site.                                             free
                     │
   6  Approve        Posts the emails to Slack in groups of 10.     ◆ a person reacts ✅
                     │
   7  Load           Creates contacts and a 4-step Apollo sequence, writes each
                     person's approved email, checks every one was saved. ◆ you switch it on
                     │
   8  Track          Daily summary in Slack: replies, bounces, totals.
```

The ◆ steps are **gates**. The skill stops and waits for you at each one. Nothing is sent without a person approving it in Slack.

---

## What makes it different

**You set the criteria in plain English.** "Partner-led", "independent", "growing", "does B2B only". The skill turns each phrase into a rule it can test on a website, with clear qualify, drop and unclear cases, and shows you the rule before using it. For example:

> **Partner-led**
> Qualify: the site names two or more people who co-founded or jointly run the firm, or it calls itself a partnership.
> Drop: a single founder with staff underneath, or part of a larger group.
> Unclear: the site doesn't say who runs it.

**Every decision has a source.** Each qualify or drop comes with the page URL and the line that supports it. "Unclear" is never guessed. Those leads go to your approver with whatever was found.

**Credits are spent last.** Search and screening are free, so the skill checks fit first and enriches only the companies that pass. It states the exact credit cost and your balance before spending anything.

**Openers are true.** Each first line is based on a real, checkable fact from the prospect's own website, with the URL kept as evidence. The house rules:
- No invented facts or numbers, no flattery, no exclamation marks.
- Subject under 60 characters, and an opt-out line in every email.

**Approval happens where your team already is.** Emails appear in your Slack channel in groups of 10. React ✅ to approve a group, or reply in its thread with names to remove. The skill reads the reactions and replies before it touches Apollo.

**What was approved is what gets sent.** Each person's approved email is saved in Apollo as a per-contact override. The skill reads back what Apollo stored. Anyone whose email wasn't saved exactly is removed before the sequence is switched on, so nobody gets a generic fallback.

**It remembers who you've contacted.** A shared record of every company and person ever enrolled, across every sender and batch, means nobody gets the same cold email twice.

**It works for a team.** Several senders can share one Apollo workspace. The skill asks "which sender?" each run and keeps sequence names, sign-offs and records separate.

**You can stop and pick up later.** Each step saves its output. Come back tomorrow and say "check the Slack approvals for the agency batch", and it carries on from there without repeating anything that costs credits.

---

## Requirements

| | |
|---|---|
| **Claude Code** | Logged in with a Claude account (Pro, Max, Team or Enterprise). The website screening runs as parallel agents, about 2 minutes for 60 companies |
| **Apollo.io** | A **paid plan**: the free plan blocks people search. Lower tiers allow only 2 active sequences, so Professional is recommended. Expect about 1 credit per qualified lead |
| **A sender mailbox** | Connected in the Apollo web app, with your signature, sending limits (50 to 75 a day for a new mailbox) and a sending schedule set up there |
| **Slack** | Any channel you want approvals posted in. You choose it at setup, or the skill can create one for you. The connected Slack user must be a member |

Connect **Apollo** and **Slack** once in claude.ai Settings > Connectors. They're tied to your Claude account, so Claude Code picks them up automatically.

---

## Install

```
/plugin marketplace add Pilotree-ai/vetted
/plugin install vetted@pilotree
```

The skill then shows up as `vetted:outbound-leads`. You don't need to call it by name: just describe the leads you want.

---

## First run

Open Claude Code in the folder you want to keep your campaigns in, and say something like:

```
> start an outbound batch
```

The skill checks your Apollo and Slack connections, then sets itself up in a short dialogue. It looks up your connected mailboxes, your name and your Slack channels and offers them as options, so you mostly just pick:

- which mailbox to send from, and the name to sign off with
- which Slack channel to post approvals in (any channel you like, or a new one it creates)
- the opt-out line that ends every email
- optionally, a second sender and a Slack canvas to track batches in

This is saved once and never asked again. Say "change my outbound config" at any time to update it.

---

## Things you can say

```
> UK B2B SaaS companies, 50 to 500 staff, head of marketing or CMO, 25 leads,
  use my saved free-audit offer
> Independent architecture practices in Manchester, 5 to 30 people, founder as
  contact, 20 leads, offer is a free site audit. Draft the copy for me.
> check the Slack approvals for the agency batch
> load the approved groups into Apollo
> how are my outbound sequences doing?
> add a second sender
> set up the daily outbound report
```

---

## Your workspace

Everything specific to you stays in your own folder, never in the skill:

```
outbound/
  config.md            your senders, Slack channel, voice rules and holds
  offers/              your saved offers: product, terms, prices and email copy
  contacted.csv        every company and person ever enrolled
  campaigns/
    uk-agencies-partner-led/
      brief.md         the confirmed brief
      01-search.csv    Apollo pull and exclusions
      02-screen.json   website screen with evidence
      03-enriched.csv  verified emails
      04-research.json openers, subjects and full emails
      05-slack.json    approval messages and results
      06-load.json     Apollo sequence and what was saved
```

Keep `outbound/` out of git. It contains mailbox addresses, Slack IDs and prospect data. This repo's `.gitignore` already excludes it.

---

## Making it yours

- **Offers and copy.** What you sell, your terms and your prices are yours, so they live in your own `outbound/offers/` folder, never in the skill. Paste a template into your sentence, name a saved offer ("use the agency offer"), or let the skill draft one. Drafted copy is approved in Slack along with the emails, and the skill offers to save it as a reusable offer. An offer file bundles its Apollo filters, drop rules, opener style, four email steps and how to handle replies. See the two examples in [`templates/`](plugins/vetted/skills/outbound-leads/templates/) for the shape.
- **Voice and limits.** Language, banned words, daily send cap, sequence timing and screening depth are all in `outbound/config.md`.
- **Holds.** List companies or people to leave alone until something is checked, and searches skip them.

---

## Good to know

- **It can't sign in for you.** Connectors and mailboxes are set up by you. The skill only checks them, and stops with clear instructions if something is missing.
- **It can't read replies.** Replies land in the sender's inbox. Reports say who replied, not what they said.
- **Strict criteria drop a lot of companies.** To end up with 40 qualified leads, expect to screen 150 or more. The skill sizes the search for you and tells you if it's falling short, instead of quietly loosening your rules.
- **Volume matters.** Sending 60 or more emails on day one from a new mailbox puts your whole domain at risk. The skill warns you and keeps to the daily cap. A second mailbox lets Apollo rotate sends.
- **Built for Claude Code.** It relies on parallel agents and local files.

---

## What's inside

```
plugins/vetted/skills/outbound-leads/
  SKILL.md              the flow, the four gates, and which file to read at each step
  references/           one file per step, loaded only when that step is reached
    preflight.md        connection and plan checks
    setup.md            the first-run config dialogue
    apollo-search.md    brief to Apollo filters, exclusions, enrichment
    qualify-rules.md    website screen: qualify, drop or unclear with evidence
    research-prompt.md  openers, subjects and the self-check
    slack-approval.md   message formats and reading reactions
    apollo-load.md      contacts, sequence, overrides, go-live
    tracking.md         record of who's been emailed, canvas and daily report
    lessons-learned.md  what went wrong before, and the fix
    multi-sender.md     running several senders on one Apollo workspace
  templates/
    config.template.md
    campaign-brief.md
    example-pilot-offer.md   the shape of an offer file: early customers on special terms
    example-free-audit.md    the shape of an offer file: a free audit, no call needed
```

---

Built by [Pilotree](https://pilotree.ai).
