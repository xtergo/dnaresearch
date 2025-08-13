"""Tests for blockchain ledger system"""

from datetime import datetime, timedelta

import pytest
from blockchain_ledger import (
    BlockchainLedger,
    ConsentStatus,
    LedgerEntryType,
)


class TestBlockchainLedger:
    """Test blockchain ledger functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.ledger = BlockchainLedger()

    def test_genesis_block_creation(self):
        """Test genesis block is created correctly"""
        assert len(self.ledger.blocks) == 1
        genesis = self.ledger.blocks[0]
        assert genesis.block_id == "genesis_block"
        assert genesis.previous_block_hash == "0" * 64
        assert genesis.merkle_root == "0" * 64
        assert len(genesis.entries) == 0
        assert len(genesis.block_hash) == 64

    def test_record_consent(self):
        """Test consent recording on blockchain"""
        consent_id = self.ledger.record_consent(
            user_id="user_001",
            consent_type="genomic_analysis",
            data_categories=["genetic_data", "health_data"],
            purpose="Rare disease research",
            digital_signature="signature_hash_123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0",
            expiry_days=365,
        )

        # Verify consent record
        assert consent_id in self.ledger.consent_records
        consent = self.ledger.consent_records[consent_id]
        assert consent.user_id == "user_001"
        assert consent.consent_type == "genomic_analysis"
        assert consent.status == ConsentStatus.ACTIVE
        assert "genetic_data" in consent.data_categories
        assert consent.purpose == "Rare disease research"

        # Verify user consent index
        assert "user_001" in self.ledger.user_consents
        assert consent_id in self.ledger.user_consents["user_001"]

        # Verify ledger entry was created
        assert len(self.ledger.pending_entries) == 1
        entry = self.ledger.pending_entries[0]
        assert entry.entry_type == LedgerEntryType.CONSENT_GRANTED
        assert entry.user_id == "user_001"
        assert "ip_address" in entry.metadata

    def test_withdraw_consent(self):
        """Test consent withdrawal on blockchain"""
        # First record consent
        consent_id = self.ledger.record_consent(
            user_id="user_002",
            consent_type="data_sharing",
            data_categories=["genetic_data"],
            purpose="Research collaboration",
            digital_signature="signature_hash_456",
        )

        # Withdraw consent
        success = self.ledger.withdraw_consent(
            user_id="user_002",
            consent_id=consent_id,
            reason="Changed mind about data sharing",
        )

        assert success is True

        # Verify consent status updated
        consent = self.ledger.consent_records[consent_id]
        assert consent.status == ConsentStatus.WITHDRAWN
        assert consent.withdrawn_at is not None

        # Verify withdrawal entry created
        assert len(self.ledger.pending_entries) == 2  # Grant + withdrawal
        withdrawal_entry = self.ledger.pending_entries[1]
        assert withdrawal_entry.entry_type == LedgerEntryType.CONSENT_WITHDRAWN
        assert withdrawal_entry.user_id == "user_002"

    def test_withdraw_nonexistent_consent(self):
        """Test withdrawing non-existent consent fails"""
        success = self.ledger.withdraw_consent(
            user_id="user_003",
            consent_id="nonexistent_consent",
            reason="Test",
        )
        assert success is False

    def test_record_data_access(self):
        """Test data access recording"""
        entry_id = self.ledger.record_data_access(
            user_id="user_004",
            resource_id="/genes/BRCA1/interpret",
            action="analyze_variants",
            granted=True,
            consent_types_checked=["genomic_analysis"],
            ip_address="10.0.0.1",
        )

        assert entry_id is not None
        assert len(self.ledger.pending_entries) == 1
        entry = self.ledger.pending_entries[0]
        assert entry.entry_type == LedgerEntryType.DATA_ACCESS
        assert entry.user_id == "user_004"
        assert entry.metadata["access_granted"] is True

    def test_record_theory_execution(self):
        """Test theory execution recording"""
        entry_id = self.ledger.record_theory_execution(
            user_id="researcher_001",
            theory_id="autism-theory-1",
            theory_version="1.0.0",
            family_id="family_001",
            bayes_factor=2.5,
            execution_time_ms=1500,
        )

        assert entry_id is not None
        assert len(self.ledger.pending_entries) == 1
        entry = self.ledger.pending_entries[0]
        assert entry.entry_type == LedgerEntryType.THEORY_EXECUTION
        assert entry.user_id == "researcher_001"
        assert entry.metadata["theory_scope"] == "autism"
        assert entry.metadata["performance_ms"] == 1500

    def test_record_evidence_addition(self):
        """Test evidence addition recording"""
        entry_id = self.ledger.record_evidence_addition(
            user_id="researcher_002",
            theory_id="cancer-theory-1",
            theory_version="2.1.0",
            family_id="family_002",
            bayes_factor=4.2,
            evidence_type="variant_segregation",
            source="clinical_lab",
        )

        assert entry_id is not None
        assert len(self.ledger.pending_entries) == 1
        entry = self.ledger.pending_entries[0]
        assert entry.entry_type == LedgerEntryType.EVIDENCE_ADDED
        assert entry.user_id == "researcher_002"
        assert entry.metadata["evidence_strength"] == "strong"  # BF > 3.0

    def test_record_genomic_analysis(self):
        """Test genomic analysis recording"""
        entry_id = self.ledger.record_genomic_analysis(
            user_id="clinician_001",
            analysis_type="variant_interpretation",
            gene="BRCA1",
            variant="c.185delAG",
            result="pathogenic",
            confidence=0.95,
        )

        assert entry_id is not None
        assert len(self.ledger.pending_entries) == 1
        entry = self.ledger.pending_entries[0]
        assert entry.entry_type == LedgerEntryType.GENOMIC_ANALYSIS
        assert entry.user_id == "clinician_001"
        assert entry.metadata["gene_category"] == "cancer"
        assert entry.metadata["confidence_level"] == "high"

    def test_block_commitment(self):
        """Test automatic block commitment"""
        # Add 10 entries to trigger auto-commit
        for i in range(10):
            self.ledger.record_data_access(
                user_id=f"user_{i:03d}",
                resource_id=f"/resource_{i}",
                action="test_action",
                granted=True,
                consent_types_checked=["test_consent"],
            )

        # Should have committed a block
        assert len(self.ledger.blocks) == 2  # Genesis + 1 new block
        assert len(self.ledger.pending_entries) == 0

        new_block = self.ledger.blocks[1]
        assert len(new_block.entries) == 10
        assert new_block.previous_block_hash == self.ledger.blocks[0].block_hash
        assert len(new_block.block_hash) == 64

    def test_verify_consent(self):
        """Test consent verification"""
        # Record consent
        self.ledger.record_consent(
            user_id="user_005",
            consent_type="research_participation",
            data_categories=["phenotype_data"],
            purpose="Autism research",
            digital_signature="sig_789",
        )

        # Verify consent exists
        assert self.ledger.verify_consent("user_005", "research_participation") is True
        assert self.ledger.verify_consent("user_005", "data_sharing") is False
        assert (
            self.ledger.verify_consent("nonexistent_user", "research_participation")
            is False
        )

    def test_consent_expiry(self):
        """Test consent expiry handling"""
        # Record consent with short expiry
        consent_id = self.ledger.record_consent(
            user_id="user_006",
            consent_type="genomic_analysis",
            data_categories=["genetic_data"],
            purpose="Test expiry",
            digital_signature="sig_exp",
            expiry_days=0,  # Expires immediately
        )

        # Manually set expiry to past
        consent = self.ledger.consent_records[consent_id]
        past_time = (datetime.utcnow() - timedelta(days=1)).isoformat() + "Z"
        consent.expiry_date = past_time

        # Verification should fail and mark as expired
        assert self.ledger.verify_consent("user_006", "genomic_analysis") is False
        assert consent.status == ConsentStatus.EXPIRED

    def test_get_user_consents(self):
        """Test getting user consent records"""
        # Record multiple consents
        self.ledger.record_consent(
            user_id="user_007",
            consent_type="genomic_analysis",
            data_categories=["genetic_data"],
            purpose="Primary analysis",
            digital_signature="sig_1",
        )

        self.ledger.record_consent(
            user_id="user_007",
            consent_type="data_sharing",
            data_categories=["anonymized_data"],
            purpose="Research sharing",
            digital_signature="sig_2",
        )

        consents = self.ledger.get_user_consents("user_007")
        assert len(consents) == 2
        consent_types = [c.consent_type for c in consents]
        assert "genomic_analysis" in consent_types
        assert "data_sharing" in consent_types

    def test_get_audit_trail(self):
        """Test getting user audit trail"""
        user_id = "user_008"

        # Create various entries for user
        self.ledger.record_consent(
            user_id=user_id,
            consent_type="genomic_analysis",
            data_categories=["genetic_data"],
            purpose="Research",
            digital_signature="sig_audit",
        )

        self.ledger.record_data_access(
            user_id=user_id,
            resource_id="/genes/SHANK3",
            action="view_gene",
            granted=True,
            consent_types_checked=["genomic_analysis"],
        )

        self.ledger.record_genomic_analysis(
            user_id=user_id,
            analysis_type="variant_interpretation",
            gene="SHANK3",
            variant="c.3679C>T",
            result="likely_pathogenic",
            confidence=0.85,
        )

        # Get audit trail
        audit_trail = self.ledger.get_audit_trail(user_id)
        assert len(audit_trail) == 3

        # Verify entry types
        entry_types = [entry.entry_type for entry in audit_trail]
        assert LedgerEntryType.CONSENT_GRANTED in entry_types
        assert LedgerEntryType.DATA_ACCESS in entry_types
        assert LedgerEntryType.GENOMIC_ANALYSIS in entry_types

        # Verify sorted by timestamp (newest first)
        timestamps = [entry.timestamp for entry in audit_trail]
        assert timestamps == sorted(timestamps, reverse=True)

    def test_get_ledger_entry(self):
        """Test getting specific ledger entry"""
        entry_id = self.ledger.record_data_access(
            user_id="user_009",
            resource_id="/test_resource",
            action="test_action",
            granted=True,
            consent_types_checked=["test_consent"],
        )

        # Get entry from pending
        entry = self.ledger.get_ledger_entry(entry_id)
        assert entry is not None
        assert entry.entry_id == entry_id
        assert entry.user_id == "user_009"

        # Force commit block
        self.ledger.force_commit_block()

        # Get entry from committed block
        entry = self.ledger.get_ledger_entry(entry_id)
        assert entry is not None
        assert entry.entry_id == entry_id
        assert len(entry.block_hash) == 64

    def test_verify_chain_integrity(self):
        """Test blockchain integrity verification"""
        # Add some entries and commit blocks
        for i in range(15):  # Will create 1 full block + pending
            self.ledger.record_data_access(
                user_id=f"user_{i:03d}",
                resource_id=f"/resource_{i}",
                action="integrity_test",
                granted=True,
                consent_types_checked=["test_consent"],
            )

        # Force commit remaining entries
        self.ledger.force_commit_block()

        # Verify integrity
        assert self.ledger.verify_chain_integrity() is True

        # Tamper with a block hash
        if len(self.ledger.blocks) > 1:
            self.ledger.blocks[1].block_hash = "tampered_hash"
            assert self.ledger.verify_chain_integrity() is False

    def test_blockchain_stats(self):
        """Test blockchain statistics"""
        # Add various types of entries
        self.ledger.record_consent(
            user_id="stats_user",
            consent_type="genomic_analysis",
            data_categories=["genetic_data"],
            purpose="Stats test",
            digital_signature="sig_stats",
        )

        self.ledger.record_data_access(
            user_id="stats_user",
            resource_id="/stats_resource",
            action="stats_action",
            granted=True,
            consent_types_checked=["genomic_analysis"],
        )

        stats = self.ledger.get_blockchain_stats()

        assert "total_blocks" in stats
        assert "total_entries" in stats
        assert "pending_entries" in stats
        assert "entry_types" in stats
        assert "consent_stats" in stats
        assert "unique_users" in stats
        assert "chain_integrity" in stats

        assert stats["total_blocks"] >= 1  # At least genesis
        assert stats["total_entries"] >= 2  # At least our 2 entries
        assert stats["unique_users"] >= 1
        assert stats["chain_integrity"] is True

        # Check entry type breakdown
        assert "consent_granted" in stats["entry_types"]
        assert "data_access" in stats["entry_types"]

        # Check consent stats
        consent_stats = stats["consent_stats"]
        assert "total_consents" in consent_stats
        assert "active_consents" in consent_stats
        assert consent_stats["active_consents"] >= 1

    def test_force_commit_block(self):
        """Test force committing blocks"""
        # Add a few entries (less than auto-commit threshold)
        for i in range(3):
            self.ledger.record_data_access(
                user_id=f"force_user_{i}",
                resource_id=f"/force_resource_{i}",
                action="force_test",
                granted=True,
                consent_types_checked=["test_consent"],
            )

        assert len(self.ledger.pending_entries) == 3
        assert len(self.ledger.blocks) == 1  # Only genesis

        # Force commit
        block_id = self.ledger.force_commit_block()

        assert block_id != ""
        assert len(self.ledger.pending_entries) == 0
        assert len(self.ledger.blocks) == 2  # Genesis + new block

        new_block = self.ledger.blocks[1]
        assert len(new_block.entries) == 3
        assert new_block.block_id == block_id

    def test_hash_calculation(self):
        """Test hash calculation consistency"""
        test_data = "test_data_for_hashing"
        hash1 = self.ledger._calculate_hash(test_data)
        hash2 = self.ledger._calculate_hash(test_data)

        assert hash1 == hash2
        assert len(hash1) == 64  # SHA-256 produces 64-char hex string

        # Different data should produce different hashes
        hash3 = self.ledger._calculate_hash("different_data")
        assert hash1 != hash3

    def test_merkle_root_calculation(self):
        """Test Merkle root calculation"""
        # Empty entries
        merkle_root = self.ledger._calculate_merkle_root([])
        assert merkle_root == "0" * 64

        # Add some entries
        entries = []
        for i in range(4):
            self.ledger.record_data_access(
                user_id=f"merkle_user_{i}",
                resource_id=f"/merkle_resource_{i}",
                action="merkle_test",
                granted=True,
                consent_types_checked=["test_consent"],
            )
            entries.append(self.ledger.pending_entries[-1])

        merkle_root = self.ledger._calculate_merkle_root(entries)
        assert len(merkle_root) == 64
        assert merkle_root != "0" * 64

        # Same entries should produce same Merkle root
        merkle_root2 = self.ledger._calculate_merkle_root(entries)
        assert merkle_root == merkle_root2

    def test_gene_categorization(self):
        """Test gene categorization for metadata"""
        assert self.ledger._categorize_gene("SHANK3") == "autism"
        assert self.ledger._categorize_gene("BRCA1") == "cancer"
        assert self.ledger._categorize_gene("UNKNOWN_GENE") == "other"

    def test_multiple_consent_types_same_user(self):
        """Test user with multiple consent types"""
        user_id = "multi_consent_user"

        # Record different consent types
        consent_id1 = self.ledger.record_consent(
            user_id=user_id,
            consent_type="genomic_analysis",
            data_categories=["genetic_data"],
            purpose="Primary analysis",
            digital_signature="sig_multi_1",
        )

        self.ledger.record_consent(
            user_id=user_id,
            consent_type="data_sharing",
            data_categories=["anonymized_data"],
            purpose="Research sharing",
            digital_signature="sig_multi_2",
        )

        # Verify both consents
        assert self.ledger.verify_consent(user_id, "genomic_analysis") is True
        assert self.ledger.verify_consent(user_id, "data_sharing") is True
        assert self.ledger.verify_consent(user_id, "research_participation") is False

        # Withdraw one consent
        success = self.ledger.withdraw_consent(
            user_id, consent_id1, "Partial withdrawal"
        )
        assert success is True

        # Verify only one consent remains active
        assert self.ledger.verify_consent(user_id, "genomic_analysis") is False
        assert self.ledger.verify_consent(user_id, "data_sharing") is True


if __name__ == "__main__":
    pytest.main([__file__])
