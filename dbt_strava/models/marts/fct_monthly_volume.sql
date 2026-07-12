{{ config(materialized='table') }}

with fct_daily as (
    select * from {{ ref('fct_daily_training_log') }}
),
dim_date as (
    select * from {{ ref('dim_date') }}
)

select
    d.year,
    d.month,
    min(d.date_day) as month_start_date,
    sum(f.total_runs) as total_runs,
    sum(f.total_distance_km) as total_distance_km,
    sum(f.total_moving_time_min) as total_moving_time_min,
    sum(f.total_elevation_m) as total_elevation_m
from dim_date d
left join fct_daily f on d.date_day = f.date_day
where d.date_day <= current_date
group by 1, 2
