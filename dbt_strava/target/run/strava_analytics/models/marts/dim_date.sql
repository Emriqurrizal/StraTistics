
  
    

  create  table "airflow"."public_gold"."dim_date__dbt_tmp"
  
  
    as
  
  (
    

with date_spine as (
    select generate_series(
        '2025-01-01'::date,
        '2030-12-31'::date,
        '1 day'::interval
    )::date as date_day
)

select
    date_day,
    extract(year from date_day) as year,
    extract(month from date_day) as month,
    extract(day from date_day) as day_of_month,
    extract(isodow from date_day) as day_of_week_iso,
    trim(to_char(date_day, 'Day')) as day_name,
    case when extract(isodow from date_day) in (6, 7) then true else false end as is_weekend,
    extract(week from date_day) as week_number,
    extract(quarter from date_day) as quarter
from date_spine
  );
  