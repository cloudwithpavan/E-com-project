# i would like to move the files from one bucket to another bucket in gcs using python script. I have written a script for that but it is not working. Can you please help me to fix the issue in the script.
from google.cloud import storage

project_id = 'my-project-77-511616'
source_bucket_name = 'lavu-cloud-tech-bckt-789'
destination_bucket_name = 'lavu-cloud-tech-bckt-567'
file_name = 'destination-file.txt'

def move_blob(source_bucket_name, destination_bucket_name, blob_name, project_id=project_id):
    """Moves a blob from one bucket to another with a new name."""
    storage_client = storage.Client(project=project_id)

    source_bucket = storage_client.bucket(source_bucket_name)
    destination_bucket = storage_client.bucket(destination_bucket_name)

    blob = source_bucket.blob(blob_name)
    new_blob = source_bucket.copy_blob(blob, destination_bucket, blob_name)
    source_bucket.delete_blob(blob_name)

    print(
        "Blob {} in bucket {} moved to blob {} in bucket {}.".format(
            blob_name, source_bucket_name, new_blob.name, destination_bucket_name
        )
    )

# Example usage:
move_blob(source_bucket_name, destination_bucket_name, file_name, project_id)

