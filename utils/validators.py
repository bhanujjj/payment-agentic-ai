"""
Validation utilities.

JSON schema validation and data validation helpers.
"""

import json
from pathlib import Path
from typing import Dict, Any
import jsonschema


def load_schema(schema_name: str) -> Dict[str, Any]:
    """
    Load a JSON schema.
    
    Args:
        schema_name: Name of schema file (without .json)
        
    Returns:
        Schema dictionary
        
    TODO:
    - Load schema from file
    - Cache schemas
    - Handle missing schemas
    """
    schema_path = Path(f"./data/schemas/{schema_name}.json")
    
    if not schema_path.exists():
        raise FileNotFoundError(f"Schema not found: {schema_path}")
    
    with open(schema_path) as f:
        return json.load(f)


def validate_payment_event(event: Dict[str, Any]) -> bool:
    """
    Validate a payment event against schema.
    
    Args:
        event: Payment event to validate
        
    Returns:
        True if valid, raises exception otherwise
        
    TODO:
    - Load schema
    - Validate event
    - Provide helpful error messages
    """
    schema = load_schema("payment_event")
    jsonschema.validate(instance=event, schema=schema)
    return True


def validate_action(action: Dict[str, Any]) -> bool:
    """
    Validate an action against schema.
    
    Args:
        action: Action to validate
        
    Returns:
        True if valid, raises exception otherwise
        
    TODO:
    - Load schema
    - Validate action
    - Check parameter constraints
    """
    schema = load_schema("action")
    jsonschema.validate(instance=action, schema=schema)
    return True
