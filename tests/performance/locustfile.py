"""
Load testing scenarios for DNA Research Platform
Uses Locust to simulate realistic user behavior and measure performance
"""

import json
import random
from locust import HttpUser, task, tag, between


class DNAResearchUser(HttpUser):
    """Simulates a researcher using the DNA Research Platform"""
    
    wait_time = between(1, 3)  # Wait 1-3 seconds between requests
    
    def on_start(self):
        """Initialize test data"""
        self.gene_symbols = ["BRCA1", "BRCA2", "SHANK3", "APOE", "CFTR", "NRXN1", "SYNGAP1"]
        self.theory_ids = ["theory_001", "theory_002", "theory_003"]
        self.user_ids = ["user_001", "user_002", "user_003"]
    
    @task(10)
    @tag("health")
    def health_check(self):
        """Test health endpoint - most frequent operation"""
        self.client.get("/health")
    
    @task(8)
    @tag("gene_search")
    def search_genes_by_symbol(self):
        """Test gene search by symbol"""
        gene = random.choice(self.gene_symbols)
        self.client.get(f"/genes/search?query={gene}")
    
    @task(5)
    @tag("gene_search")
    def search_genes_by_coordinates(self):
        """Test gene search by genomic coordinates"""
        # SHANK3 coordinates
        self.client.get("/genes/search?query=22:51150000-51180000")
    
    @task(6)
    @tag("gene_search")
    def search_genes_semantic(self):
        """Test semantic gene search"""
        terms = ["autism", "cancer", "neurological"]
        term = random.choice(terms)
        self.client.get(f"/genes/search?query={term}")
    
    @task(4)
    @tag("variant_interpretation")
    def interpret_variant(self):
        """Test variant interpretation"""
        gene = random.choice(self.gene_symbols)
        variant_data = {
            "chromosome": "17",
            "position": 43094692,
            "ref": "G",
            "alt": "A",
            "gene_symbol": gene
        }
        self.client.post(f"/genes/{gene}/interpret", json=variant_data)
    
    @task(3)
    @tag("researcher_reports")
    def get_researcher_report(self):
        """Test researcher report generation"""
        gene = random.choice(self.gene_symbols)
        self.client.get(f"/genes/{gene}/report")
    
    @task(2)
    @tag("theory_exec")
    def execute_theory(self):
        """Test theory execution - heavy operation"""
        theory_id = random.choice(self.theory_ids)
        execution_data = {
            "vcf_data": "sample_vcf_content",
            "family_id": f"family_{random.randint(1, 100)}"
        }
        self.client.post(f"/theories/{theory_id}/execute", json=execution_data)
    
    @task(3)
    @tag("theory_management")
    def list_theories(self):
        """Test theory listing"""
        params = {
            "limit": 20,
            "offset": 0,
            "sort_by": "posterior_probability"
        }
        self.client.get("/theories", params=params)
    
    @task(2)
    @tag("theory_management")
    def fork_theory(self):
        """Test theory forking"""
        theory_id = random.choice(self.theory_ids)
        fork_data = {
            "name": f"Forked Theory {random.randint(1, 1000)}",
            "description": "Performance test fork",
            "modifications": {"scope": "extended"}
        }
        self.client.post(f"/theories/{theory_id}/fork", json=fork_data)
    
    @task(4)
    @tag("file_upload")
    def request_upload_url(self):
        """Test secure file upload URL generation"""
        upload_data = {
            "filename": f"test_data_{random.randint(1, 1000)}.vcf",
            "file_type": "vcf",
            "file_size": random.randint(1000000, 50000000)  # 1MB to 50MB
        }
        self.client.post("/files/presign", json=upload_data)
    
    @task(3)
    @tag("consent_management")
    def check_consent(self):
        """Test consent validation"""
        user_id = random.choice(self.user_ids)
        self.client.get(f"/consent/{user_id}/validate")
    
    @task(2)
    @tag("collaboration")
    def get_theory_comments(self):
        """Test theory collaboration features"""
        theory_id = random.choice(self.theory_ids)
        self.client.get(f"/theories/{theory_id}/comments")
    
    @task(1)
    @tag("evidence_accumulation")
    def add_evidence(self):
        """Test evidence accumulation - infrequent but important"""
        theory_id = random.choice(self.theory_ids)
        evidence_data = {
            "type": "variant_hit",
            "data": {
                "chromosome": "17",
                "position": 43094692,
                "family_id": f"family_{random.randint(1, 100)}"
            },
            "weight": random.uniform(0.1, 1.0)
        }
        self.client.post(f"/theories/{theory_id}/evidence", json=evidence_data)


class HighVolumeUser(HttpUser):
    """Simulates high-volume automated systems"""
    
    wait_time = between(0.1, 0.5)  # Much faster requests
    weight = 2  # Less common user type
    
    @task(20)
    @tag("health")
    def rapid_health_checks(self):
        """Rapid health monitoring"""
        self.client.get("/health")
    
    @task(10)
    @tag("gene_search")
    def batch_gene_search(self):
        """Batch gene searches"""
        genes = ["BRCA1", "BRCA2", "SHANK3"]
        for gene in genes:
            self.client.get(f"/genes/search?query={gene}")


class CasualUser(HttpUser):
    """Simulates casual users (parents) with simpler usage patterns"""
    
    wait_time = between(5, 15)  # Longer think time
    weight = 3  # More common user type
    
    @task(5)
    @tag("variant_interpretation")
    def simple_variant_lookup(self):
        """Simple variant interpretation for parents"""
        gene = random.choice(["BRCA1", "BRCA2", "CFTR"])
        variant_data = {
            "chromosome": "17",
            "position": 43094692,
            "ref": "G",
            "alt": "A",
            "gene_symbol": gene
        }
        self.client.post(f"/genes/{gene}/interpret", json=variant_data)
    
    @task(3)
    @tag("gene_search")
    def search_by_condition(self):
        """Search genes by medical condition"""
        conditions = ["autism", "cancer", "cystic fibrosis"]
        condition = random.choice(conditions)
        self.client.get(f"/genes/search?query={condition}")
    
    @task(1)
    @tag("consent_management")
    def view_consent_status(self):
        """Check consent status"""
        user_id = f"user_{random.randint(1, 100)}"
        self.client.get(f"/consent/{user_id}/validate")