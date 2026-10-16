output "raw_bucket_name" {
  description = "Name of the raw GCS bucket"
  value       = google_storage_bucket.raw_data_bucket.name
}

output "processed_bucket_name" {
  description = "Name of the processed GCS bucket"
  value       = google_storage_bucket.processed_data_bucket.name
}

output "unprocessed_bucket_name" {
  description = "Name of the unprocessed GCS bucket"
  value       = google_storage_bucket.unprocessed_data_bucket.name
}

output "raw_bucket_url" {
  description = "URL of the raw GCS bucket"
  value       = google_storage_bucket.raw_data_bucket.url
}
