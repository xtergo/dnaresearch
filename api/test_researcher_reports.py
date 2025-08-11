"""
Tests for Researcher Reports System

Comprehensive tests for technical report generation functionality.
"""

from fastapi.testclient import TestClient
from main import app
from researcher_reports import (
    EvidenceLevel,
    ReportType,
    ResearcherReportGenerator,
)

client = TestClient(app)


class TestResearcherReportGenerator:
    """Test researcher report generation functionality"""

    def setup_method(self):
        """Set up test fixtures"""
        self.report_generator = ResearcherReportGenerator()

    def test_generate_variant_report_brca1(self):
        """Test generating variant report for BRCA1"""
        report = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")

        assert report.report_type == ReportType.VARIANT_ANALYSIS
        assert report.gene == "BRCA1"
        assert report.variant == "c.185delAG"
        assert "pathogenic" in report.summary.lower()
        assert report.confidence_score > 0.8
        assert len(report.recommendations) > 0
        assert "genetic counseling" in " ".join(report.recommendations).lower()

    def test_generate_variant_report_shank3(self):
        """Test generating variant report for SHANK3"""
        report = self.report_generator.generate_variant_report("SHANK3", "c.3679C>T")

        assert report.gene == "SHANK3"
        assert report.variant == "c.3679C>T"
        assert len(report.variant_annotations) > 0
        assert (
            report.variant_annotations[0].evidence_level
            == EvidenceLevel.LIKELY_PATHOGENIC
        )
        assert report.confidence_score > 0.5

    def test_generate_variant_report_unknown_gene(self):
        """Test generating variant report for unknown gene"""
        report = self.report_generator.generate_variant_report("UNKNOWN", "c.123A>T")

        assert report.gene == "UNKNOWN"
        assert report.variant == "c.123A>T"
        assert (
            "limited" in report.summary.lower() or "requires" in report.summary.lower()
        )
        assert len(report.variant_annotations) == 0
        assert len(report.population_frequencies) == 0

    def test_generate_gene_report_brca1(self):
        """Test generating gene summary report for BRCA1"""
        report = self.report_generator.generate_gene_report("BRCA1")

        assert report.report_type == ReportType.GENE_SUMMARY
        assert report.gene == "BRCA1"
        assert report.variant is None
        assert "tumor suppressor" in report.summary.lower()
        assert report.clinical_significance == "High clinical significance"
        assert len(report.literature_references) > 0
        assert report.confidence_score > 0.7

    def test_generate_gene_report_shank3(self):
        """Test generating gene summary report for SHANK3"""
        report = self.report_generator.generate_gene_report("SHANK3")

        assert report.gene == "SHANK3"
        assert (
            "synaptic" in report.summary.lower() or "autism" in report.summary.lower()
        )
        assert len(report.literature_references) > 0
        assert "autism" in report.detailed_analysis.lower()

    def test_variant_annotation_structure(self):
        """Test variant annotation data structure"""
        report = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")

        if report.variant_annotations:
            annotation = report.variant_annotations[0]
            assert hasattr(annotation, "variant")
            assert hasattr(annotation, "gene")
            assert hasattr(annotation, "consequence")
            assert hasattr(annotation, "amino_acid_change")
            assert hasattr(annotation, "conservation_score")
            assert hasattr(annotation, "pathogenicity_score")
            assert hasattr(annotation, "evidence_level")

    def test_population_frequency_structure(self):
        """Test population frequency data structure"""
        report = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")

        if report.population_frequencies:
            freq = report.population_frequencies[0]
            assert hasattr(freq, "population")
            assert hasattr(freq, "frequency")
            assert hasattr(freq, "allele_count")
            assert hasattr(freq, "total_alleles")
            assert hasattr(freq, "source")
            assert freq.frequency >= 0.0
            assert freq.allele_count >= 0
            assert freq.total_alleles > 0

    def test_literature_reference_structure(self):
        """Test literature reference data structure"""
        report = self.report_generator.generate_gene_report("BRCA1")

        if report.literature_references:
            ref = report.literature_references[0]
            assert hasattr(ref, "pmid")
            assert hasattr(ref, "title")
            assert hasattr(ref, "authors")
            assert hasattr(ref, "journal")
            assert hasattr(ref, "year")
            assert hasattr(ref, "relevance_score")
            assert len(ref.pmid) > 0
            assert len(ref.title) > 0
            assert len(ref.authors) > 0
            assert ref.year > 1990
            assert 0.0 <= ref.relevance_score <= 1.0

    def test_confidence_score_calculation(self):
        """Test confidence score calculation"""
        # Test with known gene/variant
        report1 = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")

        # Test with unknown gene/variant
        report2 = self.report_generator.generate_variant_report("UNKNOWN", "c.123A>T")

        # Known variant should have higher confidence
        assert report1.confidence_score > report2.confidence_score
        assert 0.0 <= report1.confidence_score <= 1.0
        assert 0.0 <= report2.confidence_score <= 1.0

    def test_report_metadata(self):
        """Test report metadata"""
        report = self.report_generator.generate_variant_report(
            "BRCA1", "c.185delAG", "vcf_data"
        )

        assert "vcf_provided" in report.metadata
        assert report.metadata["vcf_provided"] is True
        assert "annotation_sources" in report.metadata
        assert "analysis_version" in report.metadata

    def test_gene_report_metadata(self):
        """Test gene report metadata"""
        report = self.report_generator.generate_gene_report("BRCA1")

        assert "total_variants" in report.metadata
        assert "pathogenic_variants" in report.metadata
        assert "analysis_version" in report.metadata
        assert report.metadata["total_variants"] >= 0
        assert report.metadata["pathogenic_variants"] >= 0

    def test_clinical_significance_classification(self):
        """Test clinical significance classification"""
        # Test pathogenic variant
        report1 = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")
        assert "pathogenic" in report1.clinical_significance.lower()

        # Test likely pathogenic variant
        report2 = self.report_generator.generate_variant_report("SHANK3", "c.3679C>T")
        assert "likely pathogenic" in report2.clinical_significance.lower()

    def test_recommendations_generation(self):
        """Test recommendations generation"""
        report = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")

        assert len(report.recommendations) > 0
        recommendations_text = " ".join(report.recommendations).lower()
        assert (
            "genetic counseling" in recommendations_text
            or "screening" in recommendations_text
        )

    def test_detailed_analysis_content(self):
        """Test detailed analysis content"""
        report = self.report_generator.generate_variant_report("BRCA1", "c.185delAG")

        assert len(report.detailed_analysis) > 100  # Should be substantial
        assert "molecular consequences" in report.detailed_analysis.lower()
        assert "clinical interpretation" in report.detailed_analysis.lower()

    def test_gene_detailed_analysis_content(self):
        """Test gene detailed analysis content"""
        report = self.report_generator.generate_gene_report("BRCA1")

        assert len(report.detailed_analysis) > 100
        assert "variant spectrum" in report.detailed_analysis.lower()
        assert "literature evidence" in report.detailed_analysis.lower()
        assert "clinical implications" in report.detailed_analysis.lower()


class TestResearcherReportsAPI:
    """Test researcher reports API endpoints"""

    def test_generate_variant_report_endpoint(self):
        """Test variant report generation endpoint"""
        request_data = {
            "gene": "BRCA1",
            "variant": "c.185delAG",
            "vcf_data": "#VCFV4.2\n17\t43094692\t.\tAG\t.\t60\tPASS",
        }

        response = client.post("/reports/variant", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "report_id" in data
        assert data["report_type"] == "variant_analysis"
        assert data["gene"] == "BRCA1"
        assert data["variant"] == "c.185delAG"
        assert "summary" in data
        assert "detailed_analysis" in data
        assert "clinical_significance" in data
        assert "recommendations" in data
        assert "confidence_score" in data
        assert "generated_at" in data

    def test_generate_variant_report_minimal(self):
        """Test variant report generation with minimal data"""
        request_data = {"gene": "SHANK3", "variant": "c.3679C>T"}

        response = client.post("/reports/variant", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "SHANK3"
        assert data["variant"] == "c.3679C>T"
        assert len(data["variant_annotations"]) > 0
        assert len(data["literature_references"]) > 0

    def test_generate_gene_report_endpoint(self):
        """Test gene report generation endpoint"""
        request_data = {"gene": "BRCA1"}

        response = client.post("/reports/gene", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert "report_id" in data
        assert data["report_type"] == "gene_summary"
        assert data["gene"] == "BRCA1"
        assert "summary" in data
        assert "detailed_analysis" in data
        assert "clinical_significance" in data
        assert "total_variants" in data
        assert "pathogenic_variants" in data
        assert "literature_references" in data

    def test_variant_report_caching(self):
        """Test variant report caching"""
        request_data = {"gene": "BRCA1", "variant": "c.185delAG"}

        # First request
        response1 = client.post("/reports/variant", json=request_data)
        assert response1.status_code == 200
        data1 = response1.json()

        # Second request (should be cached)
        response2 = client.post("/reports/variant", json=request_data)
        assert response2.status_code == 200
        data2 = response2.json()

        # Should have same report_id and generated_at (cached)
        assert data1["report_id"] == data2["report_id"]
        assert data1["generated_at"] == data2["generated_at"]

    def test_gene_report_caching(self):
        """Test gene report caching"""
        request_data = {"gene": "SHANK3"}

        # First request
        response1 = client.post("/reports/gene", json=request_data)
        assert response1.status_code == 200
        data1 = response1.json()

        # Second request (should be cached)
        response2 = client.post("/reports/gene", json=request_data)
        assert response2.status_code == 200
        data2 = response2.json()

        # Should have same report_id (cached)
        assert data1["report_id"] == data2["report_id"]

    def test_variant_report_response_structure(self):
        """Test variant report response structure"""
        request_data = {"gene": "BRCA1", "variant": "c.185delAG"}

        response = client.post("/reports/variant", json=request_data)
        data = response.json()

        # Check required fields
        required_fields = [
            "report_id",
            "report_type",
            "gene",
            "variant",
            "summary",
            "detailed_analysis",
            "clinical_significance",
            "recommendations",
            "confidence_score",
            "generated_at",
        ]
        for field in required_fields:
            assert field in data

        # Check array fields
        assert isinstance(data["recommendations"], list)
        assert isinstance(data["variant_annotations"], list)
        assert isinstance(data["population_frequencies"], list)
        assert isinstance(data["literature_references"], list)

    def test_gene_report_response_structure(self):
        """Test gene report response structure"""
        request_data = {"gene": "BRCA1"}

        response = client.post("/reports/gene", json=request_data)
        data = response.json()

        # Check required fields
        required_fields = [
            "report_id",
            "report_type",
            "gene",
            "summary",
            "detailed_analysis",
            "clinical_significance",
            "recommendations",
            "confidence_score",
            "generated_at",
            "total_variants",
            "pathogenic_variants",
        ]
        for field in required_fields:
            assert field in data

        # Check data types
        assert isinstance(data["total_variants"], int)
        assert isinstance(data["pathogenic_variants"], int)
        assert isinstance(data["confidence_score"], float)

    def test_variant_annotation_response_structure(self):
        """Test variant annotation in response"""
        request_data = {"gene": "BRCA1", "variant": "c.185delAG"}

        response = client.post("/reports/variant", json=request_data)
        data = response.json()

        if data["variant_annotations"]:
            annotation = data["variant_annotations"][0]
            required_fields = [
                "consequence",
                "amino_acid_change",
                "conservation_score",
                "pathogenicity_score",
                "evidence_level",
            ]
            for field in required_fields:
                assert field in annotation

    def test_population_frequency_response_structure(self):
        """Test population frequency in response"""
        request_data = {"gene": "BRCA1", "variant": "c.185delAG"}

        response = client.post("/reports/variant", json=request_data)
        data = response.json()

        if data["population_frequencies"]:
            freq = data["population_frequencies"][0]
            required_fields = ["population", "frequency", "source"]
            for field in required_fields:
                assert field in freq

    def test_literature_reference_response_structure(self):
        """Test literature reference in response"""
        request_data = {"gene": "BRCA1"}

        response = client.post("/reports/gene", json=request_data)
        data = response.json()

        if data["literature_references"]:
            ref = data["literature_references"][0]
            required_fields = ["pmid", "title", "authors", "journal", "year"]
            for field in required_fields:
                assert field in ref

    def test_unknown_gene_variant_report(self):
        """Test report generation for unknown gene/variant"""
        request_data = {"gene": "UNKNOWN_GENE", "variant": "c.999A>T"}

        response = client.post("/reports/variant", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "UNKNOWN_GENE"
        assert data["variant"] == "c.999A>T"
        assert len(data["variant_annotations"]) == 0
        assert len(data["population_frequencies"]) == 0
        assert data["confidence_score"] < 0.5  # Should be low for unknown

    def test_unknown_gene_report(self):
        """Test gene report for unknown gene"""
        request_data = {"gene": "UNKNOWN_GENE"}

        response = client.post("/reports/gene", json=request_data)

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "UNKNOWN_GENE"
        assert data["total_variants"] == 0
        assert data["pathogenic_variants"] == 0
        assert len(data["literature_references"]) == 0

    def test_report_error_handling(self):
        """Test error handling in report generation"""
        # Test missing required field
        response = client.post("/reports/variant", json={"gene": "BRCA1"})
        assert response.status_code == 422  # Validation error

        # Test empty gene
        response = client.post("/reports/gene", json={})
        assert response.status_code == 422  # Validation error
