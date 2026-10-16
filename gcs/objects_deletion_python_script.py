# i need like a python script which can delete the files from gcs bucket. I have written a script for that but it is not working. Can you please help me to fix the issue in the script.
from google.cloud import storage

project_id = 'my-project-77-511616'
bucket_name = 'bucket_raw_data'
client = storage.Client(project=project_id)

def delete_blob(bucket_name, blob_name, project_id=project_id):
    """Deletes a blob from the bucket."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(blob_name)
    blob.delete()

    print(
        "Blob {} deleted.".format(
            blob_name
        )
    )

# Example usage:
delete_blob(bucket_name, "destination-file.txt", project_id)

