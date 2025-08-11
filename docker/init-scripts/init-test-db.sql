-- Test database initialization (same schema as dev, no test data)

-- Create extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Create tables for anchor/diff storage
CREATE TABLE IF NOT EXISTS anchor_sequences (
    id VARCHAR PRIMARY KEY,
    sequence_hash VARCHAR UNIQUE NOT NULL,
    reference_genome VARCHAR DEFAULT 'GRCh38',
    quality_score FLOAT,
    usage_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS genomic_differences (
    id VARCHAR PRIMARY KEY,
    anchor_id VARCHAR REFERENCES anchor_sequences(id),
    individual_id VARCHAR NOT NULL,
    position INTEGER NOT NULL,
    reference_allele VARCHAR NOT NULL,
    alternate_allele VARCHAR NOT NULL,
    quality_score FLOAT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_genomic_diff_individual ON genomic_differences(individual_id);
CREATE INDEX IF NOT EXISTS idx_genomic_diff_position ON genomic_differences(position);
CREATE INDEX IF NOT EXISTS idx_anchor_usage ON anchor_sequences(usage_count DESC);