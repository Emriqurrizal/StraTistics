"""
strava_auth.py
Handles OAuth2 token refresh and caching for Strava API.
"""

import os
import time
import requests
import logging

logger = logging.getLogger(__name__)

class StravaAuth:
    def __init__(self):
        self.client_id = os.getenv('STRAVA_CLIENT_ID')
        self.client_secret = os.getenv('STRAVA_CLIENT_SECRET')
        self.refresh_token = os.getenv('STRAVA_REFRESH_TOKEN')
        
        if not all([self.client_id, self.client_secret, self.refresh_token]):
            raise ValueError("Missing Strava API credentials in environment variables. Ensure STRAVA_CLIENT_ID, STRAVA_CLIENT_SECRET, and STRAVA_REFRESH_TOKEN are set.")
            
        self.access_token = None
        self.token_expires_at = 0
        
    def get_access_token(self) -> str:
        """Returns a valid access token, refreshing it if necessary."""
        # Add a 60-second buffer to ensure the token doesn't expire during use
        if self.access_token and time.time() < (self.token_expires_at - 60):
            return self.access_token
            
        logger.info("Refreshing Strava access token...")
        url = "https://www.strava.com/oauth/token"
        payload = {
            'client_id': self.client_id,
            'client_secret': self.client_secret,
            'refresh_token': self.refresh_token,
            'grant_type': 'refresh_token'
        }
        
        response = requests.post(url, data=payload)
        response.raise_for_status()
        
        token_data = response.json()
        self.access_token = token_data['access_token']
        self.token_expires_at = token_data['expires_at']
        
        new_refresh_token = token_data.get('refresh_token')
        if new_refresh_token and new_refresh_token != self.refresh_token:
            logger.warning("Received a new refresh token. Please update your environment variables.")
            self.refresh_token = new_refresh_token
            
        return self.access_token

def get_initial_token_from_code(client_id: str, client_secret: str, auth_code: str) -> dict:
    """
    Helper function to get the initial refresh token from the auth code.
    This is intended to be run manually once during initial setup.
    """
    url = "https://www.strava.com/oauth/token"
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'code': auth_code,
        'grant_type': 'authorization_code'
    }
    response = requests.post(url, data=payload)
    response.raise_for_status()
    return response.json()

if __name__ == "__main__":
    # Small helper snippet to use from command line during setup
    import argparse
    parser = argparse.ArgumentParser(description="Strava Auth Helper")
    parser.add_argument("--code", help="Auth code from Strava to get initial tokens")
    parser.add_argument("--client_id", help="Strava Client ID")
    parser.add_argument("--client_secret", help="Strava Client Secret")
    args = parser.parse_args()
    
    if args.code and args.client_id and args.client_secret:
        print("Fetching tokens...")
        try:
            tokens = get_initial_token_from_code(args.client_id, args.client_secret, args.code)
            print("Successfully retrieved tokens!")
            print(f"Access Token: {tokens.get('access_token')}")
            print(f"Refresh Token: {tokens.get('refresh_token')}")
            print("Store the Refresh Token in your .env file!")
        except Exception as e:
            print(f"Error: {e}")
    else:
        print("To test token refresh based on .env, running StravaAuth().get_access_token()...")
        logging.basicConfig(level=logging.INFO)
        try:
            auth = StravaAuth()
            print("Access token retrieved:", auth.get_access_token()[:10] + "... (truncated)")
        except Exception as e:
            print(f"Error: {e}")
