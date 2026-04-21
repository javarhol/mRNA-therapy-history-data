"""Fetch mRNA-titled trials from ClinicalTrials.gov API v2 and write them to CSV.

Uses only the Python standard library so no pip install is required. The search
mirrors the original project: studies with "mRNA" in the title. COVID-19 is NOT
filtered at the API level — it is flagged in an `is_covid` column so downstream
analysis can include or exclude it.

Run:
    python3 scripts/fetch_trials.py --out data/mrna_trials.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

API_URL = "https://clinicaltrials.gov/api/v2/studies"
PAGE_SIZE = 100

# The v2 API tokenizes "mRNA-1010"-style compounds as indivisible tokens, so a
# bare "mRNA" query (in any scope, with any wildcard we tested) will not match
# a study whose indexed text contains ONLY the hyphenated form. We pull the
# broad `query.term=mRNA` (~2857 hits) and client-side-filter to studies whose
# brief or official title contains "mrna" as a substring. This covers the
# large majority but will miss a handful of studies whose titles use only a
# compound code (e.g. "A Study of mRNA-1010...") and whose full-text index
# contains no standalone "mRNA" token. Those can be added with targeted
# per-compound queries in `EXTRA_TERMS` below.
QUERIES = (
    {"query.term": "mRNA"},
    {"query.term": '"messenger RNA"'},
)
# Known compound codes that the broad query misses because the API tokenizes
# "mRNA-NNNN" as an atom. Extend as new programs appear.
EXTRA_TERMS: tuple[str, ...] = (
    "mRNA-1010",
    "mRNA-1273",
    "mRNA-1647",
    "mRNA-1189",
    "mRNA-1345",
    "mRNA-1653",
    "mRNA-1893",
    "mRNA-2752",
    "mRNA-3704",
    "mRNA-3705",
    "mRNA-3745",
    "mRNA-3927",
    "mRNA-4157",
)
QUERIES = QUERIES + tuple({"query.term": t} for t in EXTRA_TERMS)

# Substrings (lowercased) that qualify a study as an mRNA trial if they appear
# in the brief title, official title, OR any intervention name. Intervention
# matching is what catches studies like NCT02872025, whose title was renamed
# away from "mRNA" but whose intervention is still "Intralesional mRNA 2752".
TITLE_FILTERS = ("mrna", "messenger rna")

COVID_TERMS = ("covid", "sars-cov-2", "sars-cov2", "sarscov2", "ncov")

CSV_FIELDS = [
    "nct_id",
    "study_first_posted",
    "start_date",
    "start_year",
    "conditions",
    "interventions",
    "study_type",
    "phases",
    "lead_sponsor",
    "sponsor_class",
    "brief_title",
    "is_covid",
    "match_source",
    "url",
]


def fetch_page(base_params: dict, page_token: str | None) -> dict:
    params = dict(base_params)
    params["pageSize"] = str(PAGE_SIZE)
    params["format"] = "json"
    if page_token:
        params["pageToken"] = page_token
    url = f"{API_URL}?{urllib.parse.urlencode(params)}"
    with urllib.request.urlopen(url, timeout=60) as resp:
        return json.loads(resp.read().decode("utf-8"))


def get(d: dict, *path, default=None):
    cur = d
    for key in path:
        if not isinstance(cur, dict) or key not in cur:
            return default
        cur = cur[key]
    return cur if cur is not None else default


def is_covid_study(conditions: list[str], title: str) -> bool:
    haystack = " ".join(conditions + [title]).lower()
    return any(term in haystack for term in COVID_TERMS)


def flatten(study: dict) -> dict | None:
    proto = study.get("protocolSection", {})
    ident = proto.get("identificationModule", {})
    status = proto.get("statusModule", {})
    sponsor = get(proto, "sponsorCollaboratorsModule", "leadSponsor", default={})
    design = proto.get("designModule", {})
    conds = get(proto, "conditionsModule", "conditions", default=[]) or []
    arms = get(proto, "armsInterventionsModule", "interventions", default=[]) or []
    intervention_names = [
        f"{i.get('type', '')}: {i.get('name', '')}".strip(": ") for i in arms
    ]

    brief_title = ident.get("briefTitle", "") or ""
    official_title = ident.get("officialTitle", "") or ""

    def hit(text: str) -> bool:
        text = text.lower()
        return any(f in text for f in TITLE_FILTERS)

    interventions_joined = " ".join(intervention_names)
    if hit(brief_title):
        match_source = "brief_title"
    elif any(hit(n) for n in intervention_names):
        match_source = "intervention"
    elif hit(official_title):
        # Lower-confidence: official titles are long and sometimes mention mRNA
        # only as a biomarker or therapeutic target (e.g. anti-sense oligos that
        # TARGET a particular mRNA), not as the therapy itself. Downstream
        # analysis can filter on match_source to drop these if desired.
        match_source = "official_title_only"
    else:
        return None

    start_date = get(status, "startDateStruct", "date", default="") or ""
    start_year = start_date[:4] if len(start_date) >= 4 else ""

    nct_id = ident.get("nctId", "")

    return {
        "nct_id": nct_id,
        "study_first_posted": get(status, "studyFirstPostDateStruct", "date", default=""),
        "start_date": start_date,
        "start_year": start_year,
        "conditions": "; ".join(conds),
        "interventions": "; ".join(intervention_names),
        "study_type": design.get("studyType", ""),
        "phases": "; ".join(design.get("phases", []) or []),
        "lead_sponsor": sponsor.get("name", ""),
        "sponsor_class": sponsor.get("class", ""),
        "brief_title": brief_title,
        "is_covid": is_covid_study(conds, brief_title + " " + official_title),
        "match_source": match_source,
        "url": f"https://clinicaltrials.gov/study/{nct_id}" if nct_id else "",
    }


def fetch_all(verbose: bool = True) -> list[dict]:
    by_nct: dict[str, dict] = {}
    for base_params in QUERIES:
        label = next(iter(base_params.values()))
        if verbose:
            print(f"Query: {label}", file=sys.stderr)
        token: str | None = None
        page = 0
        while True:
            page += 1
            data = fetch_page(base_params, token)
            studies = data.get("studies", []) or []
            for s in studies:
                row = flatten(s)
                if row and row["nct_id"] and row["nct_id"] not in by_nct:
                    by_nct[row["nct_id"]] = row
            if verbose:
                print(f"  page {page}: fetched {len(studies)} (unique so far {len(by_nct)})", file=sys.stderr)
            token = data.get("nextPageToken")
            if not token:
                break
            time.sleep(0.2)
    return list(by_nct.values())


def write_csv(rows: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("data/mrna_trials.csv"),
        help="Output CSV path (default: data/mrna_trials.csv)",
    )
    args = parser.parse_args()

    print("Fetching mRNA-titled studies from ClinicalTrials.gov API v2…", file=sys.stderr)
    rows = fetch_all()

    rows.sort(key=lambda r: (r["start_date"] or "", r["nct_id"]), reverse=True)
    write_csv(rows, args.out)

    total = len(rows)
    covid = sum(1 for r in rows if r["is_covid"])
    print(f"Wrote {total} rows to {args.out} ({covid} flagged COVID, {total - covid} non-COVID).", file=sys.stderr)


if __name__ == "__main__":
    main()
