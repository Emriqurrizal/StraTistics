
  
    

  create  table "airflow"."public_gold"."fct_daily_training_log__dbt_tmp"
  
  
    as
  
  (
    

with fct_activities as (
    select * from "airflow"."public_gold"."fct_activities"
),
dim_date as (
    select * from "airflow"."public_gold"."dim_date"
),
daily_agg as (
    select
        date_day,
        count(strava_id) as total_runs,
        sum(distance_km) as total_distance_km,
        sum(moving_time_min) as total_moving_time_min,
        sum(elevation_m) as total_elevation_m
    from fct_activities
    group by date_day
)

select
    d.date_day,
    coalesce(a.total_runs, 0) as total_runs,
    coalesce(a.total_distance_km, 0.0) as total_distance_km,
    coalesce(a.total_moving_time_min, 0.0) as total_moving_time_min,
    coalesce(a.total_elevation_m, 0.0) as total_elevation_m,
    case when a.total_runs is null then true else false end as is_rest_day
from dim_date d
left join daily_agg a on d.date_day = a.date_day
where d.date_day <= current_date
  );
  