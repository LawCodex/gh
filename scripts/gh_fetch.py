#!/usr/bin/env python3
"""Ghana: download the PDFs listed by gh_list.py from the Parliament of Ghana repository
and convert them to Markdown. Usage: python3 gh_fetch.py [--no-download] [--download-only]"""
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import gh_text as T  # noqa

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(os.path.dirname(REPO), "_raw", "gh")
API = "https://repository.parliament.gh/server/api/"
HANDLE = "https://repository.parliament.gh/handle/%s"
RETRIEVED = os.environ.get("LC_RETRIEVED", "2026-10-13")

ID_PATS = [
    (r"\bP\.?\s?N\.?\s?D\.?\s?C\.?\s?L\.?\s*(\d+)", "PNDCL %s"),
    (r"\bA\.?\s?F\.?\s?R\.?\s?C\.?\s?D\.?\s*(\d+)", "AFRCD %s"),
    (r"\bS\.?\s?M\.?\s?C\.?\s?D\.?\s*(\d+)", "SMCD %s"),
    (r"\bN\.?\s?R\.?\s?C\.?\s?D\.?\s*(\d+)", "NRCD %s"),
    (r"\bN\.?\s?L\.?\s?C\.?\s?D\.?\s*(\d+)", "NLCD %s"),
    (r"\bC\.\s?I\.?\s*(\d+)", "C.I. %s"),
    (r"\bL\.\s?I\.?\s*(\d+)", "L.I. %s"),
    (r"\bE\.\s?I\.?\s*(\d+)", "E.I. %s"),
    (r"\bACT\s*(\d{1,4})\b(?!\s*\))?", "Act %s"),
]
TYPES = {"acts": "act", "constitutional-instruments": "constitutional_instrument",
         "legislative-instruments": "legislative_instrument"}


def identifier(it):
    cands = [it["name"] or ""] + it["metadata"].get("dc.title.alternative", [])
    for c in cands:
        for pat, fmt in ID_PATS:
            m = re.search(pat, c, re.I)
            if m:
                if fmt == "Act %s" and re.search(r"\b(19|20)\d\d\b", m.group(1)):
                    continue
                return fmt % m.group(1)
    return None


def year_of(it):
    m = re.search(r"\b(1[89]\d\d|20\d\d)\b", it["name"] or "")
    if m:
        return m.group(1)
    d = (it["metadata"].get("dc.date.issued") or [""])[0]
    return d[:4] if re.match(r"\d{4}", d) else "undated"


def clean_name(n):
    n = re.sub(r"\s+", " ", n or "").strip().rstrip(".")
    n = re.sub(r"\s*,\s*", ", ", n)
    n = re.sub(r"(\w)\(", r"\1 (", n)
    return n


def convert_one(uid, it, b, dest, suffix, rev_file, used_paths):
    pages, ocr = T.doc_or_pdf_text(dest, "eng", tmpdir=RAW)
    lines = T.clean_pages(pages)
    body = T.structure(lines, "en")
    nchar = sum(len(x) for x in body)
    if nchar < 200:
        print("EMPTY", it["name"], b["name"], nchar, flush=True)
        return None
    name = clean_name(it["name"])
    ident = identifier(it)
    year = year_of(it)
    cat = it["category"]
    base = T.slug(((ident + " ") if ident else "") + re.sub(r"\(?\b(Revised( Edition)?)\b\)?", "", name), 90) + suffix
    rel = "%s/%s/%s.md" % (cat, year, base)
    if rel in used_paths:
        k = 2
        while "%s/%s/%s-%d.md" % (cat, year, base, k) in used_paths:
            k += 1
        rel = "%s/%s/%s-%d.md" % (cat, year, base, k)
    used_paths[rel] = uid
    typ = TYPES.get(cat, "decree")
    issued = (it["metadata"].get("dc.date.issued") or [""])[0]
    revised = rev_file or (re.search(r"revised", it["name"] or "", re.I) and not suffix)
    meta = {
        "title": name + (" (Revised Edition)" if rev_file and "revised" not in name.lower() else ""),
        "identifier": ident,
        "type": typ,
        "jurisdiction": "gh",
        "language": "en",
        "date": issued if re.match(r"^\d{4}-\d{2}-\d{2}$", issued) else None,
        "year": year if year != "undated" else None,
        "status": "unknown",
        "source": HANDLE % it["handle"],
        "file": API + "core/bitstreams/%s/content" % b["uuid"],
        "retrieved": RETRIEVED,
        "collection": it["collection_label"],
        "note": (("Revised edition text (Laws of Ghana, revised edition)" if revised
                  else "Text as published (as enacted, not consolidated)") + ("; text obtained by OCR of a scanned PDF" if ocr else "")),
    }
    T.write_md(os.path.join(REPO, rel), meta, meta["title"], body)
    print("OK", rel, nchar, "OCR" if ocr else "", flush=True)
    return rel


def download_all(items, workers=3):
    """Parallel download (<= 4 connections, as allowed by the LawCodex politeness rules)."""
    from concurrent.futures import ThreadPoolExecutor
    jobs = []
    for it in items.values():
        for b in it.get("bitstreams") or []:
            ext = os.path.splitext(b["name"] or "")[1].lower() or ".bin"
            dest = os.path.join(RAW, "pdf", b["uuid"] + ext)
            if not (os.path.exists(dest) and (ext != ".pdf" or T.pdf_ok(dest))):
                jobs.append((API + "core/bitstreams/%s/content" % b["uuid"], dest, ext == ".pdf"))
    print("to download", len(jobs), flush=True)
    with ThreadPoolExecutor(workers) as ex:
        for i, r in enumerate(ex.map(lambda j: T.fetch(j[0], j[1], delay=0.5, check_pdf=j[2], timeout=600), jobs)):
            if i % 25 == 0:
                print("downloaded", i, flush=True)


def main():
    items = json.load(open(os.path.join(RAW, "items.json")))
    if "--download-only" in sys.argv:
        download_all(items)
        return
    seen_ck = {}
    used_paths = {}
    report = []
    for uid, it in sorted(items.items(), key=lambda kv: (kv[1]["category"], kv[1]["name"] or "")):
        bs = [b for b in (it.get("bitstreams") or []) if (b["name"] or "").lower().endswith((".pdf", ".doc", ".docx")) or True]
        if not bs:
            print("NOFILE", it["name"])
            continue
        # one item may hold several files (e.g. split volumes): take them in order
        files = []
        for b in bs:
            ext = os.path.splitext(b["name"] or "")[1].lower() or ".bin"
            dest = os.path.join(RAW, "pdf", b["uuid"] + ext)
            if "--no-download" not in sys.argv:
                T.fetch(API + "core/bitstreams/%s/content" % b["uuid"], dest, delay=1.5,
                        check_pdf=(ext == ".pdf"), timeout=300)
            if os.path.exists(dest) and (ext != ".pdf" or T.pdf_ok(dest)):
                files.append((b, dest))
            else:
                print("MISSING/BAD", b["name"], it["name"], flush=True)
        if "--download-only" in sys.argv or not files:
            continue
        for fi, (b, dest) in enumerate(files):
            ck = b.get("checksum") or b["uuid"]
            if ck in seen_ck:
                print("DUP", it["name"], "=", seen_ck[ck], flush=True)
                continue
            seen_ck[ck] = it["name"]
            rev = bool(re.search(r"rev", b["name"] or "", re.I))
            suffix = ""
            if len(files) > 1:
                suffix = "-rev-ed" if rev else ("" if fi == 0 or any(re.search(r"rev", x["name"] or "", re.I) for x, _ in files) else "-%d" % (fi + 1))
            r = convert_one(uid, it, b, dest, suffix, rev, used_paths)
            if r:
                report.append(r)
    print("written", len(report))


CONST_ORIG = "http://www.parliament.gh:80/assets/file/Acts%202016/CONSTITUTION%20OF%20THE%20FOURTH%20REPUBLIC%20OF%20GHANA.pdf"
CONST_WB = "https://web.archive.org/web/20161019104717id_/" + CONST_ORIG


def constitution():
    """1992 Constitution as amended by Act 527 (1996), as formerly published on the Parliament website
    (no longer online; Internet Archive capture of 2016-10-19)."""
    dest = os.path.join(RAW, "constitution-1992.pdf")
    T.fetch(CONST_WB, dest, delay=1, check_pdf=True)
    pages, ocr = T.pdf_text(dest, "eng", tmpdir=RAW)
    body = T.structure(T.clean_pages(pages), "en")
    meta = {"title": "Constitution of the Republic of Ghana, 1992", "identifier": "PNDCL 282 (as amended by Act 527)",
            "type": "constitution", "jurisdiction": "gh", "language": "en", "date": "1992-04-28",
            "last_amended": "1996-12-16", "status": "in_force",
            "source": CONST_ORIG.replace(":80", ""), "archived_source": CONST_WB.replace("id_/", "/"),
            "retrieved": RETRIEVED,
            "note": ("Constitution of the Fourth Republic of Ghana (Promulgation) Law, 1992 (PNDCL 282) with the Constitution "
                     "in its Schedule, as amended by the Constitution of the Republic of Ghana (Amendment) Act, 1996 (Act 527); "
                     "in force since 7 January 1993")}
    T.write_md(os.path.join(REPO, "constitution", "constitution-1992.md"), meta, meta["title"], body)
    print("OK constitution", sum(len(x) for x in body), flush=True)


if __name__ == "__main__":
    if "--download-only" not in sys.argv:
        constitution()
    main()
