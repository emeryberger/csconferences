#!/usr/bin/env python3
"""Extract submission deadlines for csconferences.csv venues from a checkout of
https://github.com/ccfddl/ccf-deadlines (MIT license) and write deadlines.csv.

Usage:
  python3 deadlines.py [path/to/ccf-deadlines] [--coverage]

`make deadlines` clones/updates the checkout into .ccfddl/ (git-ignored) and runs this.
Deadlines are converted to UTC. ccf-deadlines is a community-maintained aggregator: each row keeps
the conference's official site (Link) so readers can confirm the deadline there.
"""
import csv, datetime as dt, re, sys
from pathlib import Path

import yaml  # PyYAML

# our Conference name -> ccf-deadlines `dblp` key (only where they differ from conf.lower())
DBLP_ALIAS = {
    "NeurIPS": "nips", "Oakland": "sp", "UsenixSec": "uss", "ATC": "usenix", "EC": "sigecom",
    "FSE": "sigsoft", "ASE": "kbse", "ISMM": "iwmm", "CHI": "chi", "SIGGRAPH": "siggraph",
    "WWW": "www", "EuroCrypt": "eurocrypt", "CRYPTO": "crypto", "VLDB": "vldb", "PODS": "pods",
}
TZ_RE = re.compile(r"^(?:UTC|GMT)\s*([+-]\d{1,2})(?::?(\d{2}))?$", re.I)
NAMED_TZ = {"AOE": -12, "UTC": 0, "GMT": 0, "PST": -8, "PDT": -7, "EST": -5, "EDT": -4, "CET": 1, "CEST": 2, "JST": 9}


def tz_offset(tz):
    tz = (tz or "UTC").strip()
    if tz.upper() in NAMED_TZ:
        return dt.timedelta(hours=NAMED_TZ[tz.upper()])
    m = TZ_RE.match(tz)
    if m:
        h = int(m.group(1)); mins = int(m.group(2) or 0)
        return dt.timedelta(hours=h, minutes=mins if h >= 0 else -mins)
    raise ValueError(f"unknown timezone {tz!r}")


# regional zones whose offset depends on daylight saving time
DST_ZONES = {"PT": "America/Los_Angeles", "ET": "America/New_York", "CT": "America/Chicago", "MT": "America/Denver"}


def to_utc(local, tz):
    if not local or str(local).upper() == "TBD":
        return ""
    t = dt.datetime.strptime(str(local).strip(), "%Y-%m-%d %H:%M:%S")
    zone = (tz or "").strip().upper()
    if zone in DST_ZONES:
        from zoneinfo import ZoneInfo
        return t.replace(tzinfo=ZoneInfo(DST_ZONES[zone])).astimezone(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return (t - tz_offset(tz)).strftime("%Y-%m-%dT%H:%M:%SZ")


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    root = Path(args[0] if args else ".ccfddl")
    ours = sorted({r["Conference"] for r in csv.DictReader(open("csconferences.csv"))})
    entries = {}
    for f in sorted((root / "conference").glob("*/*.yml")):
        for e in yaml.safe_load(f.read_text()) or []:
            entries.setdefault(str(e.get("dblp", "")).lower(), []).append((f, e))
    rows, missing = [], []
    for conf in ours:
        key = DBLP_ALIAS.get(conf, conf.lower())
        found = entries.get(key)
        if not found:
            missing.append(conf); continue
        f, e = found[0]
        for c in e.get("confs", []):
            tz = c.get("timezone", "UTC")
            for i, t in enumerate(c.get("timeline") or []):
                try:
                    dl = to_utc(t.get("deadline"), tz)
                    ab = to_utc(t.get("abstract_deadline"), tz)
                except ValueError as err:
                    print(f"skip {conf} {c.get('year')}: {err}", file=sys.stderr); continue
                if not dl:
                    continue
                rows.append({"Conference": conf, "Year": c.get("year"), "Round": t.get("comment", "") or (f"round {i + 1}" if len(c["timeline"]) > 1 else ""),
                             "Deadline": dl, "AbstractDeadline": ab, "Timezone": tz,
                             "Dates": c.get("date", ""), "Place": c.get("place", ""), "Link": c.get("link", ""),
                             "Source": f"https://github.com/ccfddl/ccf-deadlines/blob/main/{f.relative_to(root).as_posix()}"})
    rows.sort(key=lambda r: (r["Conference"], r["Deadline"]))
    if "--coverage" in sys.argv:
        print(f"{len(ours) - len(missing)} of {len(ours)} conferences matched; missing: {', '.join(missing)}")
        now = dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        upcoming = [r for r in rows if r["Deadline"] >= now]
        print(f"{len(rows)} deadline rows; {len(upcoming)} upcoming; confs with an upcoming deadline: {len({r['Conference'] for r in upcoming})}")
        return
    with open("deadlines.csv", "w", newline="") as out:
        w = csv.DictWriter(out, fieldnames=list(rows[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(rows)
    print(f"wrote deadlines.csv: {len(rows)} rows for {len({r['Conference'] for r in rows})} conferences; not in ccf-deadlines: {', '.join(missing) or 'none'}")


if __name__ == "__main__":
    main()
