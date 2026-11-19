"""Rebuild missing non-ICU analysis tables without replacing existing tables.

Run without arguments for a read-only full-pipeline dry run. --execute creates
only missing tables, with an explicit 60-day lifetime for BigQuery sandbox.
Patient records are never printed or written to local files.
"""
import argparse
from pathlib import Path

import google.auth
from google.api_core.exceptions import NotFound
from google.cloud import bigquery
from real_data_access import real_data_io, require_destination

ROOT = Path(__file__).resolve().parents[1]
DATASET = "mimic-iv-portfolio.nonicu_raas"
STEPS = [
    ("base_admissions", "01_build_base_hosp_admissions.sql"),
    ("base_admissions_racegrp", "01_collapse_race_categories.sql"),
    ("nonicu_admissions", "02_exclude_icu_admissions.sql"),
    ("exposure_raas_early", "03_define_exposure_raas_early.sql"),
    ("analysis_dataset", "03_build_analysis_dataset.sql"),
]
LIMIT = 10 * 1024**3


def load_steps(root=ROOT):
    steps = []
    for table, filename in STEPS:
        sql = (root / "sql" / filename).read_text()
        header = f"CREATE OR REPLACE TABLE `{DATASET}.{table}` AS\n"
        if sql.count(header) != 1:
            raise ValueError(f"Unexpected CREATE statement in {filename}")
        body = sql.split(header, 1)[1].strip().removesuffix(";")
        steps.append((table, sql, body))
    return steps


def dry_run_query(steps):
    ctes = []
    for table, _, body in steps:
        for name, _, _ in steps:
            body = body.replace(f"`{DATASET}.{name}`", name)
        ctes.append(f"{table} AS (\n{body}\n)")
    return "WITH " + ",\n".join(ctes) + "\nSELECT * FROM analysis_dataset"


def creation_query(table, sql):
    header = f"CREATE OR REPLACE TABLE `{DATASET}.{table}` AS\n"
    replacement = (
        f"CREATE TABLE `{DATASET}.{table}`\n"
        "OPTIONS (expiration_timestamp = TIMESTAMP_ADD(CURRENT_TIMESTAMP(), INTERVAL 60 DAY)) AS\n"
    )
    return sql.replace(header, replacement, 1)


@real_data_io
def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true", help="Create missing tables after dry-run validation")
    args = parser.parse_args()
    require_destination(DATASET)
    steps = load_steps()
    credentials, _ = google.auth.default()
    client = bigquery.Client(project="mimic-iv-portfolio", credentials=credentials)
    location = client.get_dataset(DATASET).location
    job = client.query(
        dry_run_query(steps), location=location,
        job_config=bigquery.QueryJobConfig(dry_run=True, use_query_cache=False),
    )
    print(f"Full-pipeline dry run: {job.total_bytes_processed:,} bytes")
    if job.total_bytes_processed > LIMIT:
        raise RuntimeError("Source scan exceeds the 10 GiB safety limit")
    if not args.execute:
        print("Read-only validation complete. Use --execute to create missing tables.")
        return
    for table, sql, _ in steps:
        name = f"{DATASET}.{table}"
        try:
            metadata = client.get_table(name)
            action = "kept existing"
        except NotFound:
            # CREATE TABLE intentionally fails on a concurrent creation; never replace.
            client.query(
                creation_query(table, sql), location=location,
                job_config=bigquery.QueryJobConfig(maximum_bytes_billed=LIMIT),
            ).result()
            metadata = client.get_table(name)
            if metadata.expires is None:
                raise RuntimeError(f"Created table has no expected 60-day expiration: {table}")
            action = "created"
        print(f"{table}: {action}; rows={metadata.num_rows:,}; expires={metadata.expires}")


if __name__ == "__main__":
    main()
