# mRNA-therapy-history-data

Dataset and figure tracking clinical trials of mRNA therapies (excluding COVID-19), pulled from [ClinicalTrials.gov](https://clinicaltrials.gov) and refreshed automatically.

The original dataset and figure supported a 2022 article on [Speaking of Research](https://speakingofresearch.com/2022/05/18/a-recent-uptick-in-the-number-of-mrna-vaccines-being-tested-in-humans/) documenting the rise in non‑COVID mRNA clinical trials. This repository now keeps that picture up to date.

![Cumulative mRNA therapy trials by disease type](figures/mRNA%20therapy%20graph.png)

## What's in the repo

- **`data/mrna_trials.csv`** — raw fields pulled from the ClinicalTrials.gov v2 API (NCT ID, start date, conditions, interventions, sponsor, etc.) with an `is_covid` flag and a `match_source` confidence tier.
- **`data/mrna_trials_classified.csv`** — the same rows with derived `disease_type` (Cancer / Virus / Genetic Disease / Other) and `therapy_type` (Vax / Dendritic Vax / IV infusion / Modified T cells / Gene editing / Intratumoral / Subcutaneous / Other) columns.
- **`figures/graph.R`** — renders the cumulative-area figure from the classified CSV. Year range and y-axis are inferred from the data so the script keeps working as new trials are added.
- **`scripts/fetch_trials.py`** — pulls trials whose brief title, official title, or intervention name contains `mRNA` / `messenger RNA`. Uses only the Python standard library.
- **`scripts/classify.py`** — applies keyword rules to add `disease_type` and `therapy_type`.
- **`Non-covid mRNA vaccines since 01_01_2020 - Sheet1.csv`** — the original hand-curated dataset, preserved as a historical record.

## Running the pipeline locally

No pip packages needed for the fetcher/classifier. The figure script needs a working R install with `dplyr`, `tidyr`, `ggplot2`, `RColorBrewer`, and `tibble`.

```sh
python3 scripts/fetch_trials.py
python3 scripts/classify.py
Rscript figures/graph.R
```

## Automated monthly refresh

[`.github/workflows/update-data.yml`](.github/workflows/update-data.yml) re-runs the pipeline on the 1st of every month and opens a pull request when the data changes, so the repository can be kept current without manual effort. The workflow can also be triggered on demand from the Actions tab.

## Caveats

- The v2 API tokenizes compound codes like `mRNA-1010` as indivisible atoms, so a bare `mRNA` query misses some studies whose indexed text contains only the hyphenated form. The fetcher seeds a list of known compound codes (in `scripts/fetch_trials.py`) to cover these; extend `EXTRA_TERMS` when new programs appear.
- Rows where the `mRNA` match is only in the long official title (`match_source = official_title_only`) occasionally describe studies whose therapy *targets* a particular mRNA rather than *being* one. Treat that tier as needing review.
- Classification is rule-based, not LLM-curated. Spot-check new rows before citing specific per-category counts.
