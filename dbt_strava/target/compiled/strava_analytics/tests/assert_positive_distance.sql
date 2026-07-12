select
    strava_id,
    distance_km
from "airflow"."public_gold"."fct_activities"
where distance_km < 0