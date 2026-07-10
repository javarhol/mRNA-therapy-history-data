import csv
import sys
from collections import defaultdict
from pathlib import Path

def generate_table(input_csv: Path, output_md: Path):
    with open(input_csv, newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        counts = defaultdict(list)
        for row in reader:
            is_covid = str(row.get("is_covid", "")).lower() in ["true", "1", "yes"]
            if is_covid:
                continue
            if row.get("match_source") == "official_title_only":
                continue
            dtype = row.get("disease_type")
            if not dtype or dtype == "Other":
                cond = row.get("conditions", "")
                if cond:
                    counts[cond].append((row["nct_id"], row["url"]))

    output_md.parent.mkdir(parents=True, exist_ok=True)
    with open(output_md, "w", encoding='utf-8') as f:
        f.write("# Breakdown of 'Other' Conditions\n\n")
        f.write("This table breaks down the trials that were categorized under the **Other** disease type.\n\n")
        f.write("| Condition | Number of Trials | Trials (Links) |\n")
        f.write("| :--- | :--- | :--- |\n")
        # sort by count descending
        sorted_conds = sorted(counts.items(), key=lambda x: len(x[1]), reverse=True)
        for cond, trials in sorted_conds:
            links = [f"[{nct}]({url})" for nct, url in trials]
            f.write(f"| {cond} | {len(trials)} | {', '.join(links)} |\n")

    print(f"Wrote markdown table to {output_md}", file=sys.stderr)

if __name__ == "__main__":
    generate_table(
        Path("data/mrna_trials_classified.csv"),
        Path("figures/other_conditions_table.md")
    )
