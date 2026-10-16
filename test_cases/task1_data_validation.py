import csv
from google.cloud import storage
from io import StringIO

# GCS paths
PROJECT_ID = "my-project-77-511616"

SOURCE_BUCKET = "ecommerce-analytics-raw-lct2026"
SOURCE_FILE = "customer_data_10_records.csv"

INVALID_BUCKET = "ecommerce-analytics-unprocessed-lct2026"
VALID_BUCKET = "ecommerce-analytics-cleaned-lct2026"

INVALID_FILE = "customer_data_invalid.csv"
VALID_FILE = "customer_data_valid.csv"


def main():
    # Create GCS client (uses Application Default Credentials)
    client = storage.Client(project=PROJECT_ID)

    # 1. Read source CSV from the raw bucket
    source_blob = client.bucket(SOURCE_BUCKET).blob(SOURCE_FILE)
    csv_bytes = source_blob.download_as_bytes()

    # 2. Validate the primary key: customer_id must not be NULL or blank
    rows = list(csv.reader(StringIO(csv_bytes.decode("utf-8-sig"))))
    if not rows or "customer_id" not in rows[0]:
        raise ValueError("Required column 'customer_id' is missing from the CSV.")

    headers = rows[0]
    customer_id_index = headers.index("customer_id")
    data_rows = rows[1:]
    invalid_rows = [
        row for row in data_rows
        if customer_id_index >= len(row) or not row[customer_id_index].strip()
    ]
    valid_rows = [
        row for row in data_rows
        if customer_id_index < len(row) and row[customer_id_index].strip()
    ]

    def to_csv_bytes(records):
        output = StringIO(newline="")
        writer = csv.writer(output)
        writer.writerow(headers)
        writer.writerows(records)
        return output.getvalue().encode("utf-8")

    # 3. Convert dataframes to CSV bytes
    invalid_bytes = to_csv_bytes(invalid_rows)
    valid_bytes = to_csv_bytes(valid_rows)

    # 4. Upload invalid records to the unprocessed bucket
    invalid_blob = client.bucket(INVALID_BUCKET).blob(INVALID_FILE)
    invalid_blob.upload_from_string(invalid_bytes, content_type="text/csv")

    # 5. Upload valid records to the cleaned bucket
    valid_blob = client.bucket(VALID_BUCKET).blob(VALID_FILE)
    valid_blob.upload_from_string(valid_bytes, content_type="text/csv")

    # 6. Print reconciliation counts
    print(f"Total input records : {len(data_rows)}")
    print(f"Invalid records     : {len(invalid_rows)}")
    print(f"Valid records       : {len(valid_rows)}")
    print("Invalid output      : gs://" + INVALID_BUCKET + "/" + INVALID_FILE)
    print("Valid output        : gs://" + VALID_BUCKET + "/" + VALID_FILE)


if __name__ == "__main__":
    main()