output "stage_dataset_id" {
  description = "Stage dataset ID"
  value       = google_bigquery_dataset.stage_dataset.dataset_id
}

output "final_dataset_id" {
  description = "Final dataset ID"
  value       = google_bigquery_dataset.final_dataset.dataset_id
}

output "stage_table_id" {
  description = "Stage table ID"
  value       = google_bigquery_table.stage_table1.table_id
}

output "final_table_id" {
  description = "Final table ID"
  value       = google_bigquery_table.final_table1.table_id
}
