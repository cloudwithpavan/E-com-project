from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from google.cloud import bigquery, storage

PROJECT_ID = "my-project-77-511616"
BIGQUERY_LOCATION = "US"

SOURCE_BUCKET = "ecommerce-analytics-raw-lct2026"
SOURCE_FILE = "customer_200_records.csv"
INVALID_BUCKET = "ecommerce-analytics-unprocessed-lct2026"
VALID_BUCKET = "ecommerce-analytics-cleaned-lct2026"
INVALID_FILE = "customer_data_invalid.csv"
VALID_FILE = "customer_data_valid.csv"

STAGE_TABLE = f"{PROJECT_ID}.ecommerce_stage_dataset.customer_stg"
DIMENSION_TABLE = f"{PROJECT_ID}.ecommerce_final_dataset.customer_dim"
GCS_URI = f"gs://{VALID_BUCKET}/{VALID_FILE}"

COLUMNS = [
    "customer_id", "first_name", "last_name", "email", "phone",
    "city", "state", "country", "signup_date", "customer_status",
]
SCHEMA = [
    bigquery.SchemaField("customer_id", "STRING"),
    bigquery.SchemaField("first_name", "STRING"),
    bigquery.SchemaField("last_name", "STRING"),
    bigquery.SchemaField("email", "STRING"),
    bigquery.SchemaField("phone", "STRING"),
    bigquery.SchemaField("city", "STRING"),
    bigquery.SchemaField("state", "STRING"),
    bigquery.SchemaField("country", "STRING"),
    bigquery.SchemaField("signup_date", "DATE"),
    bigquery.SchemaField("customer_status", "STRING"),
]

def data_validation_task():
    gcs = storage.Client(project=PROJECT_ID)
    source = gcs.bucket(SOURCE_BUCKET).blob(SOURCE_FILE)
    if not source.exists():
        raise FileNotFoundError(f"Missing gs://{SOURCE_BUCKET}/{SOURCE_FILE}")

    df = pd.read_csv(BytesIO(source.download_as_bytes()), dtype={"customer_id": "string"})
    missing = [col for col in COLUMNS if col not in df.columns]
    if missing:
        raise ValueError(f"CSV missing columns {missing}; found {list(df.columns)}")

    df = df[COLUMNS].copy()
    ids = df["customer_id"].astype("string").str.strip()
    invalid_mask = ids.isna() | ids.eq("")
    valid_df = df.loc[~invalid_mask].copy()
    invalid_df = df.loc[invalid_mask].copy()
    valid_df["customer_id"] = ids.loc[~invalid_mask]

    # Convert dates to YYYY-MM-DD so BigQuery DATE loading is predictable.
    for frame in (valid_df, invalid_df):
        frame["signup_date"] = pd.to_datetime(
            frame["signup_date"], errors="coerce"
        ).dt.strftime("%Y-%m-%d")

    gcs.bucket(INVALID_BUCKET).blob(INVALID_FILE).upload_from_string(
        invalid_df.to_csv(index=False), content_type="text/csv"
    )
    gcs.bucket(VALID_BUCKET).blob(VALID_FILE).upload_from_string(
        valid_df.to_csv(index=False), content_type="text/csv"
    )

    print(f"Total={len(df)}, valid={len(valid_df)}, invalid={len(invalid_df)}")
    if valid_df.empty:
        raise ValueError("No valid records found; stopping before BigQuery load.")
    return len(valid_df)


def load_csv_from_gcs():
    bq = bigquery.Client(project=PROJECT_ID)
    config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
        autodetect=False,
    )
    job = bq.load_table_from_uri(
        GCS_URI, STAGE_TABLE, job_config=config, location=BIGQUERY_LOCATION
    )
    job.result()
    print(f"Loaded {job.output_rows} rows into {STAGE_TABLE}")
    return job.output_rows or 0


# BigQuery MERGE cannot update a matched row and also insert its replacement
# version from the same source row in one matched branch. Use a transaction:
# expire changed active rows, then insert new/changed active versions.
MERGE_CUSTOMERS_SQL = f"""
DECLARE run_date DATE DEFAULT CURRENT_DATE('UTC');

BEGIN TRANSACTION;

UPDATE `{DIMENSION_TABLE}` AS target
SET
  end_date = DATE_SUB(run_date, INTERVAL 1 DAY),
  status = 'INACTIVE'
WHERE target.status = 'ACTIVE'
  AND target.end_date IS NULL
  AND EXISTS (
    SELECT 1
    FROM (
      SELECT * FROM `{STAGE_TABLE}`
      WHERE customer_id IS NOT NULL AND TRIM(customer_id) != ''
      QUALIFY ROW_NUMBER() OVER (
        PARTITION BY customer_id ORDER BY signup_date DESC, email
      ) = 1
    ) AS source
    WHERE source.customer_id = target.customer_id
      AND (
        target.first_name IS DISTINCT FROM source.first_name
        OR target.last_name IS DISTINCT FROM source.last_name
        OR target.email IS DISTINCT FROM source.email
        OR target.phone IS DISTINCT FROM source.phone
        OR target.city IS DISTINCT FROM source.city
        OR target.state IS DISTINCT FROM source.state
        OR target.country IS DISTINCT FROM source.country
        OR target.signup_date IS DISTINCT FROM source.signup_date
        OR target.customer_status IS DISTINCT FROM source.customer_status
      )
  );

INSERT INTO `{DIMENSION_TABLE}` (
  customer_id, first_name, last_name, email, phone, city, state,
  country, signup_date, customer_status, start_date, end_date, status
)
WITH stage_latest AS (
  SELECT * FROM `{STAGE_TABLE}`
  WHERE customer_id IS NOT NULL AND TRIM(customer_id) != ''
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY customer_id ORDER BY signup_date DESC, email
  ) = 1
)
SELECT
  s.customer_id, s.first_name, s.last_name, s.email, s.phone,
  s.city, s.state, s.country, s.signup_date, s.customer_status,
  run_date, CAST(NULL AS DATE), 'ACTIVE'
FROM stage_latest AS s
LEFT JOIN `{DIMENSION_TABLE}` AS active
  ON active.customer_id = s.customer_id
  AND active.status = 'ACTIVE'
  AND active.end_date IS NULL
WHERE active.customer_id IS NULL;

COMMIT TRANSACTION;
"""

def merge_customers_scd_type_2():
    bq = bigquery.Client(project=PROJECT_ID)
    job = bq.query(MERGE_CUSTOMERS_SQL, location=BIGQUERY_LOCATION)
    job.result()
    print(f"SCD Type 2 merge completed for {STAGE_TABLE} -> {DIMENSION_TABLE}")
    return int(job.num_dml_affected_rows or 0)


default_args = {
    "owner": "data-engineering",
    "start_date": datetime(2026, 10, 9),
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}

with DAG(
    dag_id="etl_dag1",
    default_args=default_args,
    description="Validate 200 customer records, load BigQuery staging, and update SCD Type 2 dimension",
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["ecommerce", "gcs", "bigquery", "scd-type-2"],
) as dag:
    validate = PythonOperator(
        task_id="data_validation_task",
        python_callable=data_validation_task,
    )
    load_stage = PythonOperator(
        task_id="gcs_to_bq_stage_job",
        python_callable=load_csv_from_gcs,
    )
    merge_dimension = PythonOperator(
        task_id="scd_type_2_merge_job",
        python_callable=merge_customers_scd_type_2,
    )
    validate >> load_stage >> merge_dimension
