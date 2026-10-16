variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "dataset_location" {
  description = "Location for the BigQuery datasets"
  type        = string
}

variable "stage_dataset_id" {
  description = "Stage dataset ID"
  type        = string
}

variable "stage_table_id" {
  description = "Stage table ID"
  type        = string
}

variable "final_dataset_id" {
  description = "Final dataset ID"
  type        = string
}

variable "final_table_id" {
  description = "Final table ID"
  type        = string
}

variable "labels" {
  description = "Labels for the BigQuery resources"
  type        = map(string)
  default     = {}
}
