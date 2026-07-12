{{ config(materialized='view') }}

with streams as (
    select * from {{ source('bronze', 'raw_streams') }}
    where heartrate is not null
),
zones as (
    select * from {{ ref('hr_zones') }}
)

select
    s.strava_id,
    z.zone,
    -- assuming 1 second intervals for streams
    count(*) as seconds_in_zone
from streams s
join zones z on s.heartrate >= z.min_hr and s.heartrate <= z.max_hr
group by 1, 2
