from datetime import datetime, timedelta
from io import BytesIO

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from google.cloud import bigquery, storage


# ---------------------------------------------------------------------------
# GCP and pipeline configuration
# ---------------------------------------------------------------------------
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


# The schema matches the customer CSV columns:
# customer_id, first_name, last_name, email, phone, city, state, country,
# signup_date, customer_status
SCHEMA = [
    bigquery.SchemaField("customer_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("first_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("last_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("phone", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("city", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("state", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("country", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("signup_date", "DATE", mode="NULLABLE"),
    bigquery.SchemaField("customer_status", "STRING", mode="NULLABLE"),
]


# SCD Type 2 process:
# 1. Deduplicate staging rows by customer_id.
# 2. Expire active dimension rows when tracked source values change.
# 3. Insert customers with no active version, including changed customers
#    whose old active version was expired in step 2.
#
# Expected dimension table columns:
# the 10 source columns above, plus start_date DATE, end_date DATE,
# and status STRING.
MERGE_CUSTOMERS_SQL = f"""
DECLARE run_date DATE DEFAULT CURRENT_DATE('UTC');

CREATE TEMP TABLE stage_latest AS
SELECT
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    state,
    country,
    signup_date,
    customer_status
FROM `{STAGE_TABLE}`
WHERE customer_id IS NOT NULL
  AND TRIM(customer_id) != ''
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY customer_id
    ORDER BY
        signup_date DESC,
        email,
        first_name,
        last_name,
        phone,
        city,
        state,
        country,
        customer_status
) = 1;

BEGIN TRANSACTION;

-- Expire current versions when any tracked source attribute changes.
UPDATE `{DIMENSION_TABLE}` AS target
SET
    end_date = DATE_SUB(run_date, INTERVAL 1 DAY),
    status = 'INACTIVE'
WHERE target.status = 'ACTIVE'
  AND target.end_date IS NULL
  AND EXISTS (
      SELECT 1
      FROM stage_latest AS source
      WHERE source.customer_id = target.customer_id
        AND (
            source.first_name IS DISTINCT FROM target.first_name
            OR source.last_name IS DISTINCT FROM target.last_name
            OR source.email IS DISTINCT FROM target.email
            OR source.phone IS DISTINCT FROM target.phone
            OR source.city IS DISTINCT FROM target.city
            OR source.state IS DISTINCT FROM target.state
            OR source.country IS DISTINCT FROM target.country
            OR source.signup_date IS DISTINCT FROM target.signup_date
            OR source.customer_status IS DISTINCT FROM target.customer_status
        )
  );

-- Insert brand-new customers and the new versions of changed customers.
INSERT INTO `{DIMENSION_TABLE}` (
    customer_id,
    first_name,
    last_name,
    email,
    phone,
    city,
    state,
    country,
    signup_date,
    customer_status,
    start_date,
    end_date,
    status
)
SELECT
    source.customer_id,
    source.first_name,
    source.last_name,
    source.email,
    source.phone,
    source.city,
    source.state,
    source.country,
    source.signup_date,
    source.customer_status,
    run_date AS start_date,
    CAST(NULL AS DATE) AS end_date,
    'ACTIVE' AS status
FROM stage_latest AS source
LEFT JOIN `{DIMENSION_TABLE}` AS target
    ON target.customer_id = source.customer_id
   AND target.status = 'ACTIVE'
   AND target.end_date IS NULL
WHERE target.customer_id IS NULL;

COMMIT TRANSACTION;
"""


default_args = {
    "owner": "data-engineering",
    "start_date": datetime(2026, 10, 9),
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def data_validation_task():
    """Read the raw CSV, split invalid IDs from valid records, and save both."""
    storage_client = storage.Client(project=PROJECT_ID)

    source_blob = storage_client.bucket(SOURCE_BUCKET).blob(SOURCE_FILE)
    csv_bytes = source_blob.download_as_bytes()
    df = pd.read_csv(BytesIO(csv_bytes), keep_default_na=True)

    expected_columns = [
        "customer_id",
        "first_name",
        "last_name",
        "email",
        "phone",
        "city",
        "state",
        "country",
        "signup_date",
        "customer_status",
    ]
    missing_columns = [column for column in expected_columns if column not in df.columns]
    if missing_columns:
        raise ValueError(
            "The source CSV is missing required columns: "
            + ", ".join(missing_columns)
        )

    # Keep the expected schema and column order for downstream BigQuery loading.
    df = df[expected_columns].copy()

    customer_id = df["customer_id"].astype("string").str.strip()
    invalid_mask = customer_id.isna() | customer_id.eq("")
    invalid_df = df.loc[invalid_mask].copy()
    valid_df = df.loc[~invalid_mask].copy()

    # Upload both outputs, including a header-only invalid file if none are invalid.
    invalid_blob = storage_client.bucket(INVALID_BUCKET).blob(INVALID_FILE)
    invalid_blob.upload_from_string(
        invalid_df.to_csv(index=False).encode("utf-8"),
        content_type="text/csv",
    )

    valid_blob = storage_client.bucket(VALID_BUCKET).blob(VALID_FILE)
    valid_blob.upload_from_string(
        valid_df.to_csv(index=False).encode("utf-8"),
        content_type="text/csv",
    )

    print(f"Total input records : {len(df)}")
    print(f"Invalid records     : {len(invalid_df)}")
    print(f"Valid records       : {len(valid_df)}")
    print(f"Invalid output      : gs://{INVALID_BUCKET}/{INVALID_FILE}")
    print(f"Valid output        : gs://{VALID_BUCKET}/{VALID_FILE}")

    if valid_df.empty:
        raise ValueError(
            "No valid customer records were found. The BigQuery load was stopped."
        )


def load_csv_from_gcs():
    """Load the cleaned CSV into the BigQuery staging table."""
    bq_client = bigquery.Client(project=PROJECT_ID)

    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = bq_client.load_table_from_uri(
        GCS_URI,
        STAGE_TABLE,
        job_config=job_config,
        location=BIGQUERY_LOCATION,
    )
    load_job.result()

    print(f"Loaded {load_job.output_rows} rows from {GCS_URI} into {STAGE_TABLE}.")
    return load_job.output_rows or 0


def merge_customers_scd_type_2():
    """Expire changed active versions and insert new active dimension versions."""
    bq_client = bigquery.Client(project=PROJECT_ID)
    query_job = bq_client.query(
        MERGE_CUSTOMERS_SQL,
        job_config=bigquery.QueryJobConfig(use_legacy_sql=False),
        location=BIGQUERY_LOCATION,
    )
    query_job.result()

    affected_rows = int(query_job.num_dml_affected_rows or 0)
    print(
        f"SCD Type 2 processing completed for {STAGE_TABLE} -> {DIMENSION_TABLE}. "
        f"BigQuery reports {affected_rows} affected rows."
    )
    return affected_rows


with DAG(
    dag_id="etl_dag1",
    description="Validate customer CSV, load BigQuery staging, and update SCD Type 2 dimension",
    default_args=default_args,
    schedule=None,
    catchup=False,
    max_active_runs=1,
    tags=["ecommerce", "gcs", "bigquery", "scd-type-2"],
) as dag:
    validate_task = PythonOperator(
        task_id="data_validation_task",
        python_callable=data_validation_task,
    )

    load_stage_task = PythonOperator(
        task_id="gcs_to_bq_stage_job",
        python_callable=load_csv_from_gcs,
    )

    scd_type_2_task = PythonOperator(
        task_id="scd_type_2_merge_job",
        python_callable=merge_customers_scd_type_2,
    )

    validate_task >> load_stage_task >> scd_type_2_task
