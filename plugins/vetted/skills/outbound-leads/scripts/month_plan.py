#!/usr/bin/env python3
"""Plan the rest of an Apollo credit cycle against credits and mailbox capacity.

Usage:
  python3 month_plan.py --credits-left 2457 --credit-limit 3040 \
      --cycle-end 2026-12-03T14:24:31Z --daily-limit 250 [options]

Options:
  --per-lead 1.6          credits per approved lead (default 1.5, flagged as a guess)
  --overview FILE         overview/current JSON (sequences with steps[].active), so the
                          plan knows what the live sequences will already send
  --sent-today N          emails the mailbox(es) already sent today
  --waits 0,3,4,7         step waits in days (default 0,3,4,7: emails on days 0, 3, 7, 14)
  --tz Europe/London      market time zone (default Europe/London)
  --today YYYY-MM-DD      plan from this date (default: today in --tz)
  --reserve 50            credits kept back for re-checks and misses
  --ahead-days 10         enrich ahead only in the last N calendar days of the cycle
  --ahead-weeks 2         enrich ahead at most this many weeks of next cycle's sending
  --json                  print JSON instead of text

The method matches the overview page (references/credit-plan.md): one batch a week, launched
on Mondays. A new person gets the emails whose day offset falls in the launch week, then one
email in each later week. Each week's new leads are the free sends left after the live
sequences and earlier planned batches, at most a steady 5 x daily limit / emails per person,
and at most what the credits pay for. Credits still left after the reserve go to enriching
ahead for the next cycle. Standard library only.
"""
import argparse
import json
import math
import sys
from datetime import date, datetime, timedelta, timezone

try:
    from zoneinfo import ZoneInfo
except ImportError:  # Python < 3.9
    ZoneInfo = None


# ---- dates (same helpers as the page) ----
def parse_key(k):
    return date.fromisoformat(k)


def add_days(k, n):
    return (parse_key(k) + timedelta(days=n)).isoformat()


def is_weekday(k):
    return parse_key(k).weekday() < 5


def next_weekday(k):
    while not is_weekday(k):
        k = add_days(k, 1)
    return k


def local_key(iso, tz):
    if not iso:
        return None
    try:
        dt = datetime.fromisoformat(str(iso).replace("Z", "+00:00"))
    except ValueError:
        return None
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    if ZoneInfo:
        try:
            dt = dt.astimezone(ZoneInfo(tz))
        except Exception:
            dt = dt.astimezone(timezone.utc)
    return dt.date().isoformat()


def sending_days(start, n):
    out, k = [], next_weekday(start)
    while len(out) < n:
        out.append(k)
        k = next_weekday(add_days(k, 1))
    return out


def index_for(days, k):
    for i, d in enumerate(days):
        if d >= k:
            return i
    return len(days)


def offsets(waits):
    d, out = 0, []
    for w in waits:
        d += int(w or 0)
        out.append(d)
    return out


# ---- forecast (port of the page's simulate/existingPlan) ----
def simulate(seqs, days, limits):
    H = len(days)
    total = [0] * H
    queues = [[dict(p) for p in s["pending"]] for s in seqs]
    for d in range(H):
        room = limits[d] if isinstance(limits, list) else limits
        for i, s in enumerate(seqs):
            q = sorted(queues[i], key=lambda it: (it["day"], -it["step"]))
            can = max(0, min(s["cap"], room))
            sent = 0
            for it in list(q):
                if sent >= can:
                    break
                if it["day"] > d or it["n"] <= 0:
                    continue
                take = min(it["n"], can - sent)
                it["n"] -= take
                sent += take
                nx = it["step"] + 1
                if nx < len(s["waits"]):
                    di = index_for(days, add_days(days[d], max(1, int(s["waits"][nx] or 0))))
                    if di < H:
                        for x in q:
                            if x["day"] == di and x["step"] == nx:
                                x["n"] += take
                                break
                        else:
                            q.append({"day": di, "step": nx, "n": take})
            queues[i] = [x for x in q if x["n"] > 0]
            total[d] += sent
            room -= sent
    return total


def existing_plan(seqs, days, tz):
    live = [s for s in seqs if s and s.get("active") and not s.get("archived")]
    live.sort(key=lambda s: str(s.get("created_at", "")))
    out = []
    for s in live:
        steps = sorted(s.get("steps") or [], key=lambda x: x.get("position") or 0)
        waits = [int(x.get("wait") or 0) for x in steps]
        offs = offsets(waits)
        created = local_key(s.get("created_at"), tz) or days[0]
        pending = []
        for k, x in enumerate(steps):
            n = int(x.get("active") or 0)
            if n <= 0:
                continue
            due = days[0] if k == 0 else add_days(created, offs[k])
            pending.append({"day": index_for(days, max(due, days[0])), "step": k, "n": n})
        out.append({"cap": max(1, int(s.get("daily_cap") or 50)), "waits": waits, "pending": pending})
    return out


# ---- the plan ----
def make_plan(a):
    tz = a.tz
    today = a.today or (datetime.now(ZoneInfo(tz)) if ZoneInfo else datetime.utcnow()).date().isoformat()
    end_key = local_key(a.cycle_end, tz)
    if not end_key:
        raise SystemExit("--cycle-end must be an ISO date or datetime")
    waits = [int(w) for w in a.waits.split(",")]
    per_person = len(waits)
    week_off = [o // 7 for o in offsets(waits)]
    launch_cost = max(1, sum(1 for w in week_off if w == 0))
    limit = a.daily_limit
    per_lead = round(min(3.0, max(1.0, a.per_lead)), 1) if a.per_lead else 1.5
    guessed = not a.per_lead

    days = sending_days(today, 60)
    limits = [max(0, limit - a.sent_today) if (i == 0 and days[0] == today) else limit for i in range(len(days))]
    seqs = []
    if a.overview:
        with open(a.overview) as f:
            seqs = json.load(f).get("sequences") or []
    base = simulate(existing_plan(seqs, days, tz), days, limits) if seqs else [0] * len(days)
    used = list(base)
    if days[0] == today:
        used[0] += a.sent_today

    weeks = []
    for i, k in enumerate(days):
        if k > end_key:
            break
        monday = add_days(k, -parse_key(k).weekday())
        if not weeks or weeks[-1]["week_of"] != monday:
            weeks.append({"week_of": monday, "days": 0, "free": 0, "launch": k == monday})
        weeks[-1]["days"] += 1
        weeks[-1]["free"] += max(0, limit - used[i])

    steady = (5 * limit) // per_person
    credits = a.credits_left
    binding = "mailbox"
    N = []
    for wi, w in enumerate(weeks):
        if not w["launch"]:
            w.update(new_leads=0, credits=0, note="no new batch: batches start on Mondays")
            N.append(0)
            continue
        carry = sum(N[wi - wo] for wo in week_off if wo > 0 and wi - wo >= 0)
        n = max(0, (w["free"] - carry) // launch_cost)
        n = min(n, steady)
        by_credit = int(credits // per_lead) if per_lead else n
        if by_credit < n:
            n, binding = by_credit, "credits"
        c = math.ceil(n * per_lead)
        credits -= c
        N.append(n)
        w.update(new_leads=n, credits=c, note=(f"{w['days']} sending days before the reset" if w["days"] < 5 else ""))

    regular_leads = sum(N)
    regular_credits = sum(w["credits"] for w in weeks)
    spare = a.credits_left - regular_credits - a.reserve

    ahead = {"leads": 0, "credits": 0, "from": None, "to": None, "load_from": None, "reason": ""}
    first_load = end_key
    while parse_key(first_load).weekday() != 0:
        first_load = add_days(first_load, 1)
    if binding == "credits":
        ahead["reason"] = "Credits run out before the mailbox does, so nothing is left to enrich ahead."
    elif spare < per_lead:
        ahead["reason"] = "The weekly batches use the credits, so there's nothing to enrich ahead."
    else:
        leads = min(int(spare // per_lead), a.ahead_weeks * steady)
        ahead.update(leads=leads, credits=math.ceil(leads * per_lead),
                     **{"from": max(today, add_days(end_key, -a.ahead_days)), "to": add_days(end_key, -1),
                        "load_from": first_load})
        if leads < int(spare // per_lead):
            ahead["reason"] = (f"Capped at {a.ahead_weeks} weeks of next cycle's sending; "
                               f"about {spare - ahead['credits']:,} credits would still expire. "
                               "Another mailbox is the way to use those.")

    expiring = max(0, a.credits_left - regular_credits - ahead["credits"])
    return {
        "today": today, "cycle_end": end_key, "credits_left": a.credits_left, "credit_limit": a.credit_limit,
        "daily_limit": limit, "per_lead": per_lead, "per_lead_is_guess": guessed,
        "emails_per_person": per_person, "steady_weekly_leads": steady, "binding": binding,
        "weeks": weeks, "regular": {"leads": regular_leads, "credits": regular_credits},
        "reserve": a.reserve, "enrich_ahead": ahead, "expiring": expiring,
        "full_month": {"leads": round(steady * 4.3), "credits": math.ceil(round(steady * 4.3) * per_lead)},
    }


def fmt_day(k):
    return parse_key(k).strftime("%a %-d %b") if sys.platform != "win32" else parse_key(k).strftime("%a %d %b")


def print_text(p):
    print(f"Credit cycle ends {fmt_day(p['cycle_end'])}: {p['credits_left']:,} credits left"
          + (f" of {p['credit_limit']:,}" if p["credit_limit"] else "")
          + f". Mailbox limit {p['daily_limit']:,} a day. About {p['per_lead']} credits per approved lead"
          + (" (a guess: no history yet)." if p["per_lead_is_guess"] else "."))
    print()
    print(f"{'Week of':<12}{'Free sends':>11}{'New leads':>11}{'Credits':>9}  Note")
    for w in p["weeks"]:
        print(f"{fmt_day(w['week_of']):<12}{w['free']:>11,}{w['new_leads']:>11,}{w['credits']:>9,}  {w['note']}")
    r = p["regular"]
    print(f"{'Weekly batches':<12}{'':>11}{r['leads']:>11,}{r['credits']:>9,}")
    print()
    a = p["enrich_ahead"]
    if a["leads"]:
        print(f"Enrich ahead: {a['leads']:,} leads (~{a['credits']:,} credits) between {fmt_day(a['from'])} and "
              f"{fmt_day(a['to'])}, held and loaded from {fmt_day(a['load_from'])}.")
    if a["reason"]:
        print(a["reason"])
    print(f"Binding limit: {p['binding']}. Reserve: {p['reserve']} credits. "
          f"Expiring at the reset: about {p['expiring']:,} credits.")
    fm = p["full_month"]
    print(f"A full month at this pace: about {p['steady_weekly_leads']:,} leads a week, {fm['leads']:,} a month, "
          f"~{fm['credits']:,} credits.")


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--credits-left", type=int, required=True)
    ap.add_argument("--credit-limit", type=int, default=0)
    ap.add_argument("--cycle-end", required=True)
    ap.add_argument("--daily-limit", type=int, required=True)
    ap.add_argument("--per-lead", type=float, default=0)
    ap.add_argument("--overview")
    ap.add_argument("--sent-today", type=int, default=0)
    ap.add_argument("--waits", default="0,3,4,7")
    ap.add_argument("--tz", default="Europe/London")
    ap.add_argument("--today")
    ap.add_argument("--reserve", type=int, default=50)
    ap.add_argument("--ahead-days", type=int, default=10)
    ap.add_argument("--ahead-weeks", type=int, default=2)
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args(argv[1:])
    if a.credits_left < 0 or a.daily_limit <= 0:
        print("Credits can't be negative and the daily limit must be above 0.")
        return 2
    p = make_plan(a)
    if a.json:
        print(json.dumps(p, indent=1))
    else:
        print_text(p)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
