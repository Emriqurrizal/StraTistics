
  create view "airflow"."public_silver"."stg_heartrate_zones__dbt_tmp"
    
    
  as (
    

with streams as (
    select * from "airflow"."bronze"."raw_streams"
    where heartrate is not null
),
zones as (
    select * from "airflow"."public"."hr_zones"
)

select
    s.strava_id,
    z.zone,
    -- assuming 1 second intervals for streams
    count(*) as seconds_in_zone
from streams s
join zones z on s.heartrate >= z.min_hr and s.heartrate <= z.max_hr
group by 1, 2
  );