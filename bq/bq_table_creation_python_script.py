# need to create table having customer_id, name, contact_number, created_at, updated_at columns in bigquery using python script
from google.cloud import bigquery

project_id = 'my-project-77-511616'
dataset_id = 'lct_interview_tracking'
table_id = 'customers'

client = bigquery.Client(project=project_id)
dataset_ref = client.dataset(dataset_id)
table_ref = dataset_ref.table(table_id) 

schema = [
    bigquery.SchemaField("customer_id", "STRING", mode="REQUIRED"), 
    bigquery.SchemaField("name", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("contact_number", "STRING", mode="REQUIRED"),
    bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
    bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
]

# table creation

table = bigquery.Table(table_ref, schema=schema)
table = client.create_table(table)
print("Table {} created.".format(table_id)) 
