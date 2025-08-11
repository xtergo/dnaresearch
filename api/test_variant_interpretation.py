"""Tests for variant interpretation functionality"""

from fastapi.testclient import TestClient
from main import app
from variant_interpreter import ConfidenceLevel, VariantImpact, VariantInterpreter

client = TestClient(app)


class TestVariantInterpreter:
    """Test the VariantInterpreter class"""

    def setup_method(self):
        self.interpreter = VariantInterpreter()

    def test_interpret_brca1_pathogenic_variant(self):
        """Test interpretation of known pathogenic BRCA1 variant"""
        result = self.interpreter.interpret_variant("BRCA1", "c.185delAG")

        assert result.gene == "BRCA1"
        assert result.variant == "c.185delAG"
        assert result.impact == VariantImpact.PATHOGENIC
        assert result.confidence == ConfidenceLevel.HIGH
        assert "breast and ovarian cancer" in result.parent_explanation
        assert "genetic counseling" in result.recommendations[0].lower()

    def test_interpret_shank3_deletion(self):
        """Test interpretation of SHANK3 deletion"""
        result = self.interpreter.interpret_variant("SHANK3", "c.3679del")

        assert result.gene == "SHANK3"
        assert result.impact == VariantImpact.LIKELY_PATHOGENIC
        assert result.confidence == ConfidenceLevel.MEDIUM
        assert "autism spectrum disorder" in result.parent_explanation

    def test_interpret_uncertain_variant(self):
        """Test interpretation of uncertain significance variant"""
        result = self.interpreter.interpret_variant("BRCA1", "c.1234A>G")

        assert result.impact == VariantImpact.UNCERTAIN
        assert "not sure" in result.parent_explanation
        assert "more research" in result.parent_explanation

    def test_classify_variant_types(self):
        """Test variant type classification"""
        assert self.interpreter._classify_variant_type("c.185delAG") == "deletion"
        assert self.interpreter._classify_variant_type("c.1234A>G") == "missense"
        assert self.interpreter._classify_variant_type("c.1234insT") == "insertion"
        assert self.interpreter._classify_variant_type("c.1234dup") == "duplication"

    def test_get_gene_summary(self):
        """Test gene summary functionality"""
        summary = self.interpreter.get_gene_summary("BRCA1")

        assert summary["gene"] == "BRCA1"
        assert summary["condition"] == "breast and ovarian cancer"
        assert summary["inheritance_pattern"] == "autosomal dominant"
        assert summary["penetrance"] == "high"

    def test_get_unknown_gene_summary(self):
        """Test gene summary for unknown gene"""
        summary = self.interpreter.get_gene_summary("UNKNOWN")

        assert summary["gene"] == "UNKNOWN"
        assert summary["condition"] == "Unknown condition"
        assert summary["inheritance_pattern"] == "Unknown"


class TestVariantInterpretationAPI:
    """Test the variant interpretation API endpoints"""

    def test_interpret_variant_endpoint_success(self):
        """Test successful variant interpretation"""
        response = client.post(
            "/genes/BRCA1/interpret", json={"variant": "c.185delAG", "vcf_data": None}
        )

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "BRCA1"
        assert data["variant"] == "c.185delAG"
        assert data["impact"] == "pathogenic"
        assert data["confidence"] == "high"
        assert "parent_explanation" in data
        assert "technical_explanation" in data
        assert "recommendations" in data
        assert isinstance(data["recommendations"], list)
        assert len(data["recommendations"]) > 0

    def test_interpret_variant_with_vcf_data(self):
        """Test variant interpretation with VCF data"""
        response = client.post(
            "/genes/SHANK3/interpret",
            json={
                "variant": "c.3679del",
                "vcf_data": "#VCFV4.2\n22\t51150000\t.\tAT\tA\t60\tPASS",
            },
        )

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "SHANK3"
        assert data["impact"] == "likely_pathogenic"
        assert "autism spectrum disorder" in data["parent_explanation"]

    def test_interpret_uncertain_variant(self):
        """Test interpretation of uncertain variant"""
        response = client.post("/genes/BRCA2/interpret", json={"variant": "c.1234A>G"})

        assert response.status_code == 200
        data = response.json()

        assert data["impact"] == "uncertain"
        assert "not sure" in data["parent_explanation"]
        assert "genetic counseling" in data["recommendations"][0].lower()

    def test_get_gene_summary_endpoint(self):
        """Test gene summary endpoint"""
        response = client.get("/genes/BRCA1/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "BRCA1"
        assert data["condition"] == "breast and ovarian cancer"
        assert data["inheritance_pattern"] == "autosomal dominant"
        assert data["penetrance"] == "high"
        assert data["recommended_screening"] == "enhanced breast/ovarian screening"

    def test_get_gene_summary_unknown_gene(self):
        """Test gene summary for unknown gene"""
        response = client.get("/genes/UNKNOWN/summary")

        assert response.status_code == 200
        data = response.json()

        assert data["gene"] == "UNKNOWN"
        assert data["condition"] == "Unknown condition"

    def test_variant_interpretation_caching(self):
        """Test that variant interpretations are cached"""
        # First request
        response1 = client.post(
            "/genes/BRCA1/interpret", json={"variant": "c.185delAG"}
        )

        # Second identical request should be cached
        response2 = client.post(
            "/genes/BRCA1/interpret", json={"variant": "c.185delAG"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()

    def test_gene_summary_caching(self):
        """Test that gene summaries are cached"""
        # First request
        response1 = client.get("/genes/BRCA1/summary")

        # Second request should be cached
        response2 = client.get("/genes/BRCA1/summary")

        assert response1.status_code == 200
        assert response2.status_code == 200
        assert response1.json() == response2.json()


class TestVariantInterpretationContent:
    """Test the content quality of variant interpretations"""

    def setup_method(self):
        self.interpreter = VariantInterpreter()

    def test_parent_explanation_readability(self):
        """Test that parent explanations are readable and appropriate"""
        result = self.interpreter.interpret_variant("BRCA1", "c.185delAG")

        explanation = result.parent_explanation

        # Should be readable (no technical jargon)
        assert "pathogenic" not in explanation.lower()
        assert "variant" not in explanation.lower()

        # Should be informative
        assert "BRCA1" in explanation
        assert "breast and ovarian cancer" in explanation
        assert len(explanation) > 50  # Substantial explanation

    def test_technical_explanation_detail(self):
        """Test that technical explanations contain appropriate detail"""
        result = self.interpreter.interpret_variant("BRCA1", "c.185delAG")

        explanation = result.technical_explanation

        # Should contain technical terms
        assert "ACMG" in explanation or "AMP" in explanation
        assert "deletion" in explanation
        assert result.impact.value.replace("_", " ") in explanation

    def test_recommendations_appropriateness(self):
        """Test that recommendations are appropriate for variant impact"""
        # Pathogenic variant should have strong recommendations
        pathogenic_result = self.interpreter.interpret_variant("BRCA1", "c.185delAG")
        assert "genetic counseling" in pathogenic_result.recommendations[0].lower()
        assert len(pathogenic_result.recommendations) >= 3

        # Uncertain variant should have cautious recommendations
        uncertain_result = self.interpreter.interpret_variant("BRCA1", "c.1234A>G")
        recommendations_text = " ".join(uncertain_result.recommendations).lower()
        assert "genetic counseling" in recommendations_text
        assert (
            "re-evaluation" in recommendations_text
            or "periodic" in recommendations_text
        )

    def test_confidence_levels_appropriate(self):
        """Test that confidence levels match variant types"""
        # Known pathogenic deletion should be high confidence
        pathogenic = self.interpreter.interpret_variant("BRCA1", "c.185delAG")
        assert pathogenic.confidence == ConfidenceLevel.HIGH

        # Missense variant should be lower confidence
        missense = self.interpreter.interpret_variant("BRCA1", "c.1234A>G")
        assert missense.confidence in [ConfidenceLevel.LOW, ConfidenceLevel.MEDIUM]

    def test_population_frequency_estimates(self):
        """Test that population frequencies are reasonable"""
        result = self.interpreter.interpret_variant("BRCA1", "c.185delAG")

        assert result.population_frequency is not None
        assert 0 <= result.population_frequency <= 1
        assert result.population_frequency < 0.01  # Should be rare

    def test_evidence_sources_included(self):
        """Test that evidence sources are provided"""
        result = self.interpreter.interpret_variant("BRCA1", "c.185delAG")

        assert len(result.evidence_sources) > 0
        assert any("ClinVar" in source for source in result.evidence_sources)
        assert any(
            "ACMG" in source or "AMP" in source for source in result.evidence_sources
        )


class TestVariantInterpretationEdgeCases:
    """Test edge cases and error handling"""

    def test_empty_variant_string(self):
        """Test handling of empty variant string"""
        interpreter = VariantInterpreter()
        result = interpreter.interpret_variant("BRCA1", "")

        # Should still return a result, likely uncertain
        assert result.impact == VariantImpact.UNCERTAIN
        assert result.confidence == ConfidenceLevel.LOW

    def test_malformed_variant_notation(self):
        """Test handling of malformed HGVS notation"""
        interpreter = VariantInterpreter()
        result = interpreter.interpret_variant("BRCA1", "invalid_variant")

        # Should classify as unknown type and uncertain impact
        assert result.impact == VariantImpact.UNCERTAIN

    def test_case_insensitive_gene_names(self):
        """Test that gene names are handled case-insensitively"""
        interpreter = VariantInterpreter()

        result_upper = interpreter.interpret_variant("BRCA1", "c.185delAG")
        result_lower = interpreter.interpret_variant("brca1", "c.185delAG")

        # Should produce same results regardless of case
        assert result_upper.impact == result_lower.impact
        assert result_upper.confidence == result_lower.confidence

    def test_api_error_handling(self):
        """Test API error handling for invalid requests"""
        # Test missing required field
        response = client.post("/genes/BRCA1/interpret", json={})
        assert response.status_code == 422  # Validation error

        # Test with valid but minimal data
        response = client.post("/genes/BRCA1/interpret", json={"variant": "c.185delAG"})
        assert response.status_code == 200
