"""
PumpPortal API utility for GrimBundle
Fetches trending tokens from pump.fun via pumpportal.fun
"""

import requests
from typing import List, Dict, Any

PUMPPORTAL_API = "https://api.pumpportal.fun/v1/tokens/trending"

def fetch_trending_tokens(limit: int = 10) -> List[Dict[str, Any]]:
    """Fetch trending tokens from pumpportal.fun API"""
    try:
        resp = requests.get(PUMPPORTAL_API, params={"limit": limit})
        resp.raise_for_status()
        data = resp.json()
        return data.get("tokens", [])
    except Exception as e:
        print(f"Error fetching trending tokens: {e}")
        return [] 