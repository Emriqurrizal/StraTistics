select
    strava_id,
    distance_km
from {{ ref('fct_activities') }}
where distance_km < 0
