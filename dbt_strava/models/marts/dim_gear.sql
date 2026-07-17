{{ config(materialized='table') }}

with raw_gear as (
    select * from {{ source('bronze', 'raw_gear') }}
),
valid_activities as (
    select * from {{ ref('stg_activities') }}
),
gear_mileage as (
    select 
        gear_id,
        sum(distance_km) as valid_distance_km
    from valid_activities
    group by 1
)

select
    r.gear_id,
    r.name,
    r.brand_name,
    r.model_name,
    coalesce(m.valid_distance_km, 0) as cumulative_distance_km,
    r.retired
from raw_gear r
left join gear_mileage m on r.gear_id = m.gear_id
