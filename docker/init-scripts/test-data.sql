-- Test data for development environment

-- Insert sample anchor sequences
INSERT INTO anchor_sequences (id, sequence_hash, reference_genome, quality_score, usage_count) VALUES
('anchor-001', 'sha256:abc123...', 'GRCh38', 0.95, 5),
('anchor-002', 'sha256:def456...', 'GRCh38', 0.92, 3),
('anchor-003', 'sha256:ghi789...', 'GRCh37', 0.88, 1);

-- Insert sample genomic differences
INSERT INTO genomic_differences (id, anchor_id, individual_id, position, reference_allele, alternate_allele, quality_score) VALUES
('diff-001', 'anchor-001', 'individual-001', 12345, 'A', 'T', 0.98),
('diff-002', 'anchor-001', 'individual-001', 23456, 'G', 'C', 0.95),
('diff-003', 'anchor-001', 'individual-002', 12345, 'A', 'G', 0.97),
('diff-004', 'anchor-002', 'individual-003', 34567, 'C', 'T', 0.93),
('diff-005', 'anchor-002', 'individual-003', 45678, 'T', 'A', 0.91);