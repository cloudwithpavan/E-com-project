# i want to delete a bucket 
from google.cloud import storage

project_id = 'my-project-77-511616'
bucket_name = 'bucket_raw_data'
client = storage.Client(project=project_id)

def delete_bucket(bucket_name, project_id=project_id):
    """Deletes a bucket from GCS."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    bucket.delete()

    print(
        "Bucket {} deleted.".format(
            bucket_name
        )
    )

# Example usage:
delete_bucket(bucket_name, project_id)
