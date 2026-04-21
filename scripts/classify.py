"""Add `disease_type` and `therapy_type` columns to the fetched trial CSV.

Reads the output of `fetch_trials.py` and applies keyword rules drawn from the
original manual curation (Cancer / Virus / Genetic Disease for disease type;
Vax / Dendritic Vax / IV infusion / Modified T cells / Gene editing /
Intratumoral / Other for therapy type).

The therapy rules also carry a per-disease fallback for the common case where
an intervention reads only as a bare drug code like `DRUG: mRNA-3927` — the
original curator knew those are IV-delivered for genetic diseases and
vaccines for viral/oncology targets, and we reproduce that inference rather
than leaving the row as "Other".

Any row flagged as low-confidence by fetch_trials.py (`match_source =
official_title_only`) is still classified, but downstream consumers can filter
on that column if they want the stricter set.

Run:
    python3 scripts/classify.py --in data/mrna_trials.csv --out data/mrna_trials_classified.csv
"""

from __future__ import annotations

import argparse
import csv
import re
from pathlib import Path

MRNA_CODE_RE = re.compile(r"mrna-?\d{3,5}", re.IGNORECASE)


CANCER_TERMS = (
    "cancer", "tumor", "tumour", "carcinoma", "melanoma", "leukemia",
    "leukaemia", "lymphoma", "sarcoma", "neoplasm", "glioma", "glioblastoma",
    "myeloma", "malignan", "oncolog", "adenocarcinoma", "mesothelioma",
    "astrocytoma", "pd-1", "pd-l1", "pd1-high", "her2", "solid tumor",
)

VIRUS_TERMS = (
    "virus", "viral", "influenza", " flu ", " hiv", "cmv", "cytomegalovirus",
    "ebv", "epstein-barr", "hpv", "papillomavirus", "rsv",
    "respiratory syncytial", "rabies", "zika", "chikungunya", "covid",
    "sars", "hepatitis", "herpes", "pneumococcal", "meningococcal",
    "chlamydia", "nipah", "vaccin",  # generic "vaccine" conditions usually indicate viral target
    "tuberculosis", "malaria", "varicella", "zoster", "dengue", "ebola",
    "norovirus",
)

GENETIC_TERMS = (
    "genetic", "hereditary", "familial", "acidemia", "acidaemia",
    "glycogen storage", "granulomatous disease", "cystic fibrosis",
    "hypercholesterolemia", "methylmalonic", "propionic",
    "phenylketonuria", "huntington", "duchenne", "fabry",
    "gaucher", "pompe", "hurler", "hunter syndrome", "sickle cell",
    "hemophilia", "ornithine transcarbamylase", "otc deficiency",
    "alpha-1 antitrypsin", "crigler-najjar", "niemann-pick",
    "pulmonary arterial hypertension",  # mRNA-3745 domain-adjacent; optional
    "hypoparathyroidism",
)

# Therapy classification is built from intervention names + brief title.
# Order matters — earlier buckets win when multiple match.
THERAPY_RULES = (
    ("Dendritic Vax",
     ("dendritic cell", "dc vaccin", "dc-vaccin", "tumor lysate-loaded")),
    ("Modified T cells",
     ("car-t", "car t cell", "tcr-t", "tcr t cell", "t-cell receptor",
      "genetically modified t", "engineered t cell")),
    ("Gene editing",
     ("crispr", "gene editing", "base editing", "zinc finger")),
    ("Intratumoral",
     ("intratumoral", "intralesional", "intra-tumoral")),
    ("IV infusion",
     ("iv infusion", "intravenous", " iv ", "infusion")),
    ("Subcutaneous",
     ("subcutaneous", " subq ", "subq injection", " sq ")),
    ("Vax",
     ("vaccine", "vaccination", "immunization", "immunisation")),
)


def contains_any(text: str, needles: tuple[str, ...]) -> bool:
    t = f" {text.lower()} "
    return any(n in t for n in needles)


def classify_disease(row: dict) -> str:
    hay = f"{row['conditions']} {row['brief_title']}".lower()
    # Cancer wins over virus when both match (e.g. HPV-associated cervical cancer)
    if contains_any(hay, CANCER_TERMS):
        return "Cancer"
    if contains_any(hay, GENETIC_TERMS):
        return "Genetic Disease"
    if contains_any(hay, VIRUS_TERMS):
        return "Virus"
    return "Other"


def classify_therapy(row: dict, disease_type: str) -> str:
    hay = f"{row['brief_title']} {row['interventions']}".lower()
    for label, needles in THERAPY_RULES:
        if contains_any(hay, needles):
            return label
    # Fallback when an intervention is only labeled with a bare compound code
    # like "DRUG: mRNA-3927" — no route or vaccine keyword. Infer from disease.
    if MRNA_CODE_RE.search(row["interventions"]):
        if disease_type == "Genetic Disease":
            return "IV infusion"
        if disease_type in ("Virus", "Cancer"):
            return "Vax"
    return "Other"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in", dest="input_path", type=Path,
                        default=Path("data/mrna_trials.csv"))
    parser.add_argument("--out", dest="output_path", type=Path,
                        default=Path("data/mrna_trials_classified.csv"))
    args = parser.parse_args()

    with args.input_path.open(encoding="utf-8") as f:
        rows = list(csv.DictReader(f))

    fieldnames = list(rows[0].keys()) + ["disease_type", "therapy_type"]

    classified: list[dict] = []
    for r in rows:
        r["disease_type"] = classify_disease(r)
        r["therapy_type"] = classify_therapy(r, r["disease_type"])
        classified.append(r)

    args.output_path.parent.mkdir(parents=True, exist_ok=True)
    with args.output_path.open("w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(classified)

    from collections import Counter
    print(f"Classified {len(classified)} rows -> {args.output_path}")
    print("disease_type:", dict(Counter(r["disease_type"] for r in classified)))
    print("therapy_type:", dict(Counter(r["therapy_type"] for r in classified)))


if __name__ == "__main__":
    main()
