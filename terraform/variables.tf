# ======================================================
# GLOBAL PROJECT VARIABLES
# ======================================================

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "environment" {
  description = "Deployment environment name"
  type        = string
  default     = "dev"
}

variable "common_labels" {
  description = "Common labels applied to GCP resources"
  type        = map(string)
  default = {
    environment = "dev"
    managed_by  = "terraform"
  }
}

# ======================================================
# GCS BUCKET VARIABLES
# ======================================================

variable "bucket_location" {
  description = "Location for all GCS buckets"
  type        = string
  default     = "US"
}

variable "raw_bucket_name" {
  description = "Name of the GCS raw bucket"
  type        = string
}

variable "processed_data_bucket" {
  description = "Name of the GCS processed bucket"
  type        = string
}

variable "unprocessed_data_bucket" {
  description = "Name of the GCS rejected/unprocessed bucket"
  type        = string
}

# ======================================================
# BIGQUERY VARIABLES
# ======================================================

variable "bigquery_location" {
  description = "Location for BigQuery datasets"
  type        = string
  default     = "US"
}

variable "raw_ds_location" {
  description = "Deprecated alias for bigquery_location"
  type        = string
  default     = "US"
}

variable "final_ds_location" {
  description = "Deprecated alias for bigquery_location"
  type        = string
  default     = "US"
}

variable "raw_dataset" {
  description = "BigQuery stage dataset ID"
  type        = string
}

variable "table_name" {
  description = "BigQuery stage table ID"
  type        = string
}

variable "final_dataset" {
  description = "BigQuery final dataset ID"
  type        = string
}

variable "final_table_name" {
  description = "BigQuery final table ID"
  type        = string
}

# ======================================================
# COMPOSER VARIABLES
# ======================================================

variable "composer_environment_name" {
  description = "Cloud Composer environment name"
  type        = string
}

variable "composer_environment_size" {
  description = "Cloud Composer environment size"
  type        = string
}

variable "composer_image_version" {
  description = "Cloud Composer image version"
  type        = string
}

variable "composer_service_account" {
  description = "Service account used by Composer worker nodes"
  type        = string
}

