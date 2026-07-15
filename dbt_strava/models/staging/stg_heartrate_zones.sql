{{ config(materialized='view') }}

with streams as (
    select * from {{ source('bronze', 'raw_streams') }}
    where heartrate is not null
),
deltas as (
    select
        strava_id,
        heartrate,
        time_offset - lag(time_offset, 1) over (
            partition by strava_id order by time_offset
        ) as seconds_elapsed
    from streams
),
zones as (
    select * from {{ ref('hr_zones') }}
)

select
    d.strava_id,
    z.zone,
    sum(d.seconds_elapsed) as seconds_in_zone
from deltas d
join zones z on d.heartrate >= z.min_hr and d.heartrate <= z.max_hr
where d.seconds_elapsed is not null
group by 1, 2
