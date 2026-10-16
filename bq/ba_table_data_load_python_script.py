# i need to load the csv file data into bigquery table using python script. I have written a script for that but it is not working. Can you please help me to fix the issue in the script.
from google.cloud import bigquery

project_id = 'retail-omkar-cli-org-dev'
dataset_id = 'lct_interview_tracking'
table_id = 'customers'

client = bigquery.Client(project=project_id)
dataset_ref = client.dataset(dataset_id)
table_ref = dataset_ref.table(table_id)

# give object address of the csv file in gcs bucket
object_address = "gs://lavu-cloud-tech-bckt-789/destination-file.txt"

schema = [
    bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"), 
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("contact_number", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
]

# make it like a function
def load_data_from_gcs_to_bigquery(object_address, table_ref, schema):
    # load job configuration
    job_config = bigquery.LoadJobConfig(
        source_format=bigquery.SourceFormat.CSV,
        skip_leading_rows=1,
        schema=schema,
        write_disposition=bigquery.WriteDisposition.WRITE_APPEND
    )

    # load data from csv file in gcs bucket to bigquery table
    load_job = client.load_table_from_uri(
        object_address,
        table_ref,
        job_config=job_config,
    )

    # wait for the load job to complete
    load_job.result()

    # print the number of rows loaded into the table
    destination_table = client.get_table(table_ref)
    print(f"Rows loaded: {destination_table.num_rows}")


# Example usage:
load_data_from_gcs_to_bigquery(object_address, table_ref, schema)



