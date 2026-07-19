import sys
import datetime
sys.path.append(r'C:\Users\Emriqurrizal\Documents\KULIAH\PROJECTS\StraTistics\dashboard')
from db import run_query

end = datetime.date.today()
start = end - datetime.timedelta(days=6)

query = """
WITH date_series AS (
    SELECT generate_series(%s::date, %s::date, '1 day'::interval)::date AS date_day
)
SELECT 
    d.date_day as date,
    p.avg_pace_min_per_km as weekly_pace,
    p.rolling_4w_pace,
    p.rolling_8w_pace,
    p.rolling_12w_pace
FROM date_series d
LEFT JOIN public_metrics.pace_trend p 
ON date_trunc('week', d.date_day)::date = p.week_start_date
ORDER BY d.date_day
"""

df = run_query(query, (start, end))
print(df.to_string())
