# need python script to load csv file from gcs to bigquery table

from google.cloud import bigquery

PROJECT_ID = "my-project-77-511616"
TABLE_ID = f"{PROJECT_ID}.ecommerce_stage_dataset.stage_table1"
GCS_URI = "gs://ecommerce-analytics-cleaned-lct2026/customer_data_valid.csv"


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


def load_csv_from_gcs() -> int:
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


if __name__ == "__main__":
    load_csv_from_gcs()