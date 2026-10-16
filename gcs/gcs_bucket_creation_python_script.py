# This python script is for creating a bucket on the gcp cloud 

# to create a bucket requirement

# organisational account / folders (optional) / project / billing enabled 

# bucket_name / location / storage class and etc 

# imports section
from google.cloud import storage # libraries - methods / client - bq - storage - service 

# variable declaration
project_id = 'my-project-77-511616' 
bucket_name = 'bucket_raw_data'
location = 'US'

def create_bucket_class_location(bucket_name,project_id,location):
    """
    Create a new bucket in the US region with the coldline storage
    class
    """ 

    storage_client = storage.Client(project=project_id)

    bucket = storage_client.bucket(bucket_name)
    bucket.storage_class = "COLDLINE"
    new_bucket = storage_client.create_bucket(bucket, location=location)

    print(
        "Created bucket {} in {} with storage class {}".format(
            new_bucket.name, new_bucket.location, new_bucket.storage_class
        )
    )
    return new_bucket

create_bucket_class_location(bucket_name,project_id,location)


