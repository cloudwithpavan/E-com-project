
# 3nd gen apache airflow managed environment creation on gcp cloud
resource "google_composer_environment" "environment1" {
  provider = google-beta

  name    = var.composer_environment_name
  region  = var.region
  project = var.project_id

  config {
    environment_size = var.environment_size

    software_config {
      image_version = var.image_version
    }

    workloads_config {
      scheduler {
        cpu        = 2
        memory_gb  = 2
        storage_gb = 2
        count      = 1
      }

      triggerer {
        count     = 1
        cpu       = 0.5
        memory_gb = 1.5
      }

      dag_processor {
        cpu        = 1
        memory_gb  = 2
        storage_gb = 1
        count      = 1
      }

      web_server {
        cpu        = 1
        memory_gb  = 2.5
        storage_gb = 2
      }

      worker {
        cpu        = 1
        memory_gb  = 2
        storage_gb = 2
        min_count  = 2
        max_count  = 4
      }
    }

    node_config {
      service_account = var.service_account
    }
  }
}
