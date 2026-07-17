"""
strava_api_client.py
Client for Strava API v3. Handles rate limiting, pagination, and fetching data.
"""

import time
import logging
import requests
from typing import List, Dict, Any, Optional

from ingestion.strava_auth import StravaAuth

logger = logging.getLogger(__name__)

class StravaRateLimitExceeded(Exception):
    pass

class StravaAPIClient:
    BASE_URL = "https://www.strava.com/api/v3"
    
    def __init__(self, auth: StravaAuth):
        self.auth = auth
        self.session = requests.Session()
        
    def _get_headers(self) -> Dict[str, str]:
        token = self.auth.get_access_token()
        return {"Authorization": f"Bearer {token}"}
        
    def _handle_rate_limit(self, headers: Dict[str, str]):
        """
        Strava headers:
        X-RateLimit-Limit: 100,1000 (15min, daily)
        X-RateLimit-Usage: 1,1
        """
        usage_str = headers.get('X-RateLimit-Usage')
        limit_str = headers.get('X-RateLimit-Limit')
        
        if usage_str and limit_str:
            try:
                usage_15m, usage_day = map(int, usage_str.split(','))
                limit_15m, limit_day = map(int, limit_str.split(','))
                
                if usage_15m >= limit_15m or usage_day >= limit_day:
                    logger.warning(f"Rate limit exceeded: Usage={usage_str}, Limit={limit_str}. Will retry after backoff.")
                    return
                    
                # Optional: Add sleep if approaching limit
                if limit_15m - usage_15m < 5:
                    logger.warning(f"Approaching 15m rate limit ({usage_15m}/{limit_15m}). Sleeping for 60s...")
                    time.sleep(60)
            except ValueError:
                pass

    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Any:
        url = f"{self.BASE_URL}/{endpoint}"
        headers = self._get_headers()
        
        retries = 3
        backoff = 2
        
        for attempt in range(retries):
            response = self.session.request(method, url, headers=headers, params=params)
            self._handle_rate_limit(response.headers)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:
                wait = 900
                logger.warning(f"429 Too Many Requests. Waiting {wait}s for rate limit reset...")
                time.sleep(wait)
            elif response.status_code >= 500:
                logger.warning(f"Server error {response.status_code}. Retrying...")
                time.sleep(backoff ** (attempt + 1))
            else:
                response.raise_for_status()
                
        raise Exception(f"Failed to fetch {url} after {retries} retries")

    def get_activities(self, after: Optional[int] = None, before: Optional[int] = None) -> List[Dict]:
        """Fetch all activities, paginating automatically."""
        activities = []
        page = 1
        per_page = 200
        
        while True:
            params = {'page': page, 'per_page': per_page}
            if after:
                params['after'] = after
            if before:
                params['before'] = before
                
            logger.info(f"Fetching activities page {page}...")
            data = self._request("GET", "athlete/activities", params=params)
            
            if not data:
                break
                
            activities.extend(data)
            if len(data) < per_page:
                break
                
            page += 1
            
        return activities

    def get_activity_detail(self, activity_id: int) -> Dict:
        """Fetch full details for an activity, including laps and splits."""
        return self._request("GET", f"activities/{activity_id}")

    def get_activity_streams(self, activity_id: int) -> Dict:
        """Fetch time-series stream data for an activity."""
        keys = "time,distance,latlng,altitude,velocity_smooth,heartrate,cadence,watts,temp,moving,grade_smooth"
        params = {'keys': keys, 'key_by_type': 'true'}
        try:
            return self._request("GET", f"activities/{activity_id}/streams", params=params)
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                logger.warning(f"No streams found for activity {activity_id}")
                return {}
            raise

    def get_athlete(self) -> Dict:
        """Fetch athlete profile info."""
        return self._request("GET", "athlete")
        
    def get_gear(self, gear_id: str) -> Dict:
        """Fetch gear details (e.g., shoe total mileage)."""
        return self._request("GET", f"gear/{gear_id}")

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    try:
        auth = StravaAuth()
        client = StravaAPIClient(auth)
        athlete = client.get_athlete()
        print(f"Athlete: {athlete.get('firstname')} {athlete.get('lastname')}")
    except Exception as e:
        print(f"Error: {e}")
