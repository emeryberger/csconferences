#!/usr/bin/env python3
"""Look up each csconferences.csv venue's CORE (ICORE) conference rank and write rankings.csv.

Source: the ICORE conference portal https://portal.core.edu.au/conf-ranks/ (CORE + GII/GRIN/SCIE).
Only the rank letter, edition, CORE title, and a link to the CORE record are stored, with attribution.
Usage: python3 rankings.py [--source ICORE2026]
Run rarely (rankings change every few years); review the output, then commit rankings.csv.
"""
import csv, html, re, subprocess, sys, time

SOURCE = sys.argv[sys.argv.index("--source") + 1] if "--source" in sys.argv else "ICORE2026"
PORTAL = "https://portal.core.edu.au"
# our Conference -> (CORE acronym to search, regex the CORE title must match)
SEARCH = {
    "Oakland": ("SP", r"Security and Privacy"),
    "UsenixSec": ("USENIX-Security", r"USENIX Security"),
    "ATC": ("USENIX", r"Annual Technical"),
    "NeurIPS": ("NeurIPS", r"Neural Information"),
    "EuroCrypt": ("EuroCrypt", r"Cryptographic Techniques|EUROCRYPT"),
    "CRYPTO": ("CRYPTO", r"Cryptology"),
    "EC": ("EC", r"Economics and Computation|Electronic Commerce"),
    "WWW": ("WWW", r"World Wide Web|Web Conference"),
    "SIGGRAPH": ("SIGGRAPH", r"SIGGRAPH|Computer Graphics"),
    "FSE": ("FSE", r"Foundations of Software Engineering"),
    "CC": ("CC", r"Compiler Construction"),
}


def fetch(url):
    return subprocess.run(["curl", "-sL", "-m", "60", "-A", "csconferences-rankings/1.0 (+https://csconferences.org)", url],
                          capture_output=True).stdout.decode("utf-8", "replace")


def rows_for(acronym):
    q = f"{PORTAL}/conf-ranks/?search={acronym}&by=acronym&source={SOURCE}&sort=arank&page=1"
    page = fetch(q)
    out = []
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", page, re.S)[1:]:   # keep the <tr> tag: its onclick has the record link
        cells = re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)
        if len(cells) < 4:
            continue
        clean = [" ".join(html.unescape(re.sub(r"<[^>]+>", " ", c)).split()) for c in cells]
        onclick = re.search(r"/conf-ranks/(\d+)/", tr)
        out.append({"title": clean[0], "acronym": clean[1], "source": clean[2], "rank": clean[3],
                    "link": f"{PORTAL}/conf-ranks/{onclick.group(1)}/" if onclick else q})
    return out


def main():
    ours = sorted({r["Conference"] for r in csv.DictReader(open("csconferences.csv"))})
    result, unmatched = [], []
    for conf in ours:
        acr, title_re = SEARCH.get(conf, (conf, ""))
        cands = [r for r in rows_for(acr) if r["acronym"].upper() == acr.upper() or (title_re and re.search(title_re, r["title"], re.I))]
        if title_re:
            cands = [r for r in cands if re.search(title_re, r["title"], re.I)] or cands
        if cands:
            best = cands[0]
            note = ""
            if best["rank"] not in ("A*", "A", "B", "C") and "/conf-ranks/" in best["link"] and "?" not in best["link"]:
                # not a letter rank (e.g. "National: USA", "unranked: merged"): record the previous edition's rank
                rec = " ".join(html.unescape(re.sub(r"<[^>]+>", " ", fetch(best["link"]))).split())
                prev = re.search(r"Source:\s*CORE2023\s*Rank:\s*([A-Za-z*: ]+?)\s*Field Of Research", rec)
                note = f"CORE2023: {prev.group(1).strip()}" if prev and prev.group(1).strip() != best["rank"] else ""
            result.append({"Conference": conf, "CORE": best["rank"], "CORESource": best["source"], "CORETitle": best["title"],
                           "CORELink": best["link"], "COREAcronym": best["acronym"], "CORENote": note})
        else:
            unmatched.append(conf)
            result.append({"Conference": conf, "CORE": "", "CORESource": SOURCE, "CORETitle": "", "CORELink": "", "COREAcronym": "",
                           "CORENote": "not in the CORE portal"})
        time.sleep(1.0)  # be polite to the portal
    with open("rankings.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(result[0].keys()), lineterminator="\n")
        w.writeheader(); w.writerows(result)
    print(f"wrote rankings.csv ({SOURCE}): {len(ours) - len(unmatched)} of {len(ours)} matched; unmatched: {', '.join(unmatched) or 'none'}")


if __name__ == "__main__":
    main()
