# Olympia Elementary Closures: Community Analysis

An independent analysis of the Olympia School District proposal to close McKenny, Madison, and LP Brown elementary schools.

## Start here

| I want to... | Click |
|---|---|
| **Read the report online** (works on phones) | [Open the web page](https://emersoncodeprojects.github.io/olympia-closures/) |
| **Download the full report** | [Full report (PDF)](https://emersoncodeprojects.github.io/olympia-closures/OSD_Closure_Community_Analysis.pdf) |
| **Download the two-page fact sheet** (good for printing and sharing) | [Fact sheet (PDF)](https://emersoncodeprojects.github.io/olympia-closures/OSD_Closure_Fact_Sheet.pdf) |
| **Contact the school board** | See "How to be heard" at the bottom of the [web page](https://emersoncodeprojects.github.io/olympia-closures/#get-involved) |

**Key dates:** public hearings at 6 p.m. on Oct. 12 (McKenny), Oct. 15 (LP Brown), and Oct. 19 (Madison). The board votes on Thursday, Nov. 12, 2026.

You do not need a GitHub account to read or download anything here. Everything below this line is for people who want to check the numbers.

---

## What is in this repository

| Path | What it is |
|---|---|
| `index.html` | The full report as a mobile-friendly web page |
| `OSD_Closure_Community_Analysis.pdf` | The full report (version of record) |
| `OSD_Closure_Fact_Sheet.pdf` | Two-page fact sheet |
| `data/` | District enrollment data, 2009-10 to 2026-27, compiled from the OSD enrollment dashboard (see `data/README.md`) |
| `analysis/OSD_Statistical_Analyses.xlsx` | Every number in Appendix A, with live formulas where possible, a Checks tab comparing each reported figure with the reproduced value, and a dependence check for the Welch tests (Welch_sensitivity tab) |
| `analysis/reproduce.py` | The code that recomputes every statistical result from `data/` and writes the workbook |
| `sources/` | District documents that are no longer posted by the district and were recovered from archived copies |
| `tools/` | The script and styles that build the web page |

Everything else the report cites is publicly available; see the References section of the report.

## Reproducing the statistics

Requires Python 3.

```
cd analysis
pip install -r requirements.txt
python reproduce.py
```

The script needs only the six files in `data/`. The bootstrap uses a fixed random seed, so every run gives identical numbers.

## Corrections

The report aims to be accurate first and persuasive second. If you find an error, please open an issue: click the **Issues** tab at the top of this page, then **New issue** (a free GitHub account is required). Every change is recorded in `CHANGELOG.md` and in this repository's history.

## Updating the web page

`tools/build_site.py` rebuilds `index.html` from the author's Word copy of the report, which is not published here (needs pandoc and BeautifulSoup). The PDF is the version of record.

```
cd tools
python build_site.py path/to/report.docx ..
```
