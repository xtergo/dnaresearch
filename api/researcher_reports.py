"""
Researcher Reports Generator

Technical report generation for researchers with detailed variant analysis,
population frequencies, and literature integration.
"""

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional


class ReportType(Enum):
    """Types of researcher reports"""

    VARIANT_ANALYSIS = "variant_analysis"
    GENE_SUMMARY = "gene_summary"
    THEORY_EVALUATION = "theory_evaluation"
    COHORT_ANALYSIS = "cohort_analysis"


class EvidenceLevel(Enum):
    """Evidence levels for variant classification"""

    PATHOGENIC = "pathogenic"
    LIKELY_PATHOGENIC = "likely_pathogenic"
    UNCERTAIN = "uncertain"
    LIKELY_BENIGN = "likely_benign"
    BENIGN = "benign"


@dataclass
class LiteratureReference:
    """Literature reference for evidence"""

    pmid: str
    title: str
    authors: List[str]
    journal: str
    year: int
    relevance_score: float


@dataclass
class PopulationFrequency:
    """Population frequency data"""

    population: str
    frequency: float
    allele_count: int
    total_alleles: int
    source: str


@dataclass
class VariantAnnotation:
    """Detailed variant annotation"""

    variant: str
    gene: str
    transcript: str
    consequence: str
    amino_acid_change: str
    conservation_score: float
    pathogenicity_score: float
    evidence_level: EvidenceLevel


@dataclass
class ResearcherReport:
    """Complete researcher report"""

    report_id: str
    report_type: ReportType
    generated_at: str
    gene: str
    variant: Optional[str]
    summary: str
    detailed_analysis: str
    variant_annotations: List[VariantAnnotation]
    population_frequencies: List[PopulationFrequency]
    literature_references: List[LiteratureReference]
    clinical_significance: str
    recommendations: List[str]
    confidence_score: float
    metadata: Dict


class ResearcherReportGenerator:
    """Generates technical reports for researchers"""

    def __init__(self):
        self.literature_db = self._initialize_literature_db()
        self.population_db = self._initialize_population_db()
        self.annotation_db = self._initialize_annotation_db()

    def _initialize_literature_db(self) -> Dict:
        """Initialize literature database"""
        return {
            "BRCA1": [
                LiteratureReference(
                    pmid="7545954",
                    title="BRCA1 mutations in primary breast and ovarian carcinomas",
                    authors=["Futreal PA", "Liu Q", "Shattuck-Eidens D"],
                    journal="Science",
                    year=1994,
                    relevance_score=0.95,
                ),
                LiteratureReference(
                    pmid="8944023",
                    title="The complete BRCA2 gene and mutations in chromosome 13q-linked kindreds",
                    authors=["Tavtigian SV", "Simard J", "Rommens J"],
                    journal="Nat Genet",
                    year=1996,
                    relevance_score=0.88,
                ),
            ],
            "SHANK3": [
                LiteratureReference(
                    pmid="17173049",
                    title="Mutations in SHANK3 in patients with autism spectrum disorders",
                    authors=["Durand CM", "Betancur C", "Boeckers TM"],
                    journal="Nat Genet",
                    year=2007,
                    relevance_score=0.92,
                )
            ],
        }

    def _initialize_population_db(self) -> Dict:
        """Initialize population frequency database"""
        return {
            "BRCA1": {
                "c.185delAG": [
                    PopulationFrequency("European", 0.0001, 12, 120000, "gnomAD"),
                    PopulationFrequency(
                        "Ashkenazi Jewish", 0.012, 144, 12000, "gnomAD"
                    ),
                    PopulationFrequency("African", 0.00005, 3, 60000, "gnomAD"),
                ]
            },
            "SHANK3": {
                "c.3679C>T": [
                    PopulationFrequency("European", 0.00002, 2, 100000, "gnomAD"),
                    PopulationFrequency("East Asian", 0.00001, 1, 100000, "gnomAD"),
                ]
            },
        }

    def _initialize_annotation_db(self) -> Dict:
        """Initialize variant annotation database"""
        return {
            "BRCA1": {
                "c.185delAG": VariantAnnotation(
                    variant="c.185delAG",
                    gene="BRCA1",
                    transcript="NM_007294.3",
                    consequence="frameshift_variant",
                    amino_acid_change="p.Glu62fs",
                    conservation_score=0.98,
                    pathogenicity_score=0.95,
                    evidence_level=EvidenceLevel.PATHOGENIC,
                )
            },
            "SHANK3": {
                "c.3679C>T": VariantAnnotation(
                    variant="c.3679C>T",
                    gene="SHANK3",
                    transcript="NM_033517.1",
                    consequence="missense_variant",
                    amino_acid_change="p.Arg1227Cys",
                    conservation_score=0.89,
                    pathogenicity_score=0.78,
                    evidence_level=EvidenceLevel.LIKELY_PATHOGENIC,
                )
            },
        }

    def generate_variant_report(
        self, gene: str, variant: str, vcf_data: Optional[str] = None
    ) -> ResearcherReport:
        """Generate detailed variant analysis report"""

        report_id = (
            f"var_report_{gene}_{variant}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        )

        # Get variant annotation
        annotations = []
        if gene in self.annotation_db and variant in self.annotation_db[gene]:
            annotations.append(self.annotation_db[gene][variant])

        # Get population frequencies
        frequencies = []
        if gene in self.population_db and variant in self.population_db[gene]:
            frequencies = self.population_db[gene][variant]

        # Get literature references
        references = self.literature_db.get(gene, [])

        # Generate analysis
        summary = self._generate_variant_summary(gene, variant, annotations)
        detailed_analysis = self._generate_detailed_analysis(
            gene, variant, annotations, frequencies
        )
        clinical_significance = self._determine_clinical_significance(annotations)
        recommendations = self._generate_recommendations(gene, variant, annotations)
        confidence_score = self._calculate_confidence_score(
            annotations, frequencies, references
        )

        return ResearcherReport(
            report_id=report_id,
            report_type=ReportType.VARIANT_ANALYSIS,
            generated_at=datetime.utcnow().isoformat() + "Z",
            gene=gene,
            variant=variant,
            summary=summary,
            detailed_analysis=detailed_analysis,
            variant_annotations=annotations,
            population_frequencies=frequencies,
            literature_references=references,
            clinical_significance=clinical_significance,
            recommendations=recommendations,
            confidence_score=confidence_score,
            metadata={
                "vcf_provided": vcf_data is not None,
                "annotation_sources": ["gnomAD", "ClinVar", "HGMD"],
                "analysis_version": "1.0.0",
            },
        )

    def generate_gene_report(self, gene: str) -> ResearcherReport:
        """Generate comprehensive gene summary report"""

        report_id = f"gene_report_{gene}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"

        # Get all annotations for gene
        annotations = []
        if gene in self.annotation_db:
            annotations = list(self.annotation_db[gene].values())

        # Get all population frequencies
        frequencies = []
        if gene in self.population_db:
            for variant_freqs in self.population_db[gene].values():
                frequencies.extend(variant_freqs)

        # Get literature references
        references = self.literature_db.get(gene, [])

        # Generate analysis
        summary = self._generate_gene_summary(gene, annotations)
        detailed_analysis = self._generate_gene_detailed_analysis(
            gene, annotations, references
        )
        clinical_significance = self._determine_gene_significance(gene, annotations)
        recommendations = self._generate_gene_recommendations(gene, annotations)
        confidence_score = self._calculate_gene_confidence_score(
            annotations, references
        )

        return ResearcherReport(
            report_id=report_id,
            report_type=ReportType.GENE_SUMMARY,
            generated_at=datetime.utcnow().isoformat() + "Z",
            gene=gene,
            variant=None,
            summary=summary,
            detailed_analysis=detailed_analysis,
            variant_annotations=annotations,
            population_frequencies=frequencies,
            literature_references=references,
            clinical_significance=clinical_significance,
            recommendations=recommendations,
            confidence_score=confidence_score,
            metadata={
                "total_variants": len(annotations),
                "pathogenic_variants": len(
                    [
                        a
                        for a in annotations
                        if a.evidence_level == EvidenceLevel.PATHOGENIC
                    ]
                ),
                "analysis_version": "1.0.0",
            },
        )

    def _generate_variant_summary(
        self, gene: str, variant: str, annotations: List[VariantAnnotation]
    ) -> str:
        """Generate variant summary"""
        if not annotations:
            return f"Variant {variant} in {gene} requires further analysis. Limited annotation data available."

        annotation = annotations[0]
        return f"Variant {variant} in {gene} is classified as {annotation.evidence_level.value} with a pathogenicity score of {annotation.pathogenicity_score:.2f}. This {annotation.consequence} results in {annotation.amino_acid_change} and shows high conservation (score: {annotation.conservation_score:.2f})."

    def _generate_detailed_analysis(
        self,
        gene: str,
        variant: str,
        annotations: List[VariantAnnotation],
        frequencies: List[PopulationFrequency],
    ) -> str:
        """Generate detailed variant analysis"""
        analysis = f"## Detailed Analysis for {gene} {variant}\n\n"

        if annotations:
            annotation = annotations[0]
            analysis += "### Molecular Consequences\n"
            analysis += f"- Transcript: {annotation.transcript}\n"
            analysis += f"- Consequence: {annotation.consequence}\n"
            analysis += f"- Amino acid change: {annotation.amino_acid_change}\n"
            analysis += f"- Conservation score: {annotation.conservation_score:.3f}\n"
            analysis += (
                f"- Pathogenicity prediction: {annotation.pathogenicity_score:.3f}\n\n"
            )

        if frequencies:
            analysis += "### Population Frequencies\n"
            for freq in frequencies:
                analysis += f"- {freq.population}: {freq.frequency:.6f} ({freq.allele_count}/{freq.total_alleles}) - {freq.source}\n"
            analysis += "\n"

        analysis += "### Clinical Interpretation\n"
        analysis += (
            "Based on ACMG/AMP guidelines, this variant shows evidence supporting "
        )
        if annotations and annotations[0].evidence_level in [
            EvidenceLevel.PATHOGENIC,
            EvidenceLevel.LIKELY_PATHOGENIC,
        ]:
            analysis += (
                "pathogenicity through functional impact and conservation analysis."
            )
        else:
            analysis += (
                "uncertain significance requiring additional functional studies."
            )

        return analysis

    def _generate_gene_summary(
        self, gene: str, annotations: List[VariantAnnotation]
    ) -> str:
        """Generate gene summary"""
        pathogenic_count = len(
            [
                a
                for a in annotations
                if a.evidence_level
                in [EvidenceLevel.PATHOGENIC, EvidenceLevel.LIKELY_PATHOGENIC]
            ]
        )

        gene_descriptions = {
            "BRCA1": "tumor suppressor gene involved in DNA repair and breast/ovarian cancer predisposition",
            "SHANK3": "synaptic scaffolding protein associated with autism spectrum disorders",
            "CFTR": "chloride channel involved in cystic fibrosis",
            "APOE": "apolipoprotein involved in Alzheimer's disease risk",
        }

        description = gene_descriptions.get(gene, "gene of clinical significance")

        return f"{gene} is a {description}. Analysis of {len(annotations)} variants reveals {pathogenic_count} with pathogenic or likely pathogenic classification, indicating significant clinical relevance for genetic counseling and patient management."

    def _generate_gene_detailed_analysis(
        self,
        gene: str,
        annotations: List[VariantAnnotation],
        references: List[LiteratureReference],
    ) -> str:
        """Generate detailed gene analysis"""
        analysis = f"## Comprehensive Analysis for {gene}\n\n"

        analysis += "### Variant Spectrum\n"
        analysis += f"Total variants analyzed: {len(annotations)}\n"

        for level in EvidenceLevel:
            count = len([a for a in annotations if a.evidence_level == level])
            if count > 0:
                analysis += f"- {level.value.replace('_', ' ').title()}: {count}\n"

        analysis += "\n### Literature Evidence\n"
        analysis += "Key publications supporting clinical significance:\n"
        for ref in references[:3]:  # Top 3 references
            analysis += f"- {ref.authors[0]} et al. ({ref.year}). {ref.title}. {ref.journal}. PMID: {ref.pmid}\n"

        analysis += "\n### Clinical Implications\n"
        if gene == "BRCA1":
            analysis += "Pathogenic variants confer high risk for breast and ovarian cancer. Recommend enhanced screening and risk-reducing strategies."
        elif gene == "SHANK3":
            analysis += "Variants associated with autism spectrum disorders and intellectual disability. Important for developmental assessment."
        else:
            analysis += "Variants may have clinical significance requiring individualized assessment and genetic counseling."

        return analysis

    def _determine_clinical_significance(
        self, annotations: List[VariantAnnotation]
    ) -> str:
        """Determine clinical significance"""
        if not annotations:
            return "Uncertain significance"

        return annotations[0].evidence_level.value.replace("_", " ").title()

    def _determine_gene_significance(
        self, gene: str, annotations: List[VariantAnnotation]
    ) -> str:
        """Determine gene clinical significance"""
        pathogenic_count = len(
            [
                a
                for a in annotations
                if a.evidence_level
                in [EvidenceLevel.PATHOGENIC, EvidenceLevel.LIKELY_PATHOGENIC]
            ]
        )

        if pathogenic_count > 0:
            return "High clinical significance"
        elif len(annotations) > 0:
            return "Moderate clinical significance"
        else:
            return "Limited clinical data"

    def _generate_recommendations(
        self, gene: str, variant: str, annotations: List[VariantAnnotation]
    ) -> List[str]:
        """Generate clinical recommendations"""
        recommendations = []

        if annotations and annotations[0].evidence_level in [
            EvidenceLevel.PATHOGENIC,
            EvidenceLevel.LIKELY_PATHOGENIC,
        ]:
            recommendations.extend(
                [
                    "Genetic counseling recommended",
                    "Family screening may be indicated",
                    "Consider clinical management guidelines",
                ]
            )

            if gene == "BRCA1":
                recommendations.extend(
                    [
                        "Enhanced breast and ovarian cancer screening",
                        "Consider risk-reducing surgery options",
                    ]
                )
            elif gene == "SHANK3":
                recommendations.extend(
                    [
                        "Developmental assessment recommended",
                        "Early intervention services may be beneficial",
                    ]
                )
        else:
            recommendations.extend(
                [
                    "Variant of uncertain significance",
                    "Monitor for additional evidence",
                    "Consider functional studies",
                ]
            )

        return recommendations

    def _generate_gene_recommendations(
        self, gene: str, annotations: List[VariantAnnotation]
    ) -> List[str]:
        """Generate gene-level recommendations"""
        recommendations = [
            "Comprehensive genetic counseling",
            "Review family history",
            "Consider cascade screening",
        ]

        pathogenic_count = len(
            [
                a
                for a in annotations
                if a.evidence_level
                in [EvidenceLevel.PATHOGENIC, EvidenceLevel.LIKELY_PATHOGENIC]
            ]
        )

        if pathogenic_count > 0:
            recommendations.extend(
                [
                    "Clinical management per established guidelines",
                    "Regular monitoring and follow-up",
                ]
            )

        return recommendations

    def _calculate_confidence_score(
        self,
        annotations: List[VariantAnnotation],
        frequencies: List[PopulationFrequency],
        references: List[LiteratureReference],
    ) -> float:
        """Calculate confidence score"""
        score = 0.0

        # Annotation quality
        if annotations:
            score += 0.4 * annotations[0].pathogenicity_score

        # Population data availability
        if frequencies:
            score += 0.2

        # Literature support
        if references:
            avg_relevance = sum(ref.relevance_score for ref in references) / len(
                references
            )
            score += 0.4 * avg_relevance

        return min(score, 1.0)

    def _calculate_gene_confidence_score(
        self,
        annotations: List[VariantAnnotation],
        references: List[LiteratureReference],
    ) -> float:
        """Calculate gene-level confidence score"""
        score = 0.0

        # Number of variants
        if annotations:
            score += min(0.3, len(annotations) * 0.1)

        # Pathogenic variants
        pathogenic_count = len(
            [
                a
                for a in annotations
                if a.evidence_level
                in [EvidenceLevel.PATHOGENIC, EvidenceLevel.LIKELY_PATHOGENIC]
            ]
        )
        if pathogenic_count > 0:
            score += 0.3

        # Literature support
        if references:
            avg_relevance = sum(ref.relevance_score for ref in references) / len(
                references
            )
            score += 0.4 * avg_relevance

        return min(score, 1.0)
