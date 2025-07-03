"""
Bundle executor for GrimBundle
Handles the core logic for creating and managing token bundles
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import random

def bundle_tokens(
    tokens: List[str], 
    slippage: float, 
    simulate: bool = False,
    amounts: Optional[List[str]] = None
) -> Dict[str, Any]:
    """
    Create a bundle of token actions
    
    Args:
        tokens: List of token symbols
        slippage: Slippage tolerance percentage
        simulate: Whether to simulate the bundle
        amounts: Optional list of amounts for each token
    
    Returns:
        Dictionary containing the bundle data
    """
    
    # Generate mock amounts if not provided
    if amounts is None:
        amounts = [str(random.randint(100000, 10000000)) for _ in tokens]
    
    # Ensure amounts list matches tokens list
    if len(amounts) != len(tokens):
        amounts = amounts[:len(tokens)] + [str(random.randint(100000, 10000000))] * (len(tokens) - len(amounts))
    
    # Create actions for each token
    actions = []
    for i, token in enumerate(tokens):
        action = {
            "type": "swap",
            "token": token.upper(),
            "amount": amounts[i],
            "slippage": slippage,
            "priority": i + 1,
            "estimated_gas": random.randint(5000, 15000),
            "estimated_price_impact": round(random.uniform(0.01, 2.0), 2)
        }
        actions.append(action)
    
    # Create bundle metadata
    bundle_data = {
        "actions": actions,
        "total_actions": len(actions),
        "total_estimated_gas": sum(action["estimated_gas"] for action in actions),
        "average_price_impact": round(
            sum(action["estimated_price_impact"] for action in actions) / len(actions), 2
        ),
        "bundle_type": "token_swaps",
        "simulation_mode": simulate
    }
    
    return bundle_data

def validate_bundle(bundle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate a bundle for potential issues
    
    Args:
        bundle_data: The bundle to validate
        
    Returns:
        Dictionary with validation results
    """
    validation = {
        "valid": True,
        "warnings": [],
        "errors": []
    }
    
    actions = bundle_data.get("actions", [])
    
    # Check for empty bundle
    if not actions:
        validation["valid"] = False
        validation["errors"].append("Bundle contains no actions")
        return validation
    
    # Check for duplicate tokens
    tokens = [action["token"] for action in actions]
    if len(tokens) != len(set(tokens)):
        validation["warnings"].append("Duplicate tokens detected in bundle")
    
    # Check for high slippage
    high_slippage_actions = [
        action for action in actions 
        if action.get("slippage", 0) > 5.0
    ]
    if high_slippage_actions:
        validation["warnings"].append(f"High slippage detected in {len(high_slippage_actions)} actions")
    
    # Check for high price impact
    high_impact_actions = [
        action for action in actions 
        if action.get("estimated_price_impact", 0) > 1.0
    ]
    if high_impact_actions:
        validation["warnings"].append(f"High price impact detected in {len(high_impact_actions)} actions")
    
    return validation

def estimate_bundle_cost(bundle_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Estimate the total cost of executing a bundle
    
    Args:
        bundle_data: The bundle to estimate
        
    Returns:
        Dictionary with cost estimates
    """
    actions = bundle_data.get("actions", [])
    
    total_gas = sum(action.get("estimated_gas", 0) for action in actions)
    gas_price = 5000  # Mock gas price in lamports
    total_cost_lamports = total_gas * gas_price
    total_cost_sol = total_cost_lamports / 1_000_000_000  # Convert to SOL
    
    return {
        "total_gas": total_gas,
        "gas_price_lamports": gas_price,
        "total_cost_lamports": total_cost_lamports,
        "total_cost_sol": round(total_cost_sol, 6),
        "estimated_fee_usd": round(total_cost_sol * 100, 2)  # Mock SOL price
    }

def generate_bundle_summary(bundle_data: Dict[str, Any]) -> str:
    """
    Generate a human-readable summary of the bundle
    
    Args:
        bundle_data: The bundle to summarize
        
    Returns:
        String summary of the bundle
    """
    actions = bundle_data.get("actions", [])
    
    if not actions:
        return "Empty bundle"
    
    tokens = [action["token"] for action in actions]
    total_gas = sum(action.get("estimated_gas", 0) for action in actions)
    avg_impact = bundle_data.get("average_price_impact", 0)
    
    summary = f"Bundle with {len(actions)} actions: {', '.join(tokens)}"
    summary += f"\nTotal gas: {total_gas:,} | Avg price impact: {avg_impact}%"
    
    return summary