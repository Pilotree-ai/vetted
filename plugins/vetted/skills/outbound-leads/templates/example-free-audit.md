# Example offer: free audit, no call needed

An example of a complete offer file for a low-commitment first email: something free and useful that the prospect can accept just by replying. Copy it to `outbound/offers/<name>.md` and replace everything in `<angle brackets>`.

## Product

<Product name>: <one or two plain sentences on what it does and for whom>.

## Audience

<Who you're targeting, e.g. UK ecommerce and B2B SaaS brands, 50 to 500 staff. Contact is a marketing leader.>

Apollo starting filters (optional):
- Titles: <head of marketing, marketing director, CMO> (strict)
- Location: <United Kingdom>
- Keyword tags: <ecommerce, saas, online retail>
- Employees: <"51,100", "101,200", "201,500">
- Exclude industries: <NAICS codes, e.g. 5418 and 5416 to keep agencies and consultancies out>
- Verified email only

## Offer

A free <one-page audit / check / report> covering <what it shows>. No call needed. **No prices in the first email.**

## Drop rules (in addition to the defaults)

- <e.g. offline-only businesses>
- <e.g. agencies>
- <e.g. companies over 1,000 staff>

## Opener

Optional pattern, if a fixed shape works better for this offer than a free-form opener:

> <e.g. "When someone searches for <their category>, do they find <Brand>? With <real fact from their site>, that's the kind of search you'd want to win.">

If the pattern needs an extra field per person (such as a likely customer question for their category), name it here so the research step writes it, e.g. `buyer_question`.

Don't claim to know a result you haven't checked yet. The free audit is what finds out.

## Step 1 (day 0, new thread, per-contact override)

```
Hi {first},

{opener}

I'm {sender_name} from <company>. <What you do, in one or two sentences.>

I'd like to run a free <audit> on {short_name} for you: <what they get, in one line>.
No call needed, just reply "yes".

{sender_name}

{opt_out_line}
```

## Follow-ups

These are shared templates, so Apollo merge tags such as `{{first_name}}` and `{{company}}` work here.

Step 2 (day 3, reply in thread):

```
Just checking this reached you. If you'd like the free <audit> on {{company}}, reply
"yes" and I'll send it over.
```

Step 3 (day 7, reply in thread):

```
<Why this matters now, in two or three sentences, without hype.>
```

Step 4 (day 14, reply in thread):

```
I'll leave it here. If it's useful later, <where to find you>.
```

## Handling replies

| Reply | What to do |
|---|---|
| "Yes" | <Run the audit and send it within a day> |
| Wants a call | Offer two times |
| "How much?" | <Your pricing answer> |
| "No", or unsubscribe | Thank them if you like. The sequence has already stopped. Don't contact them again |
| Out of office | Apollo pauses that contact automatically |
