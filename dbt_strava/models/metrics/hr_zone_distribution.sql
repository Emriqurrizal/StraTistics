{{ config(materialized='table') }}

with stg_zones as (
    select * from {{ ref('stg_heartrate_zones') }}
),
fct_acts as (
    select * from {{ ref('fct_activities') }}
),
joined as (
    select
        a.date_day,
        a.strava_id,
        z.zone,
        z.seconds_in_zone
    from fct_acts a
    join stg_zones z on a.strava_id = z.strava_id
)

select
    date_day,
    zone,
    sum(seconds_in_zone) as total_seconds_in_zone,
    sum(seconds_in_zone) / 60.0 as total_minutes_in_zone
from joined
group by 1, 2
