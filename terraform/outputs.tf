output "raw_bucket_name" {
  description = "Raw GCS bucket name"
  value       = module.gcs.raw_bucket_name
}

output "processed_bucket_name" {
  description = "Processed GCS bucket name"
  value       = module.gcs.processed_bucket_name
}

output "unprocessed_bucket_name" {
  description = "Unprocessed GCS bucket name"
  value       = module.gcs.unprocessed_bucket_name
}

output "stage_dataset_id" {
  description = "BigQuery staging dataset ID"
  value       = module.bigquery.stage_dataset_id
}

output "final_dataset_id" {
  description = "BigQuery final dataset ID"
  value       = module.bigquery.final_dataset_id
}

output "composer_environment_name" {
  description = "Cloud Composer environment name"
  value       = module.composer.environment_name
}

output "composer_environment_id" {
  description = "Cloud Composer environment resource ID"
  value       = module.composer.environment_id
}

output "composer_airflow_uri" {
  description = "Airflow web UI URI"
  value       = module.composer.airflow_uri
}

output "composer_dag_gcs_prefix" {
  description = "Cloud Storage path for Composer DAGs"
  value       = module.composer.dag_gcs_prefix
}

