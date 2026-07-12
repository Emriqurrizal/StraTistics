
  
    

  create  table "airflow"."public_gold"."fct_activities__dbt_tmp"
  
  
    as
  
  (
    

with stg_activities as (
    select * from "airflow"."public_silver"."stg_activities"
),
dim_gear as (
    select * from "airflow"."public_gold"."dim_gear"
)

select
    a.strava_id,
    a.name,
    a.sport_type,
    a.start_date,
    a.start_date::date as date_day,
    a.distance_km,
    a.moving_time,
    a.moving_time / 60.0 as moving_time_min,
    a.elapsed_time,
    a.elevation_m,
    a.avg_pace_min_per_km,
    a.average_heartrate,
    a.max_heartrate,
    a.average_cadence,
    a.calories,
    a.gear_id,
    g.name as gear_name,
    a.source,
    a.ingested_at
from stg_activities a
left join dim_gear g on a.gear_id = g.gear_id
  );
  