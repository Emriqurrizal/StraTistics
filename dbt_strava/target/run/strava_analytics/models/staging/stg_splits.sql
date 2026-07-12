
  create view "airflow"."public_silver"."stg_splits__dbt_tmp"
    
    
  as (
    

with laps as (
    select * from "airflow"."bronze"."raw_laps"
)

select
    strava_id,
    lap_index,
    distance / 1000.0 as lap_distance_km,
    elapsed_time,
    moving_time,
    case 
        when distance > 0 then (moving_time / 60.0) / (distance / 1000.0)
        else null 
    end as pace_min_per_km,
    average_heartrate,
    max_heartrate,
    average_cadence
from laps
  );