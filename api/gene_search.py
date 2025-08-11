"""Gene Search Engine for DNA Research Platform"""

import re
from typing import Dict, List, Optional
from dataclasses import dataclass


@dataclass
class Gene:
    """Gene data structure"""

    symbol: str
    name: str
    chromosome: str
    start: int
    end: int
    aliases: List[str]
    description: str
    pathways: List[str]


class GeneSearchEngine:
    """Fast gene search with fuzzy matching"""

    def __init__(self):
        self.genes = self._load_gene_database()
        self.symbol_index = {gene.symbol.upper(): gene for gene in self.genes}
        self.alias_index = {}
        for gene in self.genes:
            for alias in gene.aliases:
                self.alias_index[alias.upper()] = gene

    def _load_gene_database(self) -> List[Gene]:
        """Load gene reference data"""
        # Mock gene database - in production this would load from a real database
        return [
            Gene(
                symbol="SHANK3",
                name="SH3 and multiple ankyrin repeat domains 3",
                chromosome="22",
                start=51150000,
                end=51180000,
                aliases=["PROSAP2", "PSAP2"],
                description="Critical for synaptic function and autism spectrum disorders",
                pathways=["synaptic_transmission", "autism_pathway"],
            ),
            Gene(
                symbol="NRXN1",
                name="Neurexin 1",
                chromosome="2",
                start=50150000,
                end=51400000,
                aliases=["KIAA0578"],
                description="Synaptic adhesion molecule linked to autism and schizophrenia",
                pathways=["synaptic_adhesion", "autism_pathway"],
            ),
            Gene(
                symbol="SYNGAP1",
                name="Synaptic Ras GTPase activating protein 1",
                chromosome="6",
                start=33400000,
                end=33500000,
                aliases=["KIAA1938", "RASA5"],
                description="Regulates synaptic plasticity, mutations cause intellectual disability",
                pathways=["synaptic_plasticity", "autism_pathway"],
            ),
            Gene(
                symbol="BRCA1",
                name="BRCA1 DNA repair associated",
                chromosome="17",
                start=43044295,
                end=43125483,
                aliases=[
                    "BRCAI",
                    "BRCC1",
                    "FANCS",
                    "IRIS",
                    "PNCA4",
                    "PPP1R53",
                    "PSCP",
                    "RNF53",
                ],
                description="Tumor suppressor gene involved in DNA repair and breast cancer",
                pathways=["dna_repair", "cancer_pathway"],
            ),
            Gene(
                symbol="BRCA2",
                name="BRCA2 DNA repair associated",
                chromosome="13",
                start=32315086,
                end=32400266,
                aliases=[
                    "BRCC2",
                    "BROVCA2",
                    "FACD",
                    "FAD",
                    "FAD1",
                    "FANCD",
                    "FANCD1",
                    "GLM3",
                    "PNCA2",
                    "XRCC11",
                ],
                description="Tumor suppressor gene involved in DNA repair and breast cancer",
                pathways=["dna_repair", "cancer_pathway"],
            ),
            Gene(
                symbol="APOE",
                name="Apolipoprotein E",
                chromosome="19",
                start=45409011,
                end=45412650,
                aliases=["AD2", "APO-E", "ApoE4", "LDLCQ5", "LPG"],
                description="Lipid transport protein, major genetic risk factor for Alzheimer's disease",
                pathways=["lipid_metabolism", "alzheimer_pathway"],
            ),
            Gene(
                symbol="CFTR",
                name="Cystic fibrosis transmembrane conductance regulator",
                chromosome="7",
                start=117465784,
                end=117715971,
                aliases=[
                    "ABC35",
                    "ABCC7",
                    "CF",
                    "CFTR/MRP",
                    "dJ760C5.1",
                    "MRP7",
                    "TNR-CFTR",
                ],
                description="Chloride channel defective in cystic fibrosis",
                pathways=["ion_transport", "cystic_fibrosis_pathway"],
            ),
        ]

    def search(self, query: str, limit: int = 10) -> List[Dict]:
        """Search genes by symbol, alias, or coordinates"""
        query = query.strip()
        if not query:
            return []

        results = []

        # Exact symbol match (highest priority)
        if query.upper() in self.symbol_index:
            gene = self.symbol_index[query.upper()]
            results.append(self._gene_to_dict(gene, match_type="exact_symbol"))

        # Exact alias match
        if query.upper() in self.alias_index and len(results) == 0:
            gene = self.alias_index[query.upper()]
            results.append(self._gene_to_dict(gene, match_type="exact_alias"))

        # Coordinate search (chr:start-end format)
        coord_match = re.match(r"^(\d+|X|Y|MT):(\d+)-(\d+)$", query.upper())
        if coord_match:
            chr_name, start, end = coord_match.groups()
            start, end = int(start), int(end)
            for gene in self.genes:
                if gene.chromosome == chr_name and not (
                    gene.end < start or gene.start > end
                ):
                    results.append(self._gene_to_dict(gene, match_type="coordinate"))

        # Fuzzy matching for partial matches
        if len(results) == 0:
            query_upper = query.upper()
            for gene in self.genes:
                score = 0
                match_type = None

                # Symbol partial match
                if query_upper in gene.symbol.upper():
                    score = len(query) / len(gene.symbol)
                    match_type = "partial_symbol"

                # Alias partial match
                for alias in gene.aliases:
                    if query_upper in alias.upper():
                        alias_score = len(query) / len(alias)
                        if alias_score > score:
                            score = alias_score
                            match_type = "partial_alias"

                # Description match (word-based)
                desc_words = gene.description.upper().split()
                for word in desc_words:
                    if query_upper == word:
                        # Exact word match
                        desc_score = 0.8
                        if desc_score > score:
                            score = desc_score
                            match_type = "description"
                    elif len(query_upper) >= 4 and query_upper in word:
                        # Partial word match (only for longer queries)
                        desc_score = 0.6
                        if desc_score > score:
                            score = desc_score
                            match_type = "description"

                if score > 0.2:  # Minimum similarity threshold
                    gene_dict = self._gene_to_dict(gene, match_type)
                    gene_dict["match_score"] = score
                    results.append(gene_dict)

        # Sort by relevance and limit results
        if len(results) > 1:
            results.sort(key=lambda x: x.get("match_score", 1.0), reverse=True)

        return results[:limit]

    def get_gene_by_symbol(self, symbol: str) -> Optional[Dict]:
        """Get gene details by exact symbol"""
        gene = self.symbol_index.get(symbol.upper())
        if gene:
            return self._gene_to_dict(gene, match_type="exact_symbol")
        return None

    def _gene_to_dict(self, gene: Gene, match_type: str) -> Dict:
        """Convert Gene object to dictionary"""
        return {
            "symbol": gene.symbol,
            "name": gene.name,
            "chromosome": gene.chromosome,
            "start": gene.start,
            "end": gene.end,
            "location": f"{gene.chromosome}:{gene.start}-{gene.end}",
            "aliases": gene.aliases,
            "description": gene.description,
            "pathways": gene.pathways,
            "match_type": match_type,
        }
