#!/usr/bin/env python3
"""Decide cheaply whether a scheduled reply check has anything to do.

Compares the overview page's saved documents with Apollo's reports and prints
one compact JSON object, so a run never has to read every document into context.
Exits non-zero when it can't be sure, and the run then follows the full check.

  quick_check.py --docs /tmp/replies/in \
      --all-time /tmp/replies/all_time.md --last-7 /tmp/replies/last_7.md
"""
import argparse
import collections
import datetime as dt
import glob
import json
import os
import re
import sys

PROBLEM_TYPES = {"spam_blocked", "hard_bounce"}
# Apollo's report and message counts can differ slightly. Flag sequences just
# under the pause level too, and let the full guard apply the exact rule.
RULE2_MARGIN = 0.9


class Unsure(Exception):
    pass


def report_text(path):
    raw = open(path, encoding="utf-8").read()
    try:
        data = json.loads(raw)
        if isinstance(data, dict) and "summary" in data:
            return data["summary"]
    except ValueError:
        pass
    return raw.replace("\\n", "\n")


def parse_table(text, path):
    """Read a markdown table by column header, never by position."""
    match = re.search(r"Showing first (\d+) of (\d+) rows", text)
    if match and int(match.group(1)) < int(match.group(2)):
        raise Unsure(f"{path}: report truncated ({match.group(0)})")
    lines = [l.strip() for l in text.splitlines() if l.strip().startswith("|")]
    if len(lines) < 2:
        raise Unsure(f"{path}: no table found")
    cells = lambda l: [c.strip() for c in l.strip("|").split("|")]
    headers = [h.lower() for h in cells(lines[0])]
    rows = []
    for line in lines[2:]:
        values = cells(line)
        if len(values) != len(headers):
            raise Unsure(f"{path}: malformed row: {line[:80]}")
        rows.append(dict(zip(headers, values)))
    return headers, rows


def number(row, column, path):
    value = row.get(column, "").replace(",", "")
    if value in ("", "-", "null", "None"):
        return 0
    try:
        return int(float(value))
    except ValueError:
        raise Unsure(f"{path}: {column} is not a number: {value!r}")


def require(headers, columns, path):
    missing = [c for c in columns if c not in headers]
    if missing:
        raise Unsure(f"{path}: missing columns {missing}")


def load_docs(root, collection):
    docs = []
    for path in sorted(glob.glob(os.path.join(root, collection, "*.json"))):
        doc = json.load(open(path, encoding="utf-8"))
        if isinstance(doc, dict) and "id" in doc and isinstance(doc.get("data"), dict):
            doc = doc["data"]
        docs.append(doc)
    return docs


def load_state(root):
    path = os.path.join(root, "guard", "state.json")
    if not os.path.exists(path):
        raise Unsure(f"{path}: guard state not found")
    doc = json.load(open(path, encoding="utf-8"))
    if isinstance(doc, dict) and "id" in doc and isinstance(doc.get("data"), dict):
        doc = doc["data"]
    return doc


def parse_day(value):
    try:
        return dt.date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def check(args):
    today = dt.date.fromisoformat(args.today) if args.today else dt.datetime.now(dt.timezone.utc).date()
    replies = load_docs(args.docs, "replies")
    events = load_docs(args.docs, "guard_events")
    pauses = load_docs(args.docs, "guard_pauses")
    held = load_docs(args.docs, "held")
    state = load_state(args.docs)

    name_col, replied_col, bounced_col, sent_col = (
        "emailer campaign", "num emails replied", "num emails bounced", "num emails sent")
    sequences = {}
    for path in args.all_time:
        headers, rows = parse_table(report_text(path), path)
        require(headers, [name_col, replied_col, bounced_col, sent_col], path)
        for row in rows:
            sequences[row[name_col]] = {
                "replied": number(row, replied_col, path),
                "bounced": number(row, bounced_col, path),
                "sent": number(row, sent_col, path),
            }

    saved_replies = collections.Counter(d.get("sequence_name") for d in replies)
    saved_events = collections.Counter(d.get("sequence_name") for d in events)
    problems = collections.Counter(
        d.get("sequence_name") for d in events if d.get("type") in PROBLEM_TYPES)
    sequence_ids = {d.get("sequence_name"): d.get("sequence_id") for d in events}
    pause_by_name = {d.get("sequence_name"): d for d in pauses}

    new_replies, new_bounces, rule2 = [], [], []
    for name, row in sequences.items():
        if row["replied"] > saved_replies[name]:
            new_replies.append({"sequence": name, "apollo": row["replied"], "saved": saved_replies[name]})
        if row["bounced"] > saved_events[name]:
            new_bounces.append({"sequence": name, "apollo": row["bounced"], "saved": saved_events[name]})
        count = problems[name]
        pause = pause_by_name.get(name)
        if pause and pause.get("status") == "paused":
            continue
        if pause and count - int(pause.get("baseline_problems") or 0) < 2:
            continue
        level = args.warning_pct / 100 * RULE2_MARGIN
        if count >= 2 and row["sent"] and count / row["sent"] >= level:
            rule2.append({"sequence": name, "sequence_id": sequence_ids.get(name),
                          "problems": count, "sent": row["sent"]})

    headers, rows = parse_table(report_text(args.last_7), args.last_7)
    require(headers, [sent_col, bounced_col], args.last_7)
    sent_7d = sum(number(r, sent_col, args.last_7) for r in rows)
    bounced_7d = sum(number(r, bounced_col, args.last_7) for r in rows)
    rate_7d = round(bounced_7d / sent_7d, 4) if sent_7d else 0
    on_hold = bool(state.get("hold_new_loads"))
    rule3 = "none"
    if sent_7d >= args.min_sent:
        if not on_hold and rate_7d * 100 >= args.hold_pct:
            rule3 = "hold"
        elif on_hold and rate_7d * 100 < args.lift_pct:
            rule3 = "lift"

    held_due = []
    for doc in held:
        due = parse_day(doc.get("load_from"))
        if doc.get("status") == "held" and due and due <= today:
            held_due.append(doc.get("label") or doc.get("slug") or "held batch")

    reactions = []
    for doc in replies:
        slack = doc.get("slack") or {}
        if not slack.get("ts"):
            continue
        marked = parse_day(doc.get("marked_at"))
        if doc.get("outcome") == "pending" or (marked and (today - marked).days <= 14):
            reactions.append({"kind": "reply", "channel": slack.get("channel_id"),
                              "ts": slack["ts"], "outcome": doc.get("outcome")})
    for doc in pauses:
        slack = doc.get("slack") or {}
        if doc.get("status") == "paused" and slack.get("ts"):
            reactions.append({"kind": "pause", "channel": slack.get("channel_id"),
                              "ts": slack["ts"], "sequence": doc.get("sequence_name")})

    reasons = [label for label, value in (
        ("new_replies", new_replies), ("new_bounces", new_bounces), ("rule2_check", rule2),
        ("rule3", rule3 != "none"), ("held_due", held_due)) if value]
    return {
        "action_needed": bool(reasons),
        "reasons": reasons,
        "new_replies": new_replies,
        "new_bounces": new_bounces,
        "rule2_check": rule2,
        "rule3": rule3,
        "held_due": held_due,
        "rate_7d": rate_7d,
        "sent_7d": sent_7d,
        "bounced_7d": bounced_7d,
        "hold_new_loads": on_hold,
        "reactions_to_check": reactions,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--docs", required=True, help="folder holding the saved collections")
    parser.add_argument("--all-time", required=True, action="append",
                        help="all-time report by sequence (repeat for filtered batches)")
    parser.add_argument("--last-7", required=True, help="7-day report by mailbox")
    parser.add_argument("--today", help="YYYY-MM-DD, defaults to today in UTC")
    parser.add_argument("--warning-pct", type=float, default=4)
    parser.add_argument("--hold-pct", type=float, default=3)
    parser.add_argument("--lift-pct", type=float, default=2)
    parser.add_argument("--min-sent", type=int, default=100)
    args = parser.parse_args()
    try:
        print(json.dumps(check(args), separators=(",", ":"), ensure_ascii=False))
    except (Unsure, OSError, ValueError) as error:
        print(json.dumps({"action_needed": True, "reasons": ["unsure"], "error": str(error)}))
        sys.exit(2)


if __name__ == "__main__":
    main()
