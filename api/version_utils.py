import re
from typing import Tuple
from fastapi import HTTPException

def validate_semver(version: str) -> bool:
    """Validate semantic version format (x.y.z)"""
    pattern = r'^\d+\.\d+\.\d+$'
    return bool(re.match(pattern, version))

def parse_version(version: str) -> Tuple[int, int, int]:
    """Parse semantic version into major, minor, patch"""
    if not validate_semver(version):
        raise HTTPException(status_code=400, detail=f"Invalid semantic version: {version}")
    
    major, minor, patch = version.split('.')
    return int(major), int(minor), int(patch)

def compare_versions(version1: str, version2: str) -> int:
    """Compare two semantic versions. Returns -1, 0, or 1"""
    v1_parts = parse_version(version1)
    v2_parts = parse_version(version2)
    
    if v1_parts < v2_parts:
        return -1
    elif v1_parts > v2_parts:
        return 1
    else:
        return 0

def increment_version(version: str, level: str = "patch") -> str:
    """Increment semantic version by level (major, minor, patch)"""
    major, minor, patch = parse_version(version)
    
    if level == "major":
        return f"{major + 1}.0.0"
    elif level == "minor":
        return f"{major}.{minor + 1}.0"
    elif level == "patch":
        return f"{major}.{minor}.{patch + 1}"
    else:
        raise HTTPException(status_code=400, detail=f"Invalid increment level: {level}")