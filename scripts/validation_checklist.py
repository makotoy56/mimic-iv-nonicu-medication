from __future__ import annotations

import argparse

from google.cloud import bigquery
from google.cloud.bigquery import QueryJobConfig

PROJECT_ID = "mimic-iv-portfolio"
DATASET = "nonicu_raas"

TABLES = {
    "base_admissions": f"{PROJECT_ID}.{DATASET}.base_admissions",
    "base_admissions_racegrp": f"{PROJECT_ID}.{DATASET}.base_admissions_racegrp",
    "nonicu_admissions": f"{PROJECT_ID}.{DATASET}.nonicu_admissions",
    "exposure_raas_early": f"{PROJECT_ID}.{DATASET}.exposure_raas_early",
    "analysis_dataset": f"{PROJECT_ID}.{DATASET}.analysis_dataset",
}

FORBIDDEN_COLS = {
    "hosp_los",
    "dischtime",
    "deathtime",
    "hospital_expire_flag",
    "outcome",
}

FEATURE_COLS = {
    "exposure",
    "age",
    "gender",
    "race_group",
    "admission_type",
    "insurance",
    "anchor_year_group",
}


def query_rows(client: bigquery.Client, sql: str, *, step: str, timeout_s: int):
    print(f"[SQL:{step}] {sql}", flush=True)
    job_config = QueryJobConfig()
    try:
        job = client.query(sql, job_config=job_config)
        return list(job.result(timeout=timeout_s))
    except Exception as exc:  # noqa: BLE001
        raise RuntimeError(f"Step '{step}' failed or timed out after {timeout_s}s") from exc


def query_scalar(client: bigquery.Client, sql: str, *, step: str, timeout_s: int) -> int | float:
    rows = query_rows(client, sql, step=step, timeout_s=timeout_s)
    if not rows:
        raise RuntimeError(f"Step '{step}' returned no rows")
    return rows[0][0]


def step_row_counts(client: bigquery.Client, timeout_s: int) -> None:
    union_sql = "\nUNION ALL\n".join(
        [f"SELECT '{name}' AS table_name, COUNT(*) AS n FROM `{table}`" for name, table in TABLES.items()]
    )
    sql = f"SELECT * FROM ({union_sql}) ORDER BY table_name"
    rows = query_rows(client, sql, step="row_counts", timeout_s=timeout_s)

    print("# Row counts")
    for row in rows:
        print(f"{row[0]}: {row[1]:,}")


def step_prevalence(client: bigquery.Client, timeout_s: int) -> None:
    print("# Exposure prevalence")
    prev_primary = query_scalar(
        client,
        f"SELECT AVG(CAST(raas_any_early AS FLOAT64)) FROM `{TABLES['analysis_dataset']}`",
        step="prevalence_primary",
        timeout_s=timeout_s,
    )

    prev_landmark = query_scalar(
        client,
        """
SELECT AVG(CAST(raas_any_early AS FLOAT64))
FROM `mimic-iv-portfolio.nonicu_raas.analysis_dataset`
WHERE deathtime IS NULL
   OR TIMESTAMP_DIFF(deathtime, admittime, HOUR) > 24
""".strip(),
        step="prevalence_landmark_24h",
        timeout_s=timeout_s,
    )

    print(f"primary: {prev_primary:.4%}")
    print(f"24h landmark: {prev_landmark:.4%}")


def step_forbidden() -> None:
    print("# Forbidden columns guard")
    forbidden_in_features = sorted(FORBIDDEN_COLS.intersection(FEATURE_COLS))
    if forbidden_in_features:
        print(f"FAIL: forbidden columns in feature list: {forbidden_in_features}")
    else:
        print("PASS: forbidden columns not in feature list")


def step_repeats(client: bigquery.Client, timeout_s: int) -> None:
    print("# Repeat admissions")
    table = TABLES["nonicu_admissions"]

    # 1回のスキャンで「総入院回数」「ユニーク患者数」「2回以上入院した患者数」を取る
    sql = (
        "SELECT "
        "  SUM(adm_count) AS n_total, "
        "  COUNT(*) AS n_subjects, "
        "  COUNTIF(adm_count >= 2) AS subjects_with_2plus "
        "FROM ("
        f"  SELECT subject_id, COUNT(*) AS adm_count FROM `{table}` GROUP BY subject_id"
        ")"
    )

    rows = query_rows(client, sql, step="repeats", timeout_s=timeout_s)
    if not rows:
        raise RuntimeError("Step 'repeats' returned no rows")

    n_total, n_subjects, subjects_with_2plus = rows[0][0], rows[0][1], rows[0][2]
    if not n_total:
        raise RuntimeError("Step 'repeats' returned n_total=0 (unexpected)")

    # 注意: これは「%患者が複数回」ではなく、入院ベースの “excess admissions” 指標
    repeat_rate = 1 - (n_subjects / n_total)
    pct_subjects_repeat = (subjects_with_2plus / n_subjects) if n_subjects else 0.0

    print(f"[repeats] table = {table}")
    print(f"n_total: {n_total:,}")
    print(f"n_subjects: {n_subjects:,}")
    print(f"subjects_with_2plus: {subjects_with_2plus:,}")
    print(f"repeat admissions rate: {repeat_rate:.4%}")
    print(f"pct subjects with >=2 admissions: {pct_subjects_repeat:.4%}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--step",
        choices=["row_counts", "prevalence", "forbidden", "repeats", "all"],
        default="all",
    )
    parser.add_argument("--timeout", type=int, default=120)
    args = parser.parse_args()

    client = bigquery.Client(project=PROJECT_ID)
    timeout_s = args.timeout

    if args.step in ("row_counts", "all"):
        step_row_counts(client, timeout_s)
        print()
    if args.step in ("prevalence", "all"):
        step_prevalence(client, timeout_s)
        print()
    if args.step in ("forbidden", "all"):
        step_forbidden()
        print()
    if args.step in ("repeats", "all"):
        step_repeats(client, timeout_s)


if __name__ == "__main__":
    main()
