terraform {
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 7.43"
    }
    google-beta = {
      source  = "hashicorp/google-beta"
      version = "~> 7.43"
    }
  }
}

provider "google" {
  project = var.project_id
  region  = var.region
}

module "gcs" {
  source = "./modules/gcs"

  project_id              = var.project_id
  region                  = var.region
  bucket_location         = var.bucket_location
  raw_bucket_name         = var.raw_bucket_name
  processed_bucket_name   = var.processed_data_bucket
  unprocessed_bucket_name = var.unprocessed_data_bucket
  labels                  = var.common_labels
}

module "bigquery" {
  source = "./modules/bigquery"

  project_id       = var.project_id
  dataset_location = var.bigquery_location
  stage_dataset_id = var.raw_dataset
  stage_table_id   = var.table_name
  final_dataset_id = var.final_dataset
  final_table_id   = var.final_table_name
  labels           = var.common_labels
}

module "composer" {
  source = "./modules/composer"

  providers = {
    google-beta = google-beta
  }

  project_id                = var.project_id
  region                    = var.region
  composer_environment_name = var.composer_environment_name
  environment_size          = var.composer_environment_size
  image_version             = var.composer_image_version
  service_account           = var.composer_service_account
}

moved {
  from = google_storage_bucket.raw_data_bucket
  to   = module.gcs.google_storage_bucket.raw_data_bucket
}

moved {
  from = google_storage_bucket.processed_data_bucket
  to   = module.gcs.google_storage_bucket.processed_data_bucket
}

moved {
  from = google_storage_bucket.unprocessed_data_bucket
  to   = module.gcs.google_storage_bucket.unprocessed_data_bucket
}

moved {
  from = google_bigquery_dataset.dataset1
  to   = module.bigquery.google_bigquery_dataset.stage_dataset
}

moved {
  from = google_bigquery_dataset.dataset2
  to   = module.bigquery.google_bigquery_dataset.final_dataset
}

moved {
  from = google_bigquery_table.raw_table
  to   = module.bigquery.google_bigquery_table.stage_table
}

moved {
  from = google_bigquery_table.final_table
  to   = module.bigquery.google_bigquery_table.final_table
}
