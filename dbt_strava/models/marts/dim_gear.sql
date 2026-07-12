{{ config(materialized='table') }}

with raw_gear as (
    select * from {{ source('bronze', 'raw_gear') }}
)

select
    gear_id,
    name,
    brand_name,
    model_name,
    distance / 1000.0 as cumulative_distance_km,
    retired
from raw_gear
