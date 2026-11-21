#!/usr/bin/env python3
"""Build rankings.csv: per-venue ranks from three widely recognized authorities.

  CORE  - ICORE conference portal (CORE with GII-GRIN-SCIE), https://portal.core.edu.au/conf-ranks/
  CCF   - China Computer Federation recommended venues (7th edition, 2026), https://www.ccf.org.cn/Academic_Evaluation/
  GSM   - Google Scholar Metrics h5-index / h5-median, from the robots.txt-allowed "top venues" pages
          (https://scholar.google.com/citations?view_op=top_venues); a venue gets a value only if it is in
          the top 20 of one of the computing subcategories (Scholar's venue search is disallowed by robots.txt).

Only facts are stored (rank letters / h-index numbers, edition, the authority's venue title, and a link back),
with attribution on the site. Usage: python3 rankings.py [--core] [--ccf] [--gsm]   (default: all)
Run rarely (editions change every 1-3 years); review the output, then commit rankings.csv.
"""
import csv, html, re, subprocess, sys, time
from pathlib import Path

UA = "csconferences-rankings/1.0 (+https://csconferences.org)"
OUT = Path("rankings.csv")


def fetch(url):
    return subprocess.run(["curl", "-sL", "-m", "60", "-A", UA, url], capture_output=True).stdout.decode("utf-8", "replace")


def clean(s):
    return " ".join(html.unescape(re.sub(r"<[^>]+>", " ", s)).split())


# ---------------- CORE ----------------
CORE_SOURCE = "ICORE2026"
CORE_PORTAL = "https://portal.core.edu.au"
CORE_SEARCH = {  # our Conference -> (CORE acronym to search, regex the CORE title must match)
    "Oakland": ("SP", r"Security and Privacy"), "UsenixSec": ("USENIX-Security", r"USENIX Security"),
    "ATC": ("USENIX", r"Annual Technical"), "NeurIPS": ("NeurIPS", r"Neural Information"),
    "EuroCrypt": ("EuroCrypt", r"Cryptographic Techniques|EUROCRYPT"), "CRYPTO": ("CRYPTO", r"Cryptology"),
    "EC": ("EC", r"Economics and Computation|Electronic Commerce"), "WWW": ("WWW", r"World Wide Web|Web Conference"),
    "SIGGRAPH": ("SIGGRAPH", r"SIGGRAPH|Computer Graphics"), "FSE": ("FSE", r"Foundations of Software Engineering"),
    "CC": ("CC", r"Compiler Construction"),
}


def core_rows(acronym):
    q = f"{CORE_PORTAL}/conf-ranks/?search={acronym}&by=acronym&source={CORE_SOURCE}&sort=arank&page=1"
    out = []
    for tr in re.findall(r"<tr[^>]*>.*?</tr>", fetch(q), re.S)[1:]:   # keep the <tr> tag: its onclick has the record link
        cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
        if len(cells) < 4:
            continue
        rec = re.search(r"/conf-ranks/(\d+)/", tr)
        out.append({"title": cells[0], "acronym": cells[1], "source": cells[2], "rank": cells[3],
                    "link": f"{CORE_PORTAL}/conf-ranks/{rec.group(1)}/" if rec else q})
    return out


def core(conf):
    acr, title_re = CORE_SEARCH.get(conf, (conf, ""))
    rows = core_rows(acr)
    cands = [r for r in rows if r["acronym"].upper() == acr.upper() or (title_re and re.search(title_re, r["title"], re.I))]
    if title_re:
        cands = [r for r in cands if re.search(title_re, r["title"], re.I)] or cands
    if not cands:
        return {"CORE": "", "CORESource": CORE_SOURCE, "CORETitle": "", "CORELink": "", "CORENote": "not in the CORE portal"}
    best, note = cands[0], ""
    if best["rank"] not in ("A*", "A", "B", "C") and "?" not in best["link"]:
        prev = re.search(r"Source:\s*CORE2023\s*Rank:\s*([A-Za-z*: ]+?)\s*Field Of Research", clean(fetch(best["link"])))
        note = f"CORE2023: {prev.group(1).strip()}" if prev and prev.group(1).strip() != best["rank"] else ""
    return {"CORE": best["rank"], "CORESource": best["source"], "CORETitle": best["title"], "CORELink": best["link"], "CORENote": note}


# ---------------- CCF ----------------
CCF_EDITION = "CCF 2026 (7th ed.)"
CCF_BASE = "https://www.ccf.org.cn/Academic_Evaluation/"
CCF_CATS = ["ARCH_DCP_SS", "CN", "NIS", "TCSE_SS_PDL", "DM_CS", "TCS", "CGAndMT", "AI", "HCIAndPC", "Cross_Compre_Emerging"]
DBLP_KEY = {  # our Conference -> DBLP conf directory, where it is not conf.lower()
    "NeurIPS": "nips", "Oakland": "sp", "UsenixSec": "uss", "ATC": "usenix", "EC": "sigecom", "FSE": "sigsoft",
    "ASE": "kbse", "ISMM": "iwmm", "EuroCrypt": "eurocrypt", "CHI": "chi", "WWW": "www",
}


def ccf_all():
    """-> list of dicts (cat, kind 'conf'|'journal', rank, acronym, title, dblp_dir, page)."""
    out = []
    for cat in CCF_CATS:
        page = CCF_BASE + cat + "/"
        raw = fetch(page)
        if "sname" not in raw:
            print(f"  CCF {cat}: no entries (status/page changed?)", file=sys.stderr)
            continue
        kind, prev_end, n0 = "journal", 0, len(out)
        for m in re.finditer(r"<ul[^>]*>(.*?)</ul>", raw, re.S):
            # section headings ("...国际学术刊物" = journals, "...国际学术会议" = conferences) appear only before the A list,
            # so carry the kind forward; the A/B/C heading sits just before each list
            between = clean(raw[prev_end:m.start()])
            prev_end = m.end()
            if "国际学术会议" in between:
                kind = "conf"
            elif "国际学术刊物" in between or "国际学术期刊" in between:
                kind = "journal"
            rk = re.findall(r"([ABC])\s*类", between)
            if not rk:
                continue
            for li in re.findall(r"<li[^>]*>(.*?)</li>", m.group(1), re.S):
                sname = re.search(r'class="sname"[^>]*>(.*?)</div>', li, re.S)
                cells = [clean(c) for c in re.findall(r"<div[^>]*>(.*?)</div>", li, re.S)]
                link = re.search(r'href="([^"]+)"', li)
                d = re.search(r"/db/(?:conf|journals)/([^/]+)/", link.group(1)) if link else None
                if sname and cells and clean(sname.group(1)) != "刊物名称":
                    out.append({"cat": cat, "kind": kind, "rank": rk[-1], "acronym": clean(sname.group(1)),
                                "title": cells[2] if len(cells) > 2 else "", "dblp": d.group(1).lower() if d else "", "page": page})
        got = out[n0:]
        print(f"  CCF {cat}: {sum(e['kind'] == 'journal' for e in got)} journals, {sum(e['kind'] == 'conf' for e in got)} conferences", file=sys.stderr)
        time.sleep(1.0)
    return out


def ccf(conf, entries):
    key = DBLP_KEY.get(conf, conf.lower())
    confs = [e for e in entries if e["kind"] == "conf"]
    hit = next((e for e in confs if e["dblp"] == key), None) or next((e for e in confs if e["acronym"].upper() == conf.upper()), None)
    if not hit:
        return {"CCF": "", "CCFEdition": CCF_EDITION, "CCFTitle": "", "CCFLink": "", "CCFNote": "not in the CCF list"}
    return {"CCF": hit["rank"], "CCFEdition": CCF_EDITION, "CCFTitle": hit["title"], "CCFLink": hit["page"], "CCFNote": ""}


# ---------------- Google Scholar Metrics ----------------
GSM_SUBCATS = ["eng", "eng_artificialintelligence", "eng_computationallinguistics", "eng_computergraphics", "eng_computerhardwaredesign",
               "eng_computernetworkswirelesscommunication", "eng_computersecuritycryptography", "eng_computervisionpatternrecognition",
               "eng_computingsystems", "eng_databasesinformationsystems", "eng_datamininganalysis", "eng_gametheorydecisionscience",
               "eng_humancomputerinteraction", "eng_multimedia", "eng_robotics", "eng_softwaresystems", "eng_theoreticalcomputerscience"]
GSM_URL = "https://scholar.google.com/citations?view_op=top_venues&hl=en&vq={}"
# our Conference -> (exact Scholar venue name, note); shared journal-level entries are flagged
GSM_NAME = {
    "AAAI": "AAAI Conference on Artificial Intelligence", "ACL": "Meeting of the Association for Computational Linguistics (ACL)",
    "ASE": "IEEE/ACM International Conference on Automated Software Engineering (ASE)",
    "ASPLOS": "International Conference on Architectural Support for Programming Languages and Operating Systems (ASPLOS)",
    "ATC": "USENIX Annual Technical Conference", "CAV": "International Conference on Computer Aided Verification (CAV)",
    "CCS": "ACM Symposium on Computer and Communications Security", "CHI": "Computer Human Interaction (CHI)",
    "CRYPTO": "International Cryptology Conference (CRYPTO)", "CVPR": "IEEE/CVF Conference on Computer Vision and Pattern Recognition",
    "EC": "ACM Conference on Electronic Commerce", "ECCV": "European Conference on Computer Vision",
    "EMNLP": "Conference on Empirical Methods in Natural Language Processing (EMNLP)",
    "EuroCrypt": "International Conference on Theory and Applications of Cryptographic Techniques (EUROCRYPT)",
    "EuroSys": "ACM European Conference on Computer Systems", "FOCS": "IEEE Symposium on Foundations of Computer Science (FOCS)",
    "FSE": "ACM SIGSOFT International Symposium on Foundations of Software Engineering",
    "HPCA": "IEEE International Symposium on High Performance Computer Architecture",
    "ICCV": "IEEE/CVF International Conference on Computer Vision", "ICDE": "International Conference on Data Engineering",
    "ICLR": "International Conference on Learning Representations", "ICML": "International Conference on Machine Learning",
    "ICRA": "IEEE International Conference on Robotics and Automation", "ICSE": "ACM/IEEE International Conference on Software Engineering",
    "IJCAI": "International Joint Conference on Artificial Intelligence (IJCAI)", "IROS": "IEEE/RSJ International Conference on Intelligent Robots and Systems",
    "ISCA": "International Symposium on Computer Architecture (ISCA)", "ISSTA": "International Symposium on Software Testing and Analysis",
    "LICS": "IEEE Symposium on Logic in Computer Science", "MICRO": "IEEE/ACM International Symposium on Microarchitecture",
    "NDSS": "Network and Distributed System Security Symposium (NDSS)", "NSDI": "USENIX Symposium on Networked Systems Design and Implementation",
    "NeurIPS": "Neural Information Processing Systems", "OSDI": "Symposium on Operating Systems Design and Implementation (OSDI)",
    "Oakland": "IEEE Symposium on Security and Privacy",
    "PLDI": "ACM SIGPLAN Conference on Programming Language Design and Implementation (PLDI)",
    "POPL": "Proceedings of the ACM on Programming Languages", "ICFP": "Proceedings of the ACM on Programming Languages",
    "OOPSLA": "Proceedings of the ACM on Programming Languages",
    "SIGGRAPH": "ACM Transactions on Graphics (TOG)",
    "SIGIR": "ACM SIGIR Conference on Research and Development in Information Retrieval",
    "SIGMOD": "ACM SIGMOD International Conference on Management of Data", "SODA": "ACM SIAM Symposium on Discrete Algorithms",
    "SOSP": "Symposium on Operating Systems Principles", "STOC": "ACM Symposium on Theory of Computing",
    "UIST": "ACM Symposium on User Interface Software and Technology", "UsenixSec": "USENIX Security Symposium",
    "VLDB": "International Conference on Very Large Databases", "WINE": "International Conference on Web and Internet Economics",
    "WSDM": "ACM International Conference on Web Search and Data Mining", "WWW": "International World Wide Web Conferences (WWW)",
}
GSM_SHARED = {"POPL": "PACMPL (shared by POPL, PLDI, ICFP, OOPSLA)", "ICFP": "PACMPL (shared by POPL, PLDI, ICFP, OOPSLA)",
              "OOPSLA": "PACMPL (shared by POPL, PLDI, ICFP, OOPSLA)", "SIGGRAPH": "ACM Transactions on Graphics (also publishes SIGGRAPH Asia papers)"}


def gsm_all():
    rows, window = {}, ""
    for sc in GSM_SUBCATS:
        raw = fetch(GSM_URL.format(sc))
        if re.search(r"captcha|unusual traffic", raw, re.I):
            sys.exit("Google Scholar asked for a CAPTCHA; stopping (try again later).")
        w = re.search(r"articles published in (\d{4})-(\d{4})", clean(raw))
        window = window or (f"{w.group(1)}–{w.group(2)}" if w else "")
        for tr in re.findall(r"<tr[^>]*>(.*?)</tr>", raw, re.S):
            cells = [clean(c) for c in re.findall(r"<td[^>]*>(.*?)</td>", tr, re.S)]
            if len(cells) >= 4 and cells[0].rstrip(".").isdigit() and cells[2].isdigit():
                rows.setdefault(cells[1], {"h5": cells[2], "h5median": cells[3], "subcat": sc})
        time.sleep(3)   # polite
    return rows, window


def gsm(conf, rows, window):
    name = GSM_NAME.get(conf)
    edition = f"Google Scholar Metrics ({window} articles)" if window else "Google Scholar Metrics"
    if not name or name not in rows:
        return {"H5": "", "H5Median": "", "H5Venue": "", "H5Link": "", "H5Edition": edition,
                "H5Note": "not in the top 20 of any Google Scholar computing subcategory"}
    r = rows[name]
    return {"H5": r["h5"], "H5Median": r["h5median"], "H5Venue": name, "H5Link": GSM_URL.format(r["subcat"]), "H5Edition": edition,
            "H5Note": GSM_SHARED.get(conf, "")}


def main():
    want = {a.lstrip("-") for a in sys.argv[1:]} or {"core", "ccf", "gsm"}
    ours = sorted({r["Conference"] for r in csv.DictReader(open("csconferences.csv"))})
    old = {r["Conference"]: r for r in csv.DictReader(open(OUT))} if OUT.exists() else {}
    table = {c: dict(old.get(c, {"Conference": c})) for c in ours}
    if "core" in want:
        for c in ours:
            table[c].update(core(c)); time.sleep(1.0)
        print("CORE:", sum(1 for c in ours if table[c]["CORE"]), "of", len(ours), "listed")
    if "ccf" in want:
        entries = ccf_all()
        print(f"CCF: parsed {len(entries)} entries ({sum(e['kind'] == 'conf' for e in entries)} conferences)")
        for c in ours:
            table[c].update(ccf(c, entries))
        print("CCF:", sum(1 for c in ours if table[c]["CCF"]), "of", len(ours), "listed; missing:",
              ", ".join(c for c in ours if not table[c]["CCF"]))
    if "gsm" in want:
        rows, window = gsm_all()
        for c in ours:
            table[c].update(gsm(c, rows, window))
        print(f"GSM ({window}):", sum(1 for c in ours if table[c]["H5"]), "of", len(ours), "with h5; missing:",
              ", ".join(c for c in ours if not table[c]["H5"]))
    cols = ["Conference"] + sorted({k for r in table.values() for k in r} - {"Conference"},
                                   key=lambda k: (["CORE", "CCF", "H5"].index(next(p for p in ["CORE", "CCF", "H5"] if k.startswith(p))), k))
    with open(OUT, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=cols, lineterminator="\n", restval="")
        w.writeheader(); w.writerows(table[c] for c in ours)
    print("wrote", OUT)


if __name__ == "__main__":
    main()
