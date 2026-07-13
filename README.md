# StraTistics

StraTistics is an end-to-end data engineering and analytics pipeline built to extract, load, transform, and analyze fitness data from Strava. 

## 🏗 Architecture & Data Flow

The project follows a standard Medallion Architecture (Bronze, Silver, Gold) powered by a modern data stack:

1. **Extraction & Loading (Ingestion):** Custom Python scripts interact with the Strava API and parse local fitness files (FIT, GPX, CSV) to extract activity data, loading it into a raw `bronze` schema in PostgreSQL.
2. **Orchestration:** Apache Airflow manages the scheduling and execution of data pipelines (DAGs), ensuring reliable incremental syncs and historical backfills.
3. **Transformation:** dbt (data build tool) handles the SQL transformation logic, cleaning the raw data into a `silver` staging layer (views), and finally aggregating it into `gold` marts and `metrics` (tables) ready for BI and reporting.
4. **Data Quality:** Great Expectations is integrated to ensure data integrity, validate pipeline outputs, and catch anomalies early.

## 🛠 Technology Stack

* **Database / Data Warehouse:** PostgreSQL 16
* **Orchestration:** Apache Airflow 2.9.1
* **Transformation:** dbt (dbt-postgres)
* **Data Quality:** Great Expectations
* **Ingestion/Scripts:** Python (Requests, Pandas, fitparse, gpxpy, psycopg2)
* **Infrastructure:** Docker & Docker Compose

## 📁 Project Structure

```text
StraTistics/
├── dags/               # Airflow DAGs for scheduling pipelines (e.g., strava_backfill, strava_incremental_sync)
├── dbt_strava/         # dbt project containing SQL transformation models (staging/silver, marts/gold, metrics)
├── ingestion/          # Python scripts for Strava API interaction, parsing local files, and loading to Postgres
├── quality/            # Great Expectations suite for data validation and checkpoints
├── init_bronze.sql     # Initial DDL script to create the 'bronze' schema and raw tables
├── docker-compose.yml  # Docker configuration to spin up Postgres and Airflow services locally
├── requirements.txt    # Python dependencies for the project
└── .env.example        # Example template for required environment variables
```

## ⚙️ Prerequisites

Before you begin, ensure you have the following installed:
* [Docker](https://docs.docker.com/get-docker/) and [Docker Compose](https://docs.docker.com/compose/install/)
* A Strava Developer Account with API credentials (Client ID, Client Secret, Refresh Token). You can create an application in your [Strava API Settings](https://www.strava.com/settings/api).

## 🚀 Setup Instructions

1. **Clone the repository** (if applicable) and navigate to the project root.

2. **Configure Environment Variables:**
   * Copy the example `.env` file to create your local `.env`:
     ```bash
     cp .env.example .env
     ```
   * Open the `.env` file and fill in your specific database credentials, Airflow settings, and your Strava API keys.

3. **Start the Infrastructure:**
   * Spin up the PostgreSQL database and Apache Airflow services in detached mode using Docker Compose:
     ```bash
     docker-compose up -d
     ```
   * *Note: Airflow initialization might take a minute or two on the first run.*

4. **Access the Airflow UI:**
   * Navigate to `http://localhost:8080` in your web browser.
   * Log in using the default credentials defined in your docker-compose setup (Username: `admin`, Password: `admin`).

## 🏃 Running the Pipeline

1. **Initialize the Data Warehouse:** Ensure the `init_bronze.sql` script has been executed against your PostgreSQL database to create the necessary schemas and raw tables.
2. **Initial Load (Backfill):** Trigger the `strava_backfill` DAG in the Airflow UI to extract your historical data from Strava and populate the `bronze` layer.
3. **Transformations (dbt):** The dbt models handle the transformation from `bronze` -> `silver` -> `gold`. Depending on your DAG configuration, these run automatically after ingestion or can be run manually via the dbt CLI inside the `dbt_strava` directory (`dbt run`).
4. **Incremental Sync:** Enable the `strava_incremental_sync` DAG in Airflow to run on a set schedule, automatically fetching only newly completed activities.

## 🛡️ Data Quality Validation

Great Expectations suites are located in the `quality/` directory. You can run validations against the loaded data to ensure everything meets your defined data contracts using the provided scripts (e.g., `python quality/run_validations.py`).

## 🧹 Maintenance

* **Logs:** Airflow and dbt generate logs. Ensure these directories (`logs/`, `dbt_strava/logs/`) are added to your `.gitignore` to keep your repository clean.
* **Teardown:** To stop the services and remove containers, run:
  ```bash
  docker-compose down
  ```
