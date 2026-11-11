#!/usr/bin/env python3
"""Compare two versions of an email by reply rate.

Usage: python3 ab_test.py <A emailed> <A replied> <B emailed> <B replied>

Each version's reply rate gets a Beta(1 + replied, 1 + emailed - replied)
distribution. The script prints the chance that B's real reply rate is
higher than A's, and a verdict using the thresholds in references/ab-tests.md.
The overview page uses the same method, so both give the same answer.
Standard library only.
"""
import math
import sys

MIN_PER_VERSION = 30
CLEAR = 0.95
LEANING = 0.80
GRID = 4000


def beta_logpdf(x, a, b):
    return (math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b)
            + (a - 1) * math.log(x) + (b - 1) * math.log(1 - x))


def chance_b_beats_a(na, ra, nb, rb):
    """P(rate_B > rate_A), integrating on a grid over (0, 1)."""
    aa, ab = 1 + ra, 1 + na - ra
    ba, bb = 1 + rb, 1 + nb - rb
    h = 1.0 / GRID
    cdf_a = 0.0
    total = 0.0
    for i in range(GRID):
        x = (i + 0.5) * h
        pa = math.exp(beta_logpdf(x, aa, ab)) * h
        pb = math.exp(beta_logpdf(x, ba, bb)) * h
        # B at x beats every A value below x, and half of A's mass at x.
        total += pb * (cdf_a + pa / 2)
        cdf_a += pa
    return min(1.0, max(0.0, total))


def verdict(na, ra, nb, rb):
    if na < MIN_PER_VERSION or nb < MIN_PER_VERSION:
        return "Too early"
    p = chance_b_beats_a(na, ra, nb, rb)
    if p >= CLEAR:
        return "B is clearly ahead"
    if 1 - p >= CLEAR:
        return "A is clearly ahead"
    if p >= LEANING:
        return "Leaning B"
    if 1 - p >= LEANING:
        return "Leaning A"
    return "No clear difference"


def main(argv):
    if len(argv) != 5:
        print(__doc__.strip())
        return 2
    try:
        na, ra, nb, rb = (int(v) for v in argv[1:])
    except ValueError:
        print("All four values must be whole numbers.")
        return 2
    if min(na, ra, nb, rb) < 0 or ra > na or rb > nb:
        print("Replies can't be negative or more than the people emailed.")
        return 2
    p = chance_b_beats_a(na, ra, nb, rb)
    rate = lambda r, n: f"{(r / n * 100):.1f}%" if n else "-"
    print(f"A: {ra} of {na} replied ({rate(ra, na)})")
    print(f"B: {rb} of {nb} replied ({rate(rb, nb)})")
    print(f"Chance B is better: {p * 100:.0f}%")
    print(f"Verdict: {verdict(na, ra, nb, rb)}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
