from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional


@dataclass
class TheoryLineage:
    """Theory lineage relationship"""

    theory_id: str
    version: str
    parent_id: Optional[str]
    parent_version: Optional[str]
    fork_reason: str
    created_at: str


@dataclass
class ForkResult:
    """Result of theory forking operation"""

    new_theory_id: str
    new_version: str
    parent_id: str
    parent_version: str
    changes_made: List[str]


class TheoryForker:
    """Handles theory forking and lineage tracking"""

    def __init__(self):
        self.lineage_store: Dict[str, TheoryLineage] = {}

    def fork_theory(
        self,
        parent_theory: Dict[str, Any],
        new_theory_id: str,
        modifications: Dict[str, Any],
        fork_reason: str = "user_modification",
    ) -> ForkResult:
        """Fork a theory with modifications"""
        import copy

        # Create new theory by deep copying parent and applying modifications
        new_theory = copy.deepcopy(parent_theory)
        new_theory["id"] = new_theory_id

        # Increment version for fork
        new_version = self._increment_version(parent_theory["version"])
        new_theory["version"] = new_version

        # Track changes made
        changes_made = []

        # Apply modifications
        for key, value in modifications.items():
            if key in new_theory and new_theory[key] != value:
                changes_made.append(f"Modified {key}")
                new_theory[key] = value
            elif key not in new_theory:
                changes_made.append(f"Added {key}")
                new_theory[key] = value

        # Store lineage relationship
        lineage_key = f"{new_theory_id}@{new_version}"
        self.lineage_store[lineage_key] = TheoryLineage(
            theory_id=new_theory_id,
            version=new_version,
            parent_id=parent_theory["id"],
            parent_version=parent_theory["version"],
            fork_reason=fork_reason,
            created_at=datetime.utcnow().isoformat() + "Z",
        )

        return (
            ForkResult(
                new_theory_id=new_theory_id,
                new_version=new_version,
                parent_id=parent_theory["id"],
                parent_version=parent_theory["version"],
                changes_made=changes_made,
            ),
            new_theory,
        )

    def get_lineage(self, theory_id: str, version: str) -> Optional[TheoryLineage]:
        """Get lineage information for a theory"""
        key = f"{theory_id}@{version}"
        return self.lineage_store.get(key)

    def get_children(self, parent_id: str, parent_version: str) -> List[TheoryLineage]:
        """Get all child theories forked from a parent"""
        children = []
        for lineage in self.lineage_store.values():
            if (
                lineage.parent_id == parent_id
                and lineage.parent_version == parent_version
            ):
                children.append(lineage)
        return children

    def get_ancestry(self, theory_id: str, version: str) -> List[TheoryLineage]:
        """Get full ancestry chain for a theory"""
        ancestry = []
        current_lineage = self.get_lineage(theory_id, version)

        while current_lineage and current_lineage.parent_id:
            ancestry.append(current_lineage)
            current_lineage = self.get_lineage(
                current_lineage.parent_id, current_lineage.parent_version
            )

        return ancestry

    def _increment_version(self, version: str) -> str:
        """Increment patch version for fork"""
        parts = version.split(".")
        if len(parts) == 3:
            major, minor, patch = parts
            return f"{major}.{minor}.{int(patch) + 1}"
        return "1.0.1"
