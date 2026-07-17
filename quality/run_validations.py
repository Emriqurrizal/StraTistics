import os
import sys
import json
import pandas as pd
import psycopg2
import great_expectations as gx

# Suppress warnings
import warnings
warnings.filterwarnings('ignore')

def get_db_connection():
    return psycopg2.connect(
        host=os.getenv("POSTGRES_HOST"),
        port=os.getenv("POSTGRES_PORT", "5432"),
        dbname=os.getenv("POSTGRES_DB", "neondb"),
        user=os.getenv("POSTGRES_USER"),
        password=os.getenv("POSTGRES_PASSWORD"),
        sslmode=os.getenv("POSTGRES_SSLMODE", "require")
    )

def run_suite(df, suite_path):
    with open(suite_path, 'r') as f:
        suite_dict = json.load(f)
    
    ge_df = gx.from_pandas(df)
    results = ge_df.validate(expectation_suite=suite_dict)
    return results

def main():
    try:
        conn = get_db_connection()
    except Exception as e:
        print(f"Failed to connect to database: {e}")
        sys.exit(1)
        
    # 1. Bronze Suite
    print("\n--- Running Bronze Suite ---")
    try:
        bronze_df = pd.read_sql("SELECT * FROM bronze.raw_activities", conn)
        bronze_results = run_suite(bronze_df, "quality/expectations/bronze_suite.json")
        
        if not bronze_results["success"]:
            print("Bronze Suite: FAILED")
            for result in bronze_results['results']:
                if not result['success']:
                    print(f"  Failed Expectation: {result['expectation_config']['expectation_type']} on {result['expectation_config']['kwargs'].get('column')}")
            # We don't exit immediately so we can see silver results too
            bronze_success = False
        else:
            print("Bronze Suite: PASSED")
            bronze_success = True
    except Exception as e:
        print(f"Error running Bronze Suite: {e}")
        bronze_success = False
        
    # 2. Silver Suite
    print("\n--- Running Silver Suite ---")
    try:
        silver_df = pd.read_sql("SELECT * FROM public_silver.stg_activities", conn)
        silver_results = run_suite(silver_df, "quality/expectations/silver_suite.json")
        
        if not silver_results["success"]:
            print("Silver Suite: FAILED")
            for result in silver_results['results']:
                if not result['success']:
                    print(f"  Failed Expectation: {result['expectation_config']['expectation_type']} on {result['expectation_config']['kwargs'].get('column')}")
            silver_success = False
        else:
            print("Silver Suite: PASSED")
            silver_success = True
    except Exception as e:
        print(f"Error running Silver Suite: {e}")
        silver_success = False
            
    conn.close()
    
    print("\n--- Summary ---")
    if bronze_success and silver_success:
        print("All Data Quality Checks PASSED!")
        sys.exit(0)
    else:
        print("Some Data Quality Checks FAILED. Please review the logs above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
