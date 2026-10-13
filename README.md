# Ghana (GH) — legislation as Markdown

Part of [LawCodex](https://github.com/LawCodex): the legislation of every country as plain Markdown in git.

Legislation of the Republic of Ghana, in **English**, from the **Parliament of Ghana institutional repository**
(https://repository.parliament.gh, DSpace), "LEGAL STATUTES" community: Acts of Parliament of the First to Fourth
Republics, decrees and laws of the military governments (NLC, NRC, SMC, AFRC, PNDC), Constitutional Instruments and
Legislative Instruments — plus the **1992 Constitution**.

Many pre-2004 Acts and decrees are the **revised-edition texts** (Laws of Ghana, revised edition — marked
"(Revised Edition)" and `note: Revised edition text`); other texts are as enacted (not consolidated).

Retrieved 2026-10-13.

<!-- COUNTS -->
| Directory | Files |
|---|---|
| `acts/` | 453 |
| `constitution/` | 1 |
| `constitutional-instruments/` | 83 |
| `decrees/afrcd/` | 8 |
| `decrees/nlcd/` | 13 |
| `decrees/nrcd/` | 32 |
| `decrees/pndcl/` | 50 |
| `decrees/smcd/` | 13 |
| `legislative-instruments/` | 14 |
| **Total** | **667** |
<!-- /COUNTS -->

## Structure

```
constitution/constitution-1992.md                       Constitution of 1992 as amended by Act 527 (1996)
acts/<year>/act-<n>-<slug>.md                           Acts of Parliament (Act number when known)
decrees/nlcd/<year>/nlcd-<n>-<slug>.md                  National Liberation Council Decrees (1966-69)
decrees/nrcd/<year>/...                                 National Redemption Council Decrees (1972-75)
decrees/smcd/<year>/...                                 Supreme Military Council Decrees (1975-79)
decrees/afrcd/<year>/...                                Armed Forces Revolutionary Council Decrees (1979)
decrees/pndcl/<year>/...                                Provisional National Defence Council Laws (1982-92)
constitutional-instruments/<year>/c-i-<n>-<slug>.md     Constitutional Instruments
legislative-instruments/<year>/l-i-<n>-<slug>.md        Legislative Instruments (only the few in the repository)
```

`<year>` is the year in the title (or the repository's `dc.date.issued`). When a repository record holds both the
original text and the revised-edition text, both are converted (the revised edition gets the suffix `-rev-ed`).

Front matter: `identifier` (e.g. `Act 987`, `PNDCL 182`, `NRCD 349`, `C.I. 112`), `date` (repository
`dc.date.issued` when a full date), `source` = repository handle page, `file` = bitstream (PDF) URL, `collection` =
repository collection, `status: unknown` (the repository does not record repeal/amendment), `note` (revised
edition or as enacted; OCR).

Headings: PART / CHAPTER / SCHEDULE → `##`/`###`; sections → headings (`Section N`, or `Section N — Title` in
revised editions). Many PDFs are scans: their text was produced by OCR (tesseract, English; marked `OCR` in `note`)
and contains recognition errors.

## Sources

| Source | URL | Used for |
|---|---|---|
| Parliament of Ghana — institutional repository (DSpace 7 REST API) | https://repository.parliament.gh/server/api/ (community "LEGAL STATUTES") | Acts, decrees, CIs, LIs |
| Parliament of Ghana website (2016), via Internet Archive | https://www.parliament.gh/assets/file/Acts%202016/CONSTITUTION%20OF%20THE%20FOURTH%20REPUBLIC%20OF%20GHANA.pdf → https://web.archive.org/web/20161019104717/… | 1992 Constitution |

The Parliament website's terms ("Disclaimer": https://www.parliament.gh/disclaimer) allow viewing, copying,
downloading, printing and distributing its content for informational or reference, non-commercial purposes; this
repository is such a non-commercial, informational use. The repository's robots.txt was respected (only the REST
API and bitstream downloads were used; no search/facet pages), with at most 3 parallel connections.

## Not covered / known gaps

* **Partial corpus**: the repository holds ~620 legislative items, far from all of Ghana's legislation (Act numbers
  now exceed 1,130; Fourth Republic Acts alone run from Act 449 onwards); in particular the 5th–6th Parliament (2009–2016) collection holds
  only 4 Acts. There is no official online consolidated database of Ghanaian legislation (the Ministry of
  Justice site did not answer); the AfricanLII "GhaLII" site was deliberately not used (its terms forbid bulk
  download).
* Executive Instruments, Bills, and most Legislative Instruments (only ~14 in the repository) are not included.
* The Constitution text is the one formerly published by Parliament (1992 text as amended in 1996).
* Items without a PDF or whose PDF could not be read are reported by the fetch script (`NOFILE`, `MISSING/BAD`,
  `EMPTY`).

## Regenerating

```sh
python3 scripts/gh_list.py --with-li          # lists items and bitstreams (../_raw/gh/items.json)
python3 scripts/gh_fetch.py --download-only   # downloads PDFs (≤3 connections)
python3 scripts/gh_fetch.py --no-download --jobs 3   # OCR/text extraction in parallel, then Markdown
python3 scripts/gh_readme.py                  # updates the counts table
```
