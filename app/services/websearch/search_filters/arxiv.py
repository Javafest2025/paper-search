"""
arXiv search filter implementation
"""

from typing import Dict, Any

from .base import BaseSearchFilter, DateFilterMixin


class ArxivFilter(BaseSearchFilter, DateFilterMixin):
    """
    Search filter implementation for arXiv API.

    arXiv supports:
    - Subject category filtering
    - Year range filtering
    - Author filtering
    - Journal reference filtering
    """

    @property
    def source_name(self) -> str:
        return "arXiv"

    def _add_date_filter(self, filters: Dict[str, Any]):
        """arXiv uses year range format: 'YYYY-YYYY'"""
        self._add_year_range_filter(filters)

    def _add_domain_filter(self, filters: Dict[str, Any], domain: str):
        """Add subject category filtering for arXiv"""
        if not domain:
            return  # No domain-specific filtering needed

        domain_lower = domain.lower()

        # arXiv subject category mapping
        category_mapping = {
            # Computer Science
            "computer science": "cs.*",
            "machine learning": "cs.LG",
            "artificial intelligence": "cs.AI",
            "computer vision": "cs.CV",
            "natural language processing": "cs.CL",
            "computational complexity": "cs.CC",
            "cryptography": "cs.CR",
            "databases": "cs.DB",
            "distributed computing": "cs.DC",
            "data structures": "cs.DS",
            "computer graphics": "cs.GR",
            "human computer interaction": "cs.HC",
            "information retrieval": "cs.IR",
            "networking": "cs.NI",
            "programming languages": "cs.PL",
            "robotics": "cs.RO",
            "software engineering": "cs.SE",
            "systems": "cs.SY",
            # Mathematics
            "mathematics": "math.*",
            "algebra": "math.AG",
            "analysis": "math.AN",
            "combinatorics": "math.CO",
            "differential geometry": "math.DG",
            "dynamical systems": "math.DS",
            "functional analysis": "math.FA",
            "general topology": "math.GN",
            "geometry": "math.MG",
            "number theory": "math.NT",
            "optimization": "math.OC",
            "probability": "math.PR",
            "representation theory": "math.RT",
            "statistics": "math.ST",
            # Physics
            "physics": "physics.*",
            "astrophysics": "astro-ph.*",
            "condensed matter": "cond-mat.*",
            "general relativity": "gr-qc",
            "high energy physics": "hep-*",
            "mathematical physics": "math-ph",
            "nuclear theory": "nucl-th",
            "quantum physics": "quant-ph",
            # Statistics
            "statistics": "stat.*",
            "machine learning stats": "stat.ML",
            "methodology": "stat.ME",
            "theory": "stat.TH",
            "applications": "stat.AP",
            # Quantitative Biology
            "quantitative biology": "q-bio.*",
            "biomolecules": "q-bio.BM",
            "cell behavior": "q-bio.CB",
            "genomics": "q-bio.GN",
            "molecular networks": "q-bio.MN",
            "neurons": "q-bio.NC",
            "populations": "q-bio.PE",
            "quantitative methods": "q-bio.QM",
            "subcellular processes": "q-bio.SC",
            "tissues": "q-bio.TO",
            # Economics
            "economics": "econ.*",
            "econometrics": "econ.EM",
            "general economics": "econ.GN",
            "theoretical economics": "econ.TH",
            # Electrical Engineering
            "electrical engineering": "eess.*",
            "audio processing": "eess.AS",
            "image processing": "eess.IV",
            "signal processing": "eess.SP",
            "systems control": "eess.SY",
        }

        # Find the best matching category
        for key, value in category_mapping.items():
            if key in domain_lower:
                filters["category"] = value
                break

        # If no specific match, use broader categories
        if "category" not in filters:
            if any(
                term in domain_lower
                for term in ["computer", "computing", "software", "algorithm"]
            ):
                filters["category"] = "cs.*"
            elif any(term in domain_lower for term in ["math", "mathematical"]):
                filters["category"] = "math.*"
            elif any(term in domain_lower for term in ["physics", "physical"]):
                filters["category"] = "physics.*"
            elif any(term in domain_lower for term in ["biology", "biological"]):
                filters["category"] = "q-bio.*"

    def _add_source_optimizations(self, filters: Dict[str, Any]):
        """Add arXiv specific optimizations"""
        # arXiv is already a preprint server, so no additional optimizations needed
        # Could add author filtering or journal reference filtering if needed
        pass

    def get_filter_info(self) -> Dict[str, Any]:
        """Get arXiv filter capabilities"""
        base_info = super().get_filter_info()
        base_info.update(
            {
                "date_format": "year_range",
                "available_optimizations": ["category_filter"],
                "supported_fields": [
                    "Computer Science",
                    "Mathematics",
                    "Physics",
                    "Statistics",
                    "Quantitative Biology",
                    "Economics",
                    "Electrical Engineering",
                ],
                "supported_categories": [
                    "cs.*",
                    "math.*",
                    "physics.*",
                    "astro-ph.*",
                    "cond-mat.*",
                    "gr-qc",
                    "hep-*",
                    "math-ph",
                    "nucl-th",
                    "quant-ph",
                    "stat.*",
                    "q-bio.*",
                    "econ.*",
                    "eess.*",
                ],
                "category_examples": {
                    "Computer Science": "cs.*",
                    "Machine Learning": "cs.LG",
                    "Mathematics": "math.*",
                    "Physics": "physics.*",
                    "Statistics": "stat.*",
                    "Biology": "q-bio.*",
                },
            }
        )
        return base_info
