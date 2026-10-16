# give a python script to upload a file to gcs bucket

from google.cloud import storage

project_id = 'my-project-77-511616'
bucket_name = 'bucket_raw_data'
file_name = "C:\\gcp_de_b55\\data\\customers.csv"
destination_blob_name = "customers.csv"

def upload_blob(bucket_name, source_file_name, destination_blob_name, project_id=project_id):
    """Uploads a file to the bucket."""
    storage_client = storage.Client(project=project_id)
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)

    blob.upload_from_filename(source_file_name)

    print(
        "File {} uploaded to {}.".format(
            source_file_name, destination_blob_name
        )
    )

# Example usage:
upload_blob(bucket_name, file_name, "destination-file.txt", project_id)