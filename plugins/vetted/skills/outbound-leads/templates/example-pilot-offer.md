# Example offer: founding customer pilot

An example of a complete offer file. It shows the shape the skill expects: audience, Apollo filters, offer, drop rules, opener, four email steps and reply handling. Copy it to `outbound/offers/<name>.md` and replace everything in `<angle brackets>` with your own product, terms and wording.

Use this shape when you want a few early customers on special terms in exchange for feedback.

## Product

<Product name>: <one or two plain sentences on what it does and for whom>.

## Audience

<Who you're targeting, e.g. UK digital agencies, 2 to 50 staff. Contact is the founder or MD.>

Apollo starting filters (optional, the skill works them out from the brief if left out):
- Titles: <founder, managing director, CEO, co-founder> (strict: `include_similar_titles: false`)
- Location: <United Kingdom> (person and company)
- Keyword tags: <"seo", "digital agency">
- Employees: <"1,10", "11,20", "21,50">
- Verified email only

## Offer

- <What they get free, and for how long>
- <The founding terms afterwards, e.g. a locked price for 12 months>
- In return: <what you ask for, e.g. feedback every two weeks and permission to write a case study>

## Drop rules (in addition to the defaults)

- <A reason a company is a poor fit for this offer, e.g. they already sell a competing product>

## Opener

Based on a real fact from their own site, linking it to <the problem your product solves for them>.

## Step 1 (day 0, new thread, per-contact override)

Subject and first paragraph are personal. Placeholders in `{braces}` are filled in per person by the skill.

```
Hi {first},

{opener}

I'm {sender_name} from <company>. <What the product does, in two or three sentences.
Be concrete about what it measures or changes.>

We're taking on a few founding customers. <The pilot terms in one or two sentences.>
In return, we'd ask for <what you ask for>.

Worth 15 minutes to see it on <something specific to them>?

{sender_name}

{opt_out_line}
```

## Step 2 (day 3, reply in thread)

```
<A lower-effort alternative to a call, e.g. a free sample or check they can say yes to
by replying.>
```

## Step 3 (day 7, reply in thread)

```
<Useful context they might be wondering about, e.g. how pricing works after the pilot,
or what a typical result looks like.>
```

## Step 4 (day 14, reply in thread)

```
I'll leave it here. If <the problem> comes up later, <where to find you>.
```

## Handling replies

| Reply | What to do |
|---|---|
| "Yes", or asks for the sample | <Your next step, and how quickly> |
| Wants a call | Offer two times |
| "How much?" | <Your pricing answer> |
| "No", or unsubscribe | Thank them if you like. The sequence has already stopped. Don't contact them again |
| Out of office | Apollo pauses that contact automatically |
