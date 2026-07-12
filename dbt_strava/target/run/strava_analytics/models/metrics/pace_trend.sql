
  
    

  create  table "airflow"."public_metrics"."pace_trend__dbt_tmp"
  
  
    as
  
  (
    

with weekly as (
    select * from "airflow"."public_gold"."fct_weekly_summary"
),
rolling_pace as (
    select
        week_start_date,
        avg_pace_min_per_km,
        avg(avg_pace_min_per_km) over (
            order by week_start_date
            rows between 3 preceding and current row
        ) as rolling_4w_pace,
        avg(avg_pace_min_per_km) over (
            order by week_start_date
            rows between 7 preceding and current row
        ) as rolling_8w_pace,
        avg(avg_pace_min_per_km) over (
            order by week_start_date
            rows between 11 preceding and current row
        ) as rolling_12w_pace
    from weekly
)

select * from rolling_pace
  );
  