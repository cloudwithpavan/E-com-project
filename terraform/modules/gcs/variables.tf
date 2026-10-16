variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
}

variable "bucket_location" {
  description = "Location for the GCS buckets"
  type        = string
}

variable "raw_bucket_name" {
  description = "Raw bucket name"
  type        = string
}

variable "processed_bucket_name" {
  description = "Processed bucket name"
  type        = string
}

variable "unprocessed_bucket_name" {
  description = "Unprocessed bucket name"
  type        = string
}

variable "labels" {
  description = "Labels for the buckets"
  type        = map(string)
  default     = {}
}
