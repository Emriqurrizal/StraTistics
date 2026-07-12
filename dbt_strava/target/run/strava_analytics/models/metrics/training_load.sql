
  
    

  create  table "airflow"."public_metrics"."training_load__dbt_tmp"
  
  
    as
  
  (
    

with daily as (
    select * from "airflow"."public_gold"."fct_daily_training_log"
),
rolling_avgs as (
    select
        date_day,
        total_distance_km as daily_distance,
        avg(total_distance_km) over (
            order by date_day
            rows between 41 preceding and current row
        ) as ctl_42d_avg,
        avg(total_distance_km) over (
            order by date_day
            rows between 6 preceding and current row
        ) as atl_7d_avg
    from daily
)

select
    date_day,
    daily_distance,
    ctl_42d_avg as ctl,
    atl_7d_avg as atl,
    (ctl_42d_avg - atl_7d_avg) as tsb
from rolling_avgs
  );
  