resource "google_bigquery_dataset" "stage_dataset" {
  dataset_id                  = var.stage_dataset_id
  description                 = "Staging dataset for raw data"
  location                    = var.dataset_location
  default_table_expiration_ms = 3600000
  labels                      = var.labels
}

resource "google_bigquery_dataset" "final_dataset" {
  dataset_id                  = var.final_dataset_id
  description                 = "Curated customer dimension dataset"
  location                    = var.dataset_location
  default_table_expiration_ms = 3600000
  labels                      = var.labels
}

resource "google_bigquery_table" "stage_table1" {
  dataset_id = google_bigquery_dataset.stage_dataset.dataset_id
  table_id   = var.stage_table_id

  deletion_protection = false
  labels              = var.labels

  schema = <<EOF
[
  {
    "mode": "NULLABLE",
    "name": "customer_id",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "first_name",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "last_name",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "email",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "phone",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "city",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "state",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "age",
    "type": "INTEGER"
  },
  {
    "mode": "NULLABLE",
    "name": "gender",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "signup_date",
    "type": "DATE"
  },
  {
    "mode": "NULLABLE",
    "name": "customer_segment",
    "type": "STRING"
  }
]
EOF
}


resource "google_bigquery_table" "final_table1" {
  dataset_id = google_bigquery_dataset.final_dataset.dataset_id
  table_id   = var.final_table_id

  deletion_protection = false
  labels              = var.labels

  schema = <<EOF
[
  {
    "mode": "NULLABLE",
    "name": "customer_id",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "first_name",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "last_name",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "email",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "phone",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "city",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "state",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "age",
    "type": "INTEGER"
  },
  {
    "mode": "NULLABLE",
    "name": "gender",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "signup_date",
    "type": "DATE"
  },
  {
    "mode": "NULLABLE",
    "name": "customer_segment",
    "type": "STRING"
  },
  {
    "mode": "NULLABLE",
    "name": "start_date",
    "type": "DATE",
    "description": "Date this customer dimension version became effective"
  },
  {
    "mode": "NULLABLE",
    "name": "end_date",
    "type": "DATE",
    "description": "Date this customer dimension version ceased to be effective; NULL for the current version"
  },
  {
    "mode": "REQUIRED",
    "name": "status",
    "type": "STRING",
    "description": "SCD Type 2 version status, such as ACTIVE or INACTIVE"
  }
]
EOF
}

