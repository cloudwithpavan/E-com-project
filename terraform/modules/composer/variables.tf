variable "project_id" {
  description = "GCP project ID for the Composer environment"
  type        = string
}

variable "region" {
  description = "GCP region for the Composer environment"
  type        = string
}

variable "composer_environment_name" {
  description = "Cloud Composer environment name"
  type        = string
}

variable "environment_size" {
  description = "Cloud Composer environment size"
  type        = string
}

variable "image_version" {
  description = "Cloud Composer image version"
  type        = string
}

variable "service_account" {
  description = "Service account used by Composer worker nodes"
  type        = string
}