output "environment_name" {
  description = "Name of the Cloud Composer environment"
  value       = google_composer_environment.environment1.name
}

output "environment_id" {
  description = "Full resource ID of the Cloud Composer environment"
  value       = google_composer_environment.environment1.id
}

output "airflow_uri" {
  description = "Web UI URI for the Airflow environment"
  value       = google_composer_environment.environment1.config[0].airflow_uri
}

output "dag_gcs_prefix" {
  description = "Cloud Storage path for DAGs"
  value       = google_composer_environment.environment1.config[0].dag_gcs_prefix
}