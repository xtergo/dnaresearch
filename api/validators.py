import json
import jsonschema
from fastapi import HTTPException
from typing import Dict, Any
from version_utils import validate_semver

def load_schema(schema_name: str) -> Dict[str, Any]:
    """Load JSON schema from schemas directory"""
    try:
        with open(f"../schemas/{schema_name}.json") as f:
            return json.load(f)
    except FileNotFoundError:
        raise HTTPException(status_code=500, detail=f"Schema {schema_name} not found")

def validate_theory(theory_data: Dict[str, Any]) -> Dict[str, Any]:
    """Validate theory JSON against schema"""
    schema = load_schema("theory")
    
    try:
        # Validate against JSON schema
        jsonschema.validate(theory_data, schema)
        
        # Additional semantic version validation
        if "version" in theory_data:
            if not validate_semver(theory_data["version"]):
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid semantic version format: {theory_data['version']}"
                )
        
        return theory_data
    except jsonschema.ValidationError as e:
        raise HTTPException(
            status_code=400, 
            detail=f"Theory validation failed: {e.message}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Validation error: {str(e)}"
        )