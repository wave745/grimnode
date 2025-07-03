"""
I/O utilities for GrimBundle
Handles file operations, JSON serialization, and bundle persistence
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime
import os

def save_bundle(bundle_data: Dict[str, Any], output_path: Path) -> bool:
    """
    Save a bundle to a JSON file
    
    Args:
        bundle_data: The bundle data to save
        output_path: Path where to save the bundle
        
    Returns:
        True if successful, False otherwise
    """
    try:
        # Ensure the directory exists
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Add metadata if not present
        if "created_at" not in bundle_data:
            bundle_data["created_at"] = datetime.now().isoformat()
        
        if "version" not in bundle_data:
            bundle_data["version"] = "1.0.0"
        
        # Save to file
        with open(output_path, 'w') as f:
            json.dump(bundle_data, f, indent=2, default=str)
        
        return True
    except Exception as e:
        print(f"Error saving bundle: {e}")
        return False

def load_bundle(bundle_path: Path) -> Optional[Dict[str, Any]]:
    """
    Load a bundle from a JSON file
    
    Args:
        bundle_path: Path to the bundle file
        
    Returns:
        Bundle data if successful, None otherwise
    """
    try:
        if not bundle_path.exists():
            return None
        
        with open(bundle_path, 'r') as f:
            bundle_data = json.load(f)
        
        return bundle_data
    except Exception as e:
        print(f"Error loading bundle: {e}")
        return None

def list_bundles(bundles_dir: Path = Path("bundles")) -> list[Path]:
    """
    List all bundle files in a directory
    
    Args:
        bundles_dir: Directory to search for bundles
        
    Returns:
        List of bundle file paths
    """
    if not bundles_dir.exists():
        return []
    
    return list(bundles_dir.glob("*.json"))

def get_bundle_info(bundle_path: Path) -> Optional[Dict[str, Any]]:
    """
    Get basic information about a bundle without loading the full data
    
    Args:
        bundle_path: Path to the bundle file
        
    Returns:
        Basic bundle info if successful, None otherwise
    """
    try:
        bundle_data = load_bundle(bundle_path)
        if not bundle_data:
            return None
        
        return {
            "bundle_id": bundle_data.get("bundle_id", bundle_path.stem),
            "tokens": bundle_data.get("tokens", []),
            "slippage": bundle_data.get("slippage", 0),
            "status": bundle_data.get("status", "unknown"),
            "created_at": bundle_data.get("created_at", bundle_data.get("timestamp", "")),
            "file_size": bundle_path.stat().st_size,
            "file_path": str(bundle_path)
        }
    except Exception as e:
        print(f"Error getting bundle info: {e}")
        return None

def validate_bundle_file(bundle_path: Path) -> Dict[str, Any]:
    """
    Validate a bundle file for integrity and required fields
    
    Args:
        bundle_path: Path to the bundle file
        
    Returns:
        Validation results
    """
    validation = {
        "valid": False,
        "errors": [],
        "warnings": []
    }
    
    try:
        # Check if file exists
        if not bundle_path.exists():
            validation["errors"].append("Bundle file does not exist")
            return validation
        
        # Check if file is readable
        if not os.access(bundle_path, os.R_OK):
            validation["errors"].append("Bundle file is not readable")
            return validation
        
        # Try to load the bundle
        bundle_data = load_bundle(bundle_path)
        if not bundle_data:
            validation["errors"].append("Failed to parse bundle JSON")
            return validation
        
        # Check required fields
        required_fields = ["bundle_id", "tokens", "actions"]
        for field in required_fields:
            if field not in bundle_data:
                validation["errors"].append(f"Missing required field: {field}")
        
        # Check if tokens list is not empty
        if bundle_data.get("tokens") and len(bundle_data["tokens"]) == 0:
            validation["warnings"].append("Bundle contains no tokens")
        
        # Check if actions list is not empty
        if bundle_data.get("actions") and len(bundle_data["actions"]) == 0:
            validation["warnings"].append("Bundle contains no actions")
        
        # If no errors, mark as valid
        if not validation["errors"]:
            validation["valid"] = True
        
        return validation
        
    except Exception as e:
        validation["errors"].append(f"Unexpected error: {e}")
        return validation

def backup_bundle(bundle_path: Path, backup_dir: Path = Path("backups")) -> Optional[Path]:
    """
    Create a backup of a bundle file
    
    Args:
        bundle_path: Path to the bundle to backup
        backup_dir: Directory to store backups
        
    Returns:
        Path to backup file if successful, None otherwise
    """
    try:
        if not bundle_path.exists():
            return None
        
        # Create backup directory
        backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate backup filename with timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{bundle_path.stem}_backup_{timestamp}.json"
        backup_path = backup_dir / backup_filename
        
        # Copy the file
        import shutil
        shutil.copy2(bundle_path, backup_path)
        
        return backup_path
    except Exception as e:
        print(f"Error creating backup: {e}")
        return None 