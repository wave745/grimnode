"""
Solana client utility for GrimBundle
Connects to Solana Devnet and fetches token/account info
"""

from solana.rpc.api import Client
from solana.publickey import PublicKey
from typing import Dict, Any, Optional
from solana.keypair import Keypair
import json
from pathlib import Path


DEVNET_URL = "https://api.devnet.solana.com"

class SolanaClient:
    def __init__(self, endpoint: str = DEVNET_URL):
        self.client = Client(endpoint)

    def get_balance(self, pubkey: str) -> Optional[float]:
        """Get SOL balance for a public key (in SOL)"""
        try:
            resp = self.client.get_balance(PublicKey(pubkey))
            if resp["result"] and "value" in resp["result"]:
                return resp["result"]["value"] / 1_000_000_000
        except Exception as e:
            print(f"Error fetching balance: {e}")
        return None

    def get_token_account_balance(self, token_account: str) -> Optional[Dict[str, Any]]:
        """Get SPL token account balance and info"""
        try:
            resp = self.client.get_token_account_balance(PublicKey(token_account))
            if resp["result"] and "value" in resp["result"]:
                return resp["result"]["value"]
        except Exception as e:
            print(f"Error fetching token account balance: {e}")
        return None

    def get_token_supply(self, mint_address: str) -> Optional[Dict[str, Any]]:
        """Get total supply and decimals for a token mint"""
        try:
            resp = self.client.get_token_supply(PublicKey(mint_address))
            if resp["result"] and "value" in resp["result"]:
                return resp["result"]["value"]
        except Exception as e:
            print(f"Error fetching token supply: {e}")
        return None

    def get_recent_blockhash(self) -> Optional[str]:
        """Get a recent blockhash for transaction simulation"""
        try:
            resp = self.client.get_recent_blockhash()
            if resp["result"] and "value" in resp["result"]:
                return resp["result"]["value"]["blockhash"]
        except Exception as e:
            print(f"Error fetching blockhash: {e}")
        return None

    def load_keypair_from_file(self, path: str) -> Keypair:
        """Load a Solana keypair from a local JSON file (Solana CLI format)"""
        with open(path, 'r') as f:
            secret = json.load(f)
        return Keypair.from_secret_key(bytes(secret)) 