
  create view "airflow"."public_silver"."stg_activities__dbt_tmp"
    
    
  as (
    

with raw as (
    select * from "airflow"."bronze"."raw_activities"
)

select
    strava_id,
    name,
    sport_type,
    start_date,
    -- Convert distance from meters to km
    distance / 1000.0 as distance_km,
    moving_time,
    elapsed_time,
    total_elevation_gain as elevation_m,
    -- Calculate pace in minutes per km
    case 
        when distance > 0 then (moving_time / 60.0) / (distance / 1000.0)
        else null 
    end as avg_pace_min_per_km,
    average_heartrate,
    max_heartrate,
    -- Strava provides 1-legged strides for running, multiply by 2 for SPM
    case 
        when sport_type in ('Run', 'TrailRun') then average_cadence * 2
        else average_cadence
    end as average_cadence,
    calories,
    gear_id,
    start_latlng,
    map_polyline,
    source,
    ingested_at
from raw
where sport_type in ('Run', 'TrailRun')
  and average_heartrate is not null
  and gear_id is not null
  and distance > 0
  and moving_time > 0
  and average_cadence is not null
  );