"""
Jupiter Aggregator API utility for GrimBundle
Fetches swap routes and builds transactions for Solana swaps
"""

import requests
from typing import Dict, Any, List, Optional

JUPITER_API = "https://quote-api.jup.ag/v6/quote"
JUPITER_SWAP_API = "https://quote-api.jup.ag/v6/swap"

# Fetch swap routes from Jupiter

def fetch_jupiter_routes(
    input_mint: str,
    output_mint: str,
    amount: int,
    slippage_bps: int = 50,
    user_public_key: Optional[str] = None
) -> List[Dict[str, Any]]:
    """Fetch swap routes from Jupiter Aggregator API"""
    params = {
        "inputMint": input_mint,
        "outputMint": output_mint,
        "amount": amount,
        "slippageBps": slippage_bps,
        "onlyDirectRoutes": False,
    }
    if user_public_key:
        params["userPublicKey"] = user_public_key
    try:
        resp = requests.get(JUPITER_API, params=params)
        resp.raise_for_status()
        data = resp.json()
        return data.get("data", [])
    except Exception as e:
        print(f"Error fetching Jupiter routes: {e}")
        return []

# Build a swap transaction (serialized) using Jupiter

def build_jupiter_swap_tx(
    route: Dict[str, Any],
    user_public_key: str
) -> Optional[Dict[str, Any]]:
    """Build a swap transaction using Jupiter Aggregator API"""
    try:
        resp = requests.post(JUPITER_SWAP_API, json={
            "route": route,
            "userPublicKey": user_public_key,
            "wrapUnwrapSOL": True,
            "asLegacyTransaction": True
        })
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        print(f"Error building Jupiter swap transaction: {e}")
        return None 