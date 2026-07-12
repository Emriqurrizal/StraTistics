{{ config(materialized='view') }}

with streams as (
    select * from {{ source('bronze', 'raw_streams') }}
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
