resource "google_storage_bucket" "raw_data_bucket" {
  name     = var.raw_bucket_name
  location = var.bucket_location
  project  = var.project_id

  force_destroy               = true
  uniform_bucket_level_access = true
  labels                      = var.labels

  lifecycle_rule {
    condition {
      age = 3
    }

    action {
      type = "Delete"
    }
  }

  lifecycle_rule {
    condition {
      age = 1
    }

    action {
      type = "AbortIncompleteMultipartUpload"
    }
  }
}

resource "google_storage_bucket" "processed_data_bucket" {
  name     = var.processed_bucket_name
  location = var.bucket_location
  project  = var.project_id

  force_destroy               = true
  uniform_bucket_level_access = true
  labels                      = var.labels
}

resource "google_storage_bucket" "unprocessed_data_bucket" {
  name     = var.unprocessed_bucket_name
  location = var.bucket_location
  project  = var.project_id

  force_destroy               = true
  uniform_bucket_level_access = true
  labels                      = var.labels
}
