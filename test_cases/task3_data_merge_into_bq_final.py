"""Apply SCD Type 2 changes from the customer staging table to the dimension."""

from google.cloud import bigquery

PROJECT_ID = "my-project-77-511616"
STAGE_TABLE = f"{PROJECT_ID}.ecommerce_stage_dataset.customer_stg"
DIMENSION_TABLE = f"{PROJECT_ID}.ecommerce_final_dataset.customer_dim"
BIGQUERY_LOCATION = "US"


MERGE_CUSTOMERS_SQL = f"""
MERGE `{DIMENSION_TABLE}` AS target
USING (
	WITH stage_latest AS (
		-- The stage schema has no ingestion timestamp, so duplicate customer IDs
		-- are resolved deterministically using the available source fields.
		SELECT
			customer_id,
			first_name,
			last_name,
			email,
			phone,
			city,
			state,
			age,
			gender,
			signup_date,
			customer_segment
		FROM `{STAGE_TABLE}`
		WHERE customer_id IS NOT NULL
			AND TRIM(customer_id) != ''
		QUALIFY ROW_NUMBER() OVER (
			PARTITION BY customer_id
			ORDER BY
				signup_date DESC,
				first_name,
				last_name,
				email,
				phone,
				city,
				state,
				age,
				gender,
				customer_segment
		) = 1
	),
	compared AS (
		SELECT
			source.*,
			existing.customer_id AS current_customer_id,
			existing.customer_id IS NOT NULL AND (
				source.first_name IS DISTINCT FROM existing.first_name
				OR source.last_name IS DISTINCT FROM existing.last_name
				OR source.email IS DISTINCT FROM existing.email
				OR source.phone IS DISTINCT FROM existing.phone
				OR source.city IS DISTINCT FROM existing.city
				OR source.state IS DISTINCT FROM existing.state
				OR source.age IS DISTINCT FROM existing.age
				OR source.gender IS DISTINCT FROM existing.gender
				OR source.signup_date IS DISTINCT FROM existing.signup_date
				OR source.customer_segment IS DISTINCT FROM existing.customer_segment
			) AS has_changes
		FROM stage_latest AS source
		LEFT JOIN `{DIMENSION_TABLE}` AS existing
			ON existing.customer_id = source.customer_id
			AND existing.status = 'ACTIVE'
			AND existing.end_date IS NULL
	),
	merge_rows AS (
		-- Match changed customers to their active target version to expire it.
		SELECT
			customer_id AS merge_key,
			'EXPIRE' AS operation,
			compared.* EXCEPT (current_customer_id, has_changes)
		FROM compared
		WHERE current_customer_id IS NOT NULL
			AND has_changes

		UNION ALL

		-- NULL merge keys ensure new/changed versions take the insert branch.
		SELECT
			CAST(NULL AS STRING) AS merge_key,
			'INSERT' AS operation,
			compared.* EXCEPT (current_customer_id, has_changes)
		FROM compared
		WHERE current_customer_id IS NULL
			 OR has_changes
	)
	SELECT * FROM merge_rows
) AS source
ON target.customer_id = source.merge_key
	AND target.status = 'ACTIVE'
	AND target.end_date IS NULL
WHEN MATCHED AND source.operation = 'EXPIRE' THEN
	UPDATE SET
		end_date = DATE_SUB(CURRENT_DATE('UTC'), INTERVAL 1 DAY),
		status = 'INACTIVE'
WHEN NOT MATCHED AND source.operation = 'INSERT' THEN
	INSERT (
		customer_id,
		first_name,
		last_name,
		email,
		phone,
		city,
		state,
		age,
		gender,
		signup_date,
		customer_segment,
		start_date,
		end_date,
		status
	)
	VALUES (
		source.customer_id,
		source.first_name,
		source.last_name,
		source.email,
		source.phone,
		source.city,
		source.state,
		source.age,
		source.gender,
		source.signup_date,
		source.customer_segment,
		CURRENT_DATE('UTC'),
		NULL,
		'ACTIVE'
	)
"""


def merge_customers_scd_type_2() -> int:
		"""Expire changed active customer versions and insert their new versions.

		New customers are inserted as ACTIVE. Unchanged customers are not modified.
		Returns the number of target rows inserted or updated by BigQuery.
		"""
		client = bigquery.Client(project=PROJECT_ID)
		job_config = bigquery.QueryJobConfig(use_legacy_sql=False)
		query_job = client.query(
				MERGE_CUSTOMERS_SQL,
				job_config=job_config,
				location=BIGQUERY_LOCATION,
		)
		query_job.result()

		affected_rows = int(query_job.num_dml_affected_rows or 0)
		print(
				f"SCD Type 2 merge completed for {STAGE_TABLE} -> {DIMENSION_TABLE}; "
				f"{affected_rows} dimension rows inserted or updated."
		)
		return affected_rows


if __name__ == "__main__":
		merge_customers_scd_type_2()
