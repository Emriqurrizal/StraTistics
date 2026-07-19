import sys
sys.path.append(r'C:\Users\Emriqurrizal\Documents\KULIAH\PROJECTS\StraTistics\dashboard')
from db import run_query

df = run_query("SELECT * FROM public_metrics.pace_trend ORDER BY week_start_date ASC")
print(f"Total rows: {len(df)}")
print(df.to_string())
