#!/usr/bin/env python3
"""Graph the growth of CS faculty (and departments) over time.

Uses CSrankings publication data (generated-author-info.csv) from a sibling
checkout. Counts, per publication year, the number of unique authors whose
*lifetime* tracked-publication total is at least K (default 5), and also the
number of departments those authors belong to. Produces a dual-axis chart in
the csconferences house style: green bars for faculty (unique authors) with a
blue line for the rough faculty-per-department ratio.

Caveats (see the CSrankings data semantics):
  * CSrankings attributes every paper to the author's *current* department, so
    this is a "total over time," not a true historical department census. For a
    global total this is fine: a faculty move just shifts which department a
    person is counted under.
  * A department/author only appears in a year with >=1 tracked publication.
    "Faculty" here means publishing authors, not an HR roster.
  * The most recent year or two are undercounted (DBLP indexing lag), so the
    series is capped at --end-year (default 2024).
"""

import argparse
import csv
import os
from collections import defaultdict

import matplotlib.pyplot as plt
import seaborn as sns

DEFAULT_CSRANKINGS_DIR = os.path.join(os.path.dirname(__file__), "..", "CSrankings")


def evenly_spaced_items(lst, N):
    """Return N items evenly spaced across lst (mirrors build.py:58)."""
    if N == 1:
        return [lst[len(lst) // 2]]
    if N >= len(lst):
        return lst.copy()
    step = (len(lst) - 1) / (N - 1)
    new_lst = [lst[0]]
    for i in range(1, N - 1):
        new_lst.append(lst[int(i * step)])
    new_lst.append(lst[-1])
    return new_lst


def load(csrankings_dir):
    """Read generated-author-info.csv -> per-author lifetime pubs, active years, dept."""
    path = os.path.join(csrankings_dir, "generated-author-info.csv")
    total_pubs = defaultdict(float)
    active_years = defaultdict(set)
    dept_of = {}
    with open(path, newline="") as f:
        for row in csv.DictReader(f):
            name = row["name"]
            year = int(float(row["year"]))
            total_pubs[name] += float(row["count"])
            active_years[name].add(year)
            # current affiliation is constant per author in this file
            dept_of[name] = row["dept"]
    return total_pubs, active_years, dept_of


def series(total_pubs, active_years, dept_of, min_total_pubs, start_year, end_year):
    """Per-year: count of eligible active authors and the departments they span."""
    eligible = [n for n, t in total_pubs.items() if t >= min_total_pubs]
    authors_by_year = defaultdict(int)
    depts_by_year = defaultdict(set)
    for name in eligible:
        dept = dept_of[name]
        for y in active_years[name]:
            if start_year <= y <= end_year:
                authors_by_year[y] += 1
                depts_by_year[y].add(dept)
    years = sorted(authors_by_year)
    authors = [authors_by_year[y] for y in years]
    depts = [len(depts_by_year[y]) for y in years]
    fac_per_dept = [a / d if d else 0 for a, d in zip(authors, depts)]
    return years, authors, depts, fac_per_dept


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csrankings-dir", default=DEFAULT_CSRANKINGS_DIR,
                    help="path to the CSrankings checkout (default: ../CSrankings)")
    ap.add_argument("--min-total-pubs", type=int, default=5,
                    help="author counts if lifetime tracked pubs >= this (default: 5)")
    ap.add_argument("--start-year", type=int, default=1970)
    ap.add_argument("--end-year", type=int, default=2024,
                    help="cap the series here; later years are DBLP-incomplete (default: 2024)")
    ap.add_argument("--out", default="graphs/faculty_growth",
                    help="output path stem (writes .png and .pdf)")
    args = ap.parse_args()

    total_pubs, active_years, dept_of = load(args.csrankings_dir)
    years, authors, depts, fac_per_dept = series(
        total_pubs, active_years, dept_of,
        args.min_total_pubs, args.start_year, args.end_year)

    # Print the series for sanity-checking.
    print(f"# faculty growth (lifetime pubs >= {args.min_total_pubs}), "
          f"{years[0]}-{years[-1]}")
    print("year\tfaculty\tdepts\tfac/dept")
    for y, a, d, r in zip(years, authors, depts, fac_per_dept):
        print(f"{y}\t{a}\t{d}\t{r:.1f}")

    sns.set_theme()
    fig = plt.figure()
    ax1 = fig.add_subplot()

    ax1.bar(years, authors, color="green", label="Faculty (unique authors)")
    ax1.set_xticks(evenly_spaced_items(years, 5))
    ax1.set_ylabel("Faculty (unique authors)", color="black", fontsize=12)
    ax1.legend(loc="upper left")

    ax2 = ax1.twinx()
    ax2.plot(years, fac_per_dept, color="blue")
    ax2.set_ylim(0, max(fac_per_dept) * 1.15)
    ax2.set_ylabel("Faculty / department", color="blue")
    ax2.tick_params(axis="y", labelcolor="blue")

    plt.title("Growth of CS Faculty Over Time", fontsize=16)

    metadata = {"CreationDate": None, "ModDate": None, "Creator": None,
                "Producer": None, "Author": None, "Version": None}
    plt.savefig(f"{args.out}.pdf", bbox_inches="tight", metadata=metadata)
    plt.savefig(f"{args.out}.png", bbox_inches="tight", metadata=metadata)
    plt.close()
    print(f"\nWrote {args.out}.png and {args.out}.pdf")


if __name__ == "__main__":
    main()
