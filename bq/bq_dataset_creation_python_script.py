# give a python scirpt to create a dataset in my project
from google.cloud import bigquery

project_id = 'my-project-77-511616'
dataset_id = 'lct_interview_tracking'

client = bigquery.Client(project=project_id)

dataset_ref = client.dataset(dataset_id)
try:
    dataset = client.get_dataset(dataset_ref)
    print("Dataset {} already exists.".format(dataset_id))
except:
    dataset = bigquery.Dataset(dataset_ref)
    dataset = client.create_dataset(dataset)
    print("Dataset {} created.".format(dataset_id))