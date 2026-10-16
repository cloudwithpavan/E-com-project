from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta
import pandas as pd
from google.cloud import storage
from io import BytesIO
from google.cloud import bigquery



# variables section 
# GCS paths
PROJECT_ID = "my-project-77-511616"

SOURCE_BUCKET = "ecommerce-analytics-raw-lct2026"
SOURCE_FILE = "customer_data_10_records.csv"

INVALID_BUCKET = "ecommerce-analytics-unprocessed-lct2026"
VALID_BUCKET = "ecommerce-analytics-cleaned-lct2026"

INVALID_FILE = "customer_data_invalid.csv"
VALID_FILE = "customer_data_valid.csv"

PROJECT_ID = "retail-omkar-cli-org-dev"
TABLE_ID = f"{PROJECT_ID}.ecommerce_stage_dataset.customer_stg"
GCS_URI = "gs://ecommerce-analytics-cleaned-lct2026/customer_data_valid.csv"

PROJECT_ID = "retail-omkar-cli-org-dev"
STAGE_TABLE = f"{PROJECT_ID}.ecommerce_stage_dataset.customer_stg"
DIMENSION_TABLE = f"{PROJECT_ID}.ecommerce_final_dataset.customer_dim"
BIGQUERY_LOCATION = "US"


SCHEMA = [
    bigquery.SchemaField("customer_id", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("first_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("last_name", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("email", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("phone", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("city", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("state", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("age", "INTEGER", mode="NULLABLE"),
    bigquery.SchemaField("gender", "STRING", mode="NULLABLE"),
    bigquery.SchemaField("signup_date", "DATE", mode="NULLABLE"),
    bigquery.SchemaField("customer_segment", "STRING", mode="NULLABLE"),
]


MERGE_CUSTOMERS_SQL = f"""
MERGE `{DIMENSION_TABLE}` AS target
USING (
	WITH stage_latest AS (
		-- The stage schema has no ingestion timestamp, so duplicate customer IDs
		-- are resolved deterministically using the available source fields.
		SELECT
			customer_id,
			first_name,
			last_name,
			email,
			phone,
			city,
			state,
			age,
			gender,
			signup_date,
			customer_segment
		FROM `{STAGE_TABLE}`
		WHERE customer_id IS NOT NULL
			AND TRIM(customer_id) != ''
		QUALIFY ROW_NUMBER() OVER (
			PARTITION BY customer_id
			ORDER BY
				signup_date DESC,
				first_name,
				last_name,
				email,
				phone,
				city,
				state,
				age,
				gender,
				customer_segment
		) = 1
	),
	compared AS (
		SELECT
			source.*,
			existing.customer_id AS current_customer_id,
			existing.customer_id IS NOT NULL AND (
				source.first_name IS DISTINCT FROM existing.first_name
				OR source.last_name IS DISTINCT FROM existing.last_name
				OR source.email IS DISTINCT FROM existing.email
				OR source.phone IS DISTINCT FROM existing.phone
				OR source.city IS DISTINCT FROM existing.city
				OR source.state IS DISTINCT FROM existing.state
				OR source.age IS DISTINCT FROM existing.age
				OR source.gender IS DISTINCT FROM existing.gender
				OR source.signup_date IS DISTINCT FROM existing.signup_date
				OR source.customer_segment IS DISTINCT FROM existing.customer_segment
			) AS has_changes
		FROM stage_latest AS source
		LEFT JOIN `{DIMENSION_TABLE}` AS existing
			ON existing.customer_id = source.customer_id
			AND existing.status = 'ACTIVE'
			AND existing.end_date IS NULL
	),
	merge_rows AS (
		-- Match changed customers to their active target version to expire it.
		SELECT
			customer_id AS merge_key,
			'EXPIRE' AS operation,
			compared.* EXCEPT (current_customer_id, has_changes)
		FROM compared
		WHERE current_customer_id IS NOT NULL
			AND has_changes

		UNION ALL

		-- NULL merge keys ensure new/changed versions take the insert branch.
		SELECT
			CAST(NULL AS STRING) AS merge_key,
			'INSERT' AS operation,
			compared.* EXCEPT (current_customer_id, has_changes)
		FROM compared
		WHERE current_customer_id IS NULL
			 OR has_changes
	)
	SELECT * FROM merge_rows
) AS source
ON target.customer_id = source.merge_key
	AND target.status = 'ACTIVE'
	AND target.end_date IS NULL
WHEN MATCHED AND source.operation = 'EXPIRE' THEN
	UPDATE SET
		end_date = DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 1 DAY),
		status = 'INACTIVE'
WHEN NOT MATCHED AND source.operation = 'INSERT' THEN
	INSERT (
		customer_id,
		first_name,
		last_name,
		email,
		phone,
		city,
		state,
		age,
		gender,
		signup_date,
		customer_segment,
		start_date,
		end_date,
		status
	)
	VALUES (
		source.customer_id,
		source.first_name,
		source.last_name,
		source.email,
		source.phone,
		source.city,
		source.state,
		source.age,
		source.gender,
		source.signup_date,
		source.customer_segment,
		CURRENT_DATE('UTC'),
		NULL,
		'ACTIVE'
	)
"""

default_args = {
    'start_date' : datetime(2026,10,9),
    'retries' : 2,
    'retry_delay' : timedelta(minutes=2)
}



# python logic / unit 
def data_validation_task():
    # Create GCS client (uses Application Default Credentials)
    client = storage.Client(project=PROJECT_ID)

    # 1. Read source CSV from the raw bucket
    source_blob = client.bucket(SOURCE_BUCKET).blob(SOURCE_FILE)
    csv_bytes = source_blob.download_as_bytes()

    # keep_default_na=True interprets empty CSV fields as NaN
    df = pd.read_csv(BytesIO(csv_bytes), keep_default_na=True)

    # 2. Validate the primary key: customer_id must not be NULL or blank
    if "customer_id" not in df.columns:
        raise ValueError("Required column 'customer_id' is missing from the CSV.")

    customer_id = df["customer_id"].astype("string").str.strip()
    invalid_mask = customer_id.isna() | customer_id.eq("")
    invalid_df = df.loc[invalid_mask].copy()
    valid_df = df.loc[~invalid_mask].copy()

    # 3. Convert dataframes to CSV bytes
    invalid_bytes = invalid_df.to_csv(index=False).encode("utf-8")
    valid_bytes = valid_df.to_csv(index=False).encode("utf-8")

    # 4. Upload invalid records to the unprocessed bucket
    invalid_blob = client.bucket(INVALID_BUCKET).blob(INVALID_FILE)
    invalid_blob.upload_from_string(invalid_bytes, content_type="text/csv")

    # 5. Upload valid records to the cleaned bucket
    valid_blob = client.bucket(VALID_BUCKET).blob(VALID_FILE)
    valid_blob.upload_from_string(valid_bytes, content_type="text/csv")

    # 6. Print reconciliation counts
    print(f"Total input records : {len(df)}")
    print(f"Invalid records     : {len(invalid_df)}")
    print(f"Valid records       : {len(valid_df)}")
    print("Invalid output      : gs://" + INVALID_BUCKET + "/" + INVALID_FILE)
    print("Valid output        : gs://" + VALID_BUCKET + "/" + VALID_FILE)



# data load job 

# need python script to load csv file from gcs to bigquery table

def load_csv_from_gcs():
    """Load the configured GCS CSV into the BigQuery staging table.

    The existing staging table is overwritten each time this script runs.
    Returns the number of rows loaded by the BigQuery job.
    """
    client = bigquery.Client(project=PROJECT_ID)
    job_config = bigquery.LoadJobConfig(
        schema=SCHEMA,
        skip_leading_rows=1,
        source_format=bigquery.SourceFormat.CSV,
        write_disposition=bigquery.WriteDisposition.WRITE_TRUNCATE,
    )

    load_job = client.load_table_from_uri(
        GCS_URI,
        TABLE_ID,
        job_config=job_config,
    )
    load_job.result()

    print(f"Loaded {load_job.output_rows} rows from {GCS_URI} into {TABLE_ID}.")
    return load_job.output_rows or 0


def merge_customers_scd_type_2():
		"""Expire changed active customer versions and insert their new versions.

		New customers are inserted as ACTIVE. Unchanged customers are not modified.
		Returns the number of target rows inserted or updated by BigQuery.
		"""
		client = bigquery.Client(project=PROJECT_ID)
		job_config = bigquery.QueryJobConfig(use_legacy_sql=False)
		query_job = client.query(
				MERGE_CUSTOMERS_SQL,
				job_config=job_config,
				location=BIGQUERY_LOCATION,
		)
		query_job.result()

		affected_rows = int(query_job.num_dml_affected_rows or 0)
		print(
				f"SCD Type 2 merge completed for {STAGE_TABLE} -> {DIMENSION_TABLE}; "
				f"{affected_rows} dimension rows inserted or updated."
		)
		return affected_rows

    
with DAG(
    dag_id='etl_dag1',
    default_args=default_args,
    schedule=None,
    catchup=False 
) as dag:
    
    task_1 = PythonOperator(
        task_id='data_validation_task',
        python_callable=data_validation_task    
    )
    
    
    task_2 = PythonOperator(
        task_id='gcs_to_bq_stage_job',
        python_callable=load_csv_from_gcs    
    )

    task_3 = PythonOperator(
        task_id='scd_type_2_merge_job',
        python_callable=merge_customers_scd_type_2
    )
    
    
    
    task_1 >> task_2 >> task_3