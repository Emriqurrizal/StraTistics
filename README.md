# StraTistics

StraTistics is an end-to-end data engineering and analytics pipeline built to extract, load, transform, and analyze running data from Strava. 

## Architecture & Data Flow

The project follows a standard Medallion Architecture (Bronze, Silver, Gold) powered by a modern serverless data stack:

1. **Extraction & Loading (Ingestion):** Custom Python scripts interact with the Strava API to extract activity data, loading it into a raw `bronze` schema in a serverless Neon DB.
2. **Orchestration:** GitHub Actions manages the scheduling and execution of data pipelines via CRON and manual triggers, ensuring reliable incremental syncs and historical backfills without any local infrastructure.
3. **Transformation:** dbt (data build tool) handles the SQL transformation logic, cleaning the raw data into a `silver` staging layer (views), and finally aggregating it into `gold` marts and `metrics` (tables) ready for BI and reporting.
4. **Data Quality:** Great Expectations is integrated to ensure data integrity, validate pipeline outputs, and catch anomalies early.

## Technology Stack

* **Database / Data Warehouse:** Neon DB (Serverless PostgreSQL)
* **Orchestration:** GitHub Actions
* **Transformation:** dbt (dbt-postgres)
* **Data Quality:** Great Expectations
* **Ingestion/Scripts:** Python (Requests, Pandas, fitparse, gpxpy, psycopg2)

## Project Structure

```text
StraTistics/
├── .github/workflows/  # GitHub Actions workflows for scheduling pipelines (e.g., strava_backfill, strava_incremental_sync)
├── dbt_strava/         # dbt project containing SQL transformation models (staging/silver, marts/gold, metrics)
├── ingestion/          # Python scripts for Strava API interaction, parsing local files, and loading to Postgres
├── quality/            # Great Expectations suite for data validation and checkpoints
├── requirements.txt    # Python dependencies for the project
└── .env.example        # Example template for required environment variables
```

## Prerequisites

Before you begin, ensure you have the following:
* A [Neon DB](https://neon.tech/) serverless PostgreSQL database.
* A Strava Developer Account (requires subscription) with API credentials (Client ID, Client Secret, Refresh Token). You can create an application in your [Strava API Settings](https://www.strava.com/settings/api).

## Setup Instructions

Since this pipeline runs entirely on GitHub Actions, you do not need to run anything locally.

1. **Configure GitHub Secrets:**
   Navigate to your repository on GitHub -> **Settings** -> **Secrets and variables** -> **Actions** and add the following repository secrets based on the `.env.example` file:
   * `POSTGRES_USER`
   * `POSTGRES_PASSWORD`
   * `POSTGRES_HOST`
   * `STRAVA_CLIENT_ID`
   * `STRAVA_CLIENT_SECRET`
   * `STRAVA_REFRESH_TOKEN`

## Running the Pipeline

1. **Initialize the Data Warehouse:** The `bronze` schema and raw tables will be automatically created on your database the first time the Python ingestion scripts run.
2. **Initial Load (Backfill):** Navigate to the **Actions** tab in your GitHub repository, select the **Strava Backfill** workflow, and click **Run workflow** to extract your historical data from Strava and populate the `bronze` layer.
3. **Transformations (dbt):** The dbt models handle the transformation from `bronze` -> `silver` -> `gold`. These run automatically as part of the GitHub Action workflows immediately after ingestion.
4. **Incremental Sync:** The **Strava Incremental Sync** workflow is automatically scheduled to run daily at 2:00 AM UTC via GitHub Actions cron, automatically fetching only newly completed activities.

## Data Quality Validation

Great Expectations suites are located in the `quality/` directory. These validations run automatically as step 2 of every GitHub Action workflow. If data fails validation, the workflow will fail, alerting you to the anomaly.
