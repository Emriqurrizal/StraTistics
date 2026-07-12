
  create view "airflow"."public_silver"."stg_gps_points__dbt_tmp"
    
    
  as (
    

with streams as (
    select * from "airflow"."bronze"."raw_streams"
    where latitude is not null and longitude is not null
)

select
    strava_id,
    time_offset,
    latitude,
    longitude,
    altitude,
    velocity,
    distance as cumulative_distance_m,
    source,
    ingested_at
from streams
  );