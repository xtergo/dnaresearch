"""Blockchain Ledger for Immutable Consent and Audit Trails"""

import hashlib
import json
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from uuid import uuid4


class LedgerEntryType(Enum):
    CONSENT_GRANTED = "consent_granted"
    CONSENT_WITHDRAWN = "consent_withdrawn"
    DATA_ACCESS = "data_access"
    THEORY_EXECUTION = "theory_execution"
    EVIDENCE_ADDED = "evidence_added"
    GENOMIC_ANALYSIS = "genomic_analysis"
    REPORT_GENERATED = "report_generated"


class ConsentStatus(Enum):
    ACTIVE = "active"
    WITHDRAWN = "withdrawn"
    EXPIRED = "expired"


@dataclass
class LedgerEntry:
    """Immutable ledger entry for blockchain storage"""

    entry_id: str
    entry_type: LedgerEntryType
    user_id: str
    timestamp: str
    data_hash: str
    previous_hash: str
    block_hash: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    signature: Optional[str] = None


@dataclass
class ConsentRecord:
    """Consent record for blockchain storage"""

    consent_id: str
    user_id: str
    consent_type: str
    status: ConsentStatus
    granted_at: str
    withdrawn_at: Optional[str] = None
    expiry_date: Optional[str] = None
    data_categories: List[str] = field(default_factory=list)
    purpose: str = ""
    digital_signature: str = ""
    ip_address: str = ""
    user_agent: str = ""


@dataclass
class Block:
    """Blockchain block containing multiple entries"""

    block_id: str
    timestamp: str
    previous_block_hash: str
    merkle_root: str
    entries: List[LedgerEntry] = field(default_factory=list)
    block_hash: str = ""
    nonce: int = 0


class BlockchainLedger:
    """Permissioned blockchain ledger for genomic research platform"""

    def __init__(self):
        self.blocks: List[Block] = []
        self.pending_entries: List[LedgerEntry] = []
        self.consent_records: Dict[str, ConsentRecord] = {}
        self.user_consents: Dict[str, List[str]] = {}  # user_id -> consent_ids
        self.entry_index: Dict[str, str] = {}  # entry_id -> block_id

        # Create genesis block
        self._create_genesis_block()

    def _create_genesis_block(self):
        """Create the genesis block"""
        genesis_block = Block(
            block_id="genesis_block",
            timestamp=datetime.utcnow().isoformat() + "Z",
            previous_block_hash="0" * 64,
            merkle_root="0" * 64,
            entries=[],
        )
        genesis_block.block_hash = self._calculate_block_hash(genesis_block)
        self.blocks.append(genesis_block)

    def _calculate_hash(self, data: str) -> str:
        """Calculate SHA-256 hash of data"""
        return hashlib.sha256(data.encode()).hexdigest()

    def _calculate_block_hash(self, block: Block) -> str:
        """Calculate hash for a block"""
        block_data = {
            "block_id": block.block_id,
            "timestamp": block.timestamp,
            "previous_block_hash": block.previous_block_hash,
            "merkle_root": block.merkle_root,
            "nonce": block.nonce,
        }
        return self._calculate_hash(json.dumps(block_data, sort_keys=True))

    def _calculate_merkle_root(self, entries: List[LedgerEntry]) -> str:
        """Calculate Merkle root for entries"""
        if not entries:
            return "0" * 64

        hashes = [entry.data_hash for entry in entries]

        while len(hashes) > 1:
            if len(hashes) % 2 == 1:
                hashes.append(hashes[-1])  # Duplicate last hash if odd number

            new_hashes = []
            for i in range(0, len(hashes), 2):
                combined = hashes[i] + hashes[i + 1]
                new_hashes.append(self._calculate_hash(combined))
            hashes = new_hashes

        return hashes[0]

    def record_consent(
        self,
        user_id: str,
        consent_type: str,
        data_categories: List[str],
        purpose: str,
        digital_signature: str,
        ip_address: str = "",
        user_agent: str = "",
        expiry_days: int = 365,
    ) -> str:
        """Record consent grant on blockchain"""
        consent_id = f"consent_{user_id}_{uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Calculate expiry date
        from datetime import timedelta

        expiry_date = (
            datetime.utcnow() + timedelta(days=expiry_days)
        ).isoformat() + "Z"

        # Create consent record
        consent_record = ConsentRecord(
            consent_id=consent_id,
            user_id=user_id,
            consent_type=consent_type,
            status=ConsentStatus.ACTIVE,
            granted_at=timestamp,
            expiry_date=expiry_date,
            data_categories=data_categories,
            purpose=purpose,
            digital_signature=digital_signature,
            ip_address=ip_address,
            user_agent=user_agent,
        )

        # Store consent record
        self.consent_records[consent_id] = consent_record

        # Update user consent index
        if user_id not in self.user_consents:
            self.user_consents[user_id] = []
        self.user_consents[user_id].append(consent_id)

        # Create ledger entry
        consent_data = {
            "consent_id": consent_id,
            "user_id": user_id,
            "consent_type": consent_type,
            "data_categories": data_categories,
            "purpose": purpose,
            "granted_at": timestamp,
            "expiry_date": expiry_date,
        }

        self._add_ledger_entry(
            entry_type=LedgerEntryType.CONSENT_GRANTED,
            user_id=user_id,
            data=consent_data,
            metadata={
                "ip_address": ip_address,
                "user_agent": user_agent,
                "signature_hash": self._calculate_hash(digital_signature),
            },
        )

        return consent_id

    def withdraw_consent(self, user_id: str, consent_id: str, reason: str = "") -> bool:
        """Record consent withdrawal on blockchain"""
        if consent_id not in self.consent_records:
            return False

        consent_record = self.consent_records[consent_id]
        if (
            consent_record.user_id != user_id
            or consent_record.status != ConsentStatus.ACTIVE
        ):
            return False

        timestamp = datetime.utcnow().isoformat() + "Z"

        # Update consent record
        consent_record.status = ConsentStatus.WITHDRAWN
        consent_record.withdrawn_at = timestamp

        # Create ledger entry
        withdrawal_data = {
            "consent_id": consent_id,
            "user_id": user_id,
            "withdrawn_at": timestamp,
            "reason": reason,
        }

        self._add_ledger_entry(
            entry_type=LedgerEntryType.CONSENT_WITHDRAWN,
            user_id=user_id,
            data=withdrawal_data,
            metadata={"reason": reason},
        )

        return True

    def record_data_access(
        self,
        user_id: str,
        resource_id: str,
        action: str,
        granted: bool,
        consent_types_checked: List[str],
        ip_address: str = "",
    ) -> str:
        """Record data access attempt on blockchain"""
        access_data = {
            "user_id": user_id,
            "resource_id": resource_id,
            "action": action,
            "granted": granted,
            "consent_types_checked": consent_types_checked,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        entry_id = self._add_ledger_entry(
            entry_type=LedgerEntryType.DATA_ACCESS,
            user_id=user_id,
            data=access_data,
            metadata={
                "ip_address": ip_address,
                "access_granted": granted,
            },
        )

        return entry_id

    def record_theory_execution(
        self,
        user_id: str,
        theory_id: str,
        theory_version: str,
        family_id: str,
        bayes_factor: float,
        execution_time_ms: int,
    ) -> str:
        """Record theory execution on blockchain"""
        execution_data = {
            "theory_id": theory_id,
            "theory_version": theory_version,
            "family_id": family_id,
            "bayes_factor": bayes_factor,
            "execution_time_ms": execution_time_ms,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        entry_id = self._add_ledger_entry(
            entry_type=LedgerEntryType.THEORY_EXECUTION,
            user_id=user_id,
            data=execution_data,
            metadata={
                "theory_scope": (
                    theory_id.split("-")[0] if "-" in theory_id else "unknown"
                ),
                "performance_ms": execution_time_ms,
            },
        )

        return entry_id

    def record_evidence_addition(
        self,
        user_id: str,
        theory_id: str,
        theory_version: str,
        family_id: str,
        bayes_factor: float,
        evidence_type: str,
        source: str,
    ) -> str:
        """Record evidence addition on blockchain"""
        evidence_data = {
            "theory_id": theory_id,
            "theory_version": theory_version,
            "family_id": family_id,
            "bayes_factor": bayes_factor,
            "evidence_type": evidence_type,
            "source": source,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        entry_id = self._add_ledger_entry(
            entry_type=LedgerEntryType.EVIDENCE_ADDED,
            user_id=user_id,
            data=evidence_data,
            metadata={
                "evidence_strength": (
                    "strong"
                    if bayes_factor > 3.0
                    else "moderate" if bayes_factor > 1.5 else "weak"
                ),
                "source_type": source,
            },
        )

        return entry_id

    def record_genomic_analysis(
        self,
        user_id: str,
        analysis_type: str,
        gene: str,
        variant: str,
        result: str,
        confidence: float,
    ) -> str:
        """Record genomic analysis on blockchain"""
        analysis_data = {
            "analysis_type": analysis_type,
            "gene": gene,
            "variant": variant,
            "result": result,
            "confidence": confidence,
            "timestamp": datetime.utcnow().isoformat() + "Z",
        }

        entry_id = self._add_ledger_entry(
            entry_type=LedgerEntryType.GENOMIC_ANALYSIS,
            user_id=user_id,
            data=analysis_data,
            metadata={
                "gene_category": self._categorize_gene(gene),
                "confidence_level": (
                    "high"
                    if confidence > 0.8
                    else "medium" if confidence > 0.5 else "low"
                ),
            },
        )

        return entry_id

    def _categorize_gene(self, gene: str) -> str:
        """Categorize gene for metadata"""
        autism_genes = ["SHANK3", "NRXN1", "SYNGAP1", "CHD8", "SCN2A"]
        cancer_genes = ["BRCA1", "BRCA2", "TP53", "PTEN", "MLH1"]

        if gene in autism_genes:
            return "autism"
        elif gene in cancer_genes:
            return "cancer"
        else:
            return "other"

    def _add_ledger_entry(
        self,
        entry_type: LedgerEntryType,
        user_id: str,
        data: Dict[str, Any],
        metadata: Dict[str, Any] = None,
    ) -> str:
        """Add entry to pending entries for next block"""
        entry_id = f"{entry_type.value}_{user_id}_{uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"

        # Calculate data hash
        data_json = json.dumps(data, sort_keys=True)
        data_hash = self._calculate_hash(data_json)

        # Get previous hash
        previous_hash = self.blocks[-1].block_hash if self.blocks else "0" * 64

        # Create entry
        entry = LedgerEntry(
            entry_id=entry_id,
            entry_type=entry_type,
            user_id=user_id,
            timestamp=timestamp,
            data_hash=data_hash,
            previous_hash=previous_hash,
            block_hash="",  # Will be set when block is created
            metadata=metadata or {},
        )

        self.pending_entries.append(entry)

        # Auto-commit block if we have enough entries
        if len(self.pending_entries) >= 10:
            self._commit_block()

        return entry_id

    def _commit_block(self) -> str:
        """Commit pending entries to a new block"""
        if not self.pending_entries:
            return ""

        block_id = f"block_{len(self.blocks)}_{uuid4().hex[:8]}"
        timestamp = datetime.utcnow().isoformat() + "Z"
        previous_block_hash = self.blocks[-1].block_hash if self.blocks else "0" * 64

        # Calculate Merkle root
        merkle_root = self._calculate_merkle_root(self.pending_entries)

        # Create block
        block = Block(
            block_id=block_id,
            timestamp=timestamp,
            previous_block_hash=previous_block_hash,
            merkle_root=merkle_root,
            entries=self.pending_entries.copy(),
        )

        # Calculate block hash
        block.block_hash = self._calculate_block_hash(block)

        # Update entry block hashes
        for entry in block.entries:
            entry.block_hash = block.block_hash
            self.entry_index[entry.entry_id] = block_id

        # Add block to chain
        self.blocks.append(block)

        # Clear pending entries
        self.pending_entries.clear()

        return block_id

    def verify_consent(self, user_id: str, consent_type: str) -> bool:
        """Verify if user has valid consent"""
        if user_id not in self.user_consents:
            return False

        for consent_id in self.user_consents[user_id]:
            consent = self.consent_records.get(consent_id)
            if not consent:
                continue

            if (
                consent.consent_type == consent_type
                and consent.status == ConsentStatus.ACTIVE
            ):
                # Check expiry
                if consent.expiry_date:
                    from datetime import datetime

                    expiry = datetime.fromisoformat(
                        consent.expiry_date.replace("Z", "+00:00")
                    )
                    if datetime.utcnow().replace(tzinfo=expiry.tzinfo) > expiry:
                        consent.status = ConsentStatus.EXPIRED
                        continue

                return True

        return False

    def get_user_consents(self, user_id: str) -> List[ConsentRecord]:
        """Get all consent records for a user"""
        if user_id not in self.user_consents:
            return []

        consents = []
        for consent_id in self.user_consents[user_id]:
            consent = self.consent_records.get(consent_id)
            if consent:
                consents.append(consent)

        return consents

    def get_audit_trail(self, user_id: str) -> List[LedgerEntry]:
        """Get audit trail for a user"""
        audit_entries = []

        for block in self.blocks:
            for entry in block.entries:
                if entry.user_id == user_id:
                    audit_entries.append(entry)

        # Add pending entries
        for entry in self.pending_entries:
            if entry.user_id == user_id:
                audit_entries.append(entry)

        return sorted(audit_entries, key=lambda x: x.timestamp, reverse=True)

    def get_ledger_entry(self, entry_id: str) -> Optional[LedgerEntry]:
        """Get specific ledger entry by ID"""
        block_id = self.entry_index.get(entry_id)
        if not block_id:
            # Check pending entries
            for entry in self.pending_entries:
                if entry.entry_id == entry_id:
                    return entry
            return None

        # Find in committed blocks
        for block in self.blocks:
            if block.block_id == block_id:
                for entry in block.entries:
                    if entry.entry_id == entry_id:
                        return entry

        return None

    def verify_chain_integrity(self) -> bool:
        """Verify blockchain integrity"""
        for i in range(1, len(self.blocks)):
            current_block = self.blocks[i]
            previous_block = self.blocks[i - 1]

            # Verify previous hash
            if current_block.previous_block_hash != previous_block.block_hash:
                return False

            # Verify block hash
            if current_block.block_hash != self._calculate_block_hash(current_block):
                return False

            # Verify Merkle root
            if current_block.merkle_root != self._calculate_merkle_root(
                current_block.entries
            ):
                return False

        return True

    def get_blockchain_stats(self) -> Dict[str, Any]:
        """Get blockchain statistics"""
        total_entries = sum(len(block.entries) for block in self.blocks) + len(
            self.pending_entries
        )

        entry_types = {}
        for block in self.blocks:
            for entry in block.entries:
                entry_type = entry.entry_type.value
                entry_types[entry_type] = entry_types.get(entry_type, 0) + 1

        for entry in self.pending_entries:
            entry_type = entry.entry_type.value
            entry_types[entry_type] = entry_types.get(entry_type, 0) + 1

        consent_stats = {
            "total_consents": len(self.consent_records),
            "active_consents": len(
                [
                    c
                    for c in self.consent_records.values()
                    if c.status == ConsentStatus.ACTIVE
                ]
            ),
            "withdrawn_consents": len(
                [
                    c
                    for c in self.consent_records.values()
                    if c.status == ConsentStatus.WITHDRAWN
                ]
            ),
            "expired_consents": len(
                [
                    c
                    for c in self.consent_records.values()
                    if c.status == ConsentStatus.EXPIRED
                ]
            ),
        }

        return {
            "total_blocks": len(self.blocks),
            "total_entries": total_entries,
            "pending_entries": len(self.pending_entries),
            "entry_types": entry_types,
            "consent_stats": consent_stats,
            "unique_users": len(self.user_consents),
            "chain_integrity": self.verify_chain_integrity(),
        }

    def force_commit_block(self) -> str:
        """Force commit pending entries to block (for testing/admin)"""
        return self._commit_block()
