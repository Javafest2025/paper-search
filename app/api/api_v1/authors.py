"""
Author search API endpoints.
Provides comprehensive author information from multiple academic sources.
"""

import asyncio
import logging
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel
import httpx

from app.services.academic_apis.clients import (
    SemanticScholarClient, OpenAlexClient, DBLPClient, 
    EuropePMCClient, PubMedClient
)

logger = logging.getLogger(__name__)
router = APIRouter()

class AuthorSearchRequest(BaseModel):
    name: str
    institution: Optional[str] = None
    field_of_study: Optional[str] = None
    email: Optional[str] = None

class AuthorResponse(BaseModel):
    author_id: Optional[str] = None
    name: str
    orcid: Optional[str] = None
    affiliations: List[Dict[str, Any]] = []
    homepage_url: Optional[str] = None
    email: Optional[str] = None
    h_index: Optional[int] = None
    paper_count: Optional[int] = None
    citation_count: Optional[int] = None
    fields_of_study: List[str] = []
    profile_image_url: Optional[str] = None
    last_updated: str
    sources: List[str] = []
    confidence_score: float = 0.0

class AuthorSearchService:
    """Service to search for author information across multiple sources."""
    
    def __init__(self):
        self.clients = {
            "semantic_scholar": SemanticScholarClient(),
            "openalex": OpenAlexClient(),
            "dblp": DBLPClient(),
            "europepmc": EuropePMCClient(),
            "pubmed": PubMedClient()
        }
    
    async def search_author(self, name: str, **kwargs) -> AuthorResponse:
        """
        Search for author information across multiple sources.
        """
        profile_tasks = [
            self._fetch_semantic_scholar_author_profile(name, **kwargs),
            self._fetch_openalex_author_profile(name, **kwargs),
            self._fetch_dblp_author_profile(name, **kwargs),
        ]
        # Paper-based fallbacks to enrich fields of study and counts
        fallback_tasks = [
            self._search_semantic_scholar(name, **kwargs),
            self._search_openalex(name, **kwargs),
            self._search_dblp(name, **kwargs),
            self._search_europepmc(name, **kwargs),
            self._search_pubmed(name, **kwargs),
        ]

        results_profiles, results_fallbacks = await asyncio.gather(
            asyncio.gather(*profile_tasks, return_exceptions=True),
            asyncio.gather(*fallback_tasks, return_exceptions=True),
        )

        # Merge results from all sources
        merged_profile = self._merge_author_data(name, results_profiles + results_fallbacks)

        # If we have S2 author_id, fetch detailed profile to fill h-index and counts
        s2_id = merged_profile.get("author_id") if merged_profile.get("author_id", "").isdigit() else None
        if s2_id:
            s2_details = await self._fetch_semantic_scholar_author_details(s2_id)
            if s2_details:
                merged_profile = self._merge_author_data(name, [merged_profile, s2_details])

        # If author_id looks like OpenAlex URL/id, fetch OpenAlex details
        openalex_id = None
        aid = merged_profile.get("author_id") or ""
        if isinstance(aid, str) and ("openalex.org" in aid or (aid.startswith("A") and aid[1:].isdigit())):
            openalex_id = aid.split("/")[-1] if "/" in aid else aid
        if openalex_id:
            oa_details = await self._fetch_openalex_author_details(openalex_id)
            if oa_details:
                merged_profile = self._merge_author_data(name, [merged_profile, oa_details])

        # If ORCID present and is a URL or id, enrich affiliations via ORCID public API
        orcid = merged_profile.get("orcid")
        if orcid:
            orcid_id = orcid.split("/")[-1]
            orcid_details = await self._fetch_orcid_author_record(orcid_id)
            if orcid_details:
                merged_profile = self._merge_author_data(name, [merged_profile, orcid_details])

        # Normalize identifiers and urls
        merged_profile = self._normalize_identifiers(merged_profile)
        return AuthorResponse(**merged_profile)

    # ---------- Dedicated author endpoints ----------
    async def _fetch_semantic_scholar_author_profile(self, name: str, **kwargs) -> Dict[str, Any]:
        """Query Semantic Scholar author search endpoint for richer profile data."""
        url = "https://api.semanticscholar.org/graph/v1/author/search"
        params = {
            "query": name,
            "limit": 5,
            "fields": "authorId,name,aliases,citationCount,hIndex,paperCount,homepage,externalIds,affiliations"
        }
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                resp = await client.get(url, params=params, headers={"User-Agent": "ScholarAI/1.0"})
                resp.raise_for_status()
                data = resp.json() or {}
                authors = data.get("data", [])
                if not authors:
                    return {}
                best = self._pick_best_name_match(name, authors, s2=True)
                if not best:
                    return {}
                affiliations: List[Dict[str, Any]] = []
                # S2 returns affiliations as strings in some contexts; normalize
                if best.get("affiliations") and isinstance(best["affiliations"], list):
                    for aff in best["affiliations"]:
                        if isinstance(aff, str):
                            affiliations.append({"institution_name": aff})
                        elif isinstance(aff, dict):
                            affiliations.append({
                                "institution_name": aff.get("name") or aff.get("displayName"),
                                "institution_id": aff.get("id"),
                            })
                author_info = {
                    "name": best.get("name") or name,
                    "author_id": str(best.get("authorId")) if best.get("authorId") else None,
                    "paper_count": best.get("paperCount"),
                    "citation_count": best.get("citationCount"),
                    "h_index": best.get("hIndex"),
                    "homepage_url": best.get("homepage"),
                    "orcid": (best.get("externalIds") or {}).get("ORCID"),
                    "affiliations": affiliations,
                    "sources": ["semantic_scholar"],
                }
                return {k: v for k, v in author_info.items() if v is not None and v != []}
        except Exception as e:
            logger.warning(f"S2 author profile fetch failed: {e}")
            return {}

    async def _fetch_openalex_author_profile(self, name: str, **kwargs) -> Dict[str, Any]:
        """Query OpenAlex author search for profile details (works_count, cited_by_count, orcid, affiliations)."""
        url = "https://api.openalex.org/authors"
        params = {"search": name, "per_page": 5}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                resp = await client.get(url, params=params, headers={"User-Agent": "ScholarAI/1.0"})
                resp.raise_for_status()
                data = resp.json() or {}
                authors = data.get("results", [])
                if not authors:
                    return {}
                best = self._pick_best_name_match(name, authors, openalex=True)
                if not best:
                    return {}
                affiliations: List[Dict[str, Any]] = []
                if best.get("last_known_institution"):
                    inst = best["last_known_institution"]
                    affiliations.append({
                        "institution_id": inst.get("id"),
                        "institution_name": inst.get("display_name"),
                        "country": inst.get("country_code"),
                    })
                author_info = {
                    "name": best.get("display_name") or name,
                    "author_id": best.get("id"),
                    "paper_count": best.get("works_count"),
                    "citation_count": best.get("cited_by_count"),
                    "orcid": (best.get("orcid")) or ((best.get("ids") or {}).get("orcid")),
                    "homepage_url": (best.get("homepage_url")),
                    "affiliations": affiliations,
                    "sources": ["openalex"],
                }
                # OpenAlex image URL (if any)
                if best.get("image_url"):
                    author_info["profile_image_url"] = best["image_url"]
                return {k: v for k, v in author_info.items() if v is not None and v != []}
        except Exception as e:
            logger.warning(f"OpenAlex author profile fetch failed: {e}")
            return {}

    async def _fetch_dblp_author_profile(self, name: str, **kwargs) -> Dict[str, Any]:
        """Query DBLP author search to retrieve pid and homepage URL."""
        url = "https://dblp.org/search/author/api"
        params = {"q": name, "format": "json"}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                resp = await client.get(url, params=params, headers={"User-Agent": "ScholarAI/1.0"})
                resp.raise_for_status()
                data = resp.json() or {}
                hits = (((data.get("result") or {}).get("hits")) or {})
                authors = hits.get("hit", [])
                if not authors:
                    return {}
                # normalize list of dicts
                candidates = []
                for a in authors:
                    info = a.get("info", {})
                    candidates.append(info)
                best = self._pick_best_name_match(name, candidates, dblp=True)
                if not best:
                    return {}
                author_info = {
                    "name": best.get("author") or best.get("name") or name,
                    "author_id": best.get("@pid") or best.get("pid"),
                    "homepage_url": best.get("url"),
                    "sources": ["dblp"],
                }
                return {k: v for k, v in author_info.items() if v is not None}
        except Exception as e:
            logger.warning(f"DBLP author profile fetch failed: {e}")
            return {}

    # ---------- Paper-based enrichment (existing) ----------
    async def _search_semantic_scholar(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            papers = await self.clients["semantic_scholar"].search_papers(
                query=f'author:"{name}"', 
                limit=50
            )
            if not papers:
                return {}
            fields: set = set()
            for p in papers:
                if "fieldsOfStudy" in p:
                    fields.update(p["fieldsOfStudy"]) 
            return {
                "name": name,
                "paper_count": len(papers),
                "fields_of_study": list(fields),
                "sources": ["semantic_scholar"],
            }
        except Exception as e:
            logger.error(f"Error searching Semantic Scholar: {e}")
            return {}
    
    async def _search_openalex(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            papers = await self.clients["openalex"].search_papers(
                query=f'author:"{name}"', 
                limit=50
            )
            if not papers:
                return {}
            citations = [p.get("citationCount", 0) for p in papers]
            return {
                "name": name,
                "paper_count": len(papers),
                "citation_count": max(citations) if citations else None,
                "sources": ["openalex"],
            }
        except Exception as e:
            logger.error(f"Error searching OpenAlex: {e}")
            return {}
    
    async def _search_dblp(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            papers = await self.clients["dblp"].search_papers(
                query=f'author:"{name}"', 
                limit=50
            )
            if not papers:
                return {}
            return {
                "name": name,
                "paper_count": len(papers),
                "sources": ["dblp"],
            }
        except Exception as e:
            logger.error(f"Error searching DBLP: {e}")
            return {}
    
    async def _search_europepmc(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            papers = await self.clients["europepmc"].search_papers(
                query=f'author:"{name}"', 
                limit=50
            )
            if not papers:
                return {}
            return {
                "name": name,
                "paper_count": len(papers),
                "sources": ["europepmc"],
            }
        except Exception as e:
            logger.error(f"Error searching Europe PMC: {e}")
            return {}
    
    async def _search_pubmed(self, name: str, **kwargs) -> Dict[str, Any]:
        try:
            papers = await self.clients["pubmed"].search_papers(
                query=f'author:"{name}"', 
                limit=50
            )
            if not papers:
                return {}
            return {
                "name": name,
                "paper_count": len(papers),
                "sources": ["pubmed"],
            }
        except Exception as e:
            logger.error(f"Error searching PubMed: {e}")
            return {}

    # ---------- Helpers ----------
    def _pick_best_name_match(self, target_name: str, candidates: List[Dict[str, Any]], *, s2: bool=False, openalex: bool=False, dblp: bool=False) -> Optional[Dict[str, Any]]:
        """Pick the best matching author by normalized name."""
        def norm(n: Optional[str]) -> str:
            return (n or "").lower().replace(".", "").strip()
        t = norm(target_name)
        best = None
        for c in candidates:
            cand_name = None
            if s2:
                cand_name = c.get("name")
                aliases = c.get("aliases") or []
                names = [cand_name] + aliases
            elif openalex:
                cand_name = c.get("display_name")
                names = [cand_name] + (c.get("display_name_alternatives") or [])
            elif dblp:
                cand_name = c.get("author") or c.get("name")
                names = [cand_name]
            else:
                names = [c.get("name")]
            names = [n for n in names if n]
            if not names:
                continue
            if any(norm(n) == t for n in names):
                best = c
                break
            # fallback: startswith or contains
            if not best and any(t in norm(n) or norm(n) in t for n in names):
                best = c
        return best or (candidates[0] if candidates else None)

    def _merge_author_data(self, name: str, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge author data from multiple sources."""
        merged = {
            "name": name,
            "author_id": None,
            "orcid": None,
            "affiliations": [],
            "homepage_url": None,
            "email": None,
            "h_index": None,
            "paper_count": 0,
            "citation_count": 0,
            "fields_of_study": set(),
            "profile_image_url": None,
            "last_updated": datetime.now().isoformat(),
            "sources": [],
            "confidence_score": 0.0
        }

        valid_results = [r for r in results if isinstance(r, dict) and r]

        # Prefer max for counts, and keep first non-null for identifiers/urls
        paper_counts: List[int] = []
        citation_counts: List[int] = []
        h_indices: List[int] = []

        for result in valid_results:
            # Merge sources
            if "sources" in result:
                merged["sources"].extend(result["sources"])

            # Counts
            if isinstance(result.get("paper_count"), int):
                paper_counts.append(result["paper_count"])
            if isinstance(result.get("citation_count"), int):
                citation_counts.append(result["citation_count"])
            if isinstance(result.get("h_index"), int):
                h_indices.append(result["h_index"])

            # IDs
            if not merged["author_id"] and result.get("author_id"):
                merged["author_id"] = result["author_id"]
            if not merged["orcid"] and result.get("orcid"):
                merged["orcid"] = result["orcid"]
            if not merged["homepage_url"] and result.get("homepage_url"):
                merged["homepage_url"] = result["homepage_url"]
            if not merged["profile_image_url"] and result.get("profile_image_url"):
                merged["profile_image_url"] = result["profile_image_url"]

            # Affiliations
            if result.get("affiliations"):
                merged["affiliations"].extend(result["affiliations"])

            # Fields of study
            if result.get("fields_of_study"):
                fos = result["fields_of_study"]
                if isinstance(fos, list):
                    merged["fields_of_study"].update(fos)

        # Finalize numeric fields using max (avoid double counting across sources)
        merged["paper_count"] = max(paper_counts) if paper_counts else 0
        merged["citation_count"] = max(citation_counts) if citation_counts else 0
        merged["h_index"] = max(h_indices) if h_indices else None

        # Deduplicate affiliations and sources
        if merged["affiliations"]:
            seen = set()
            dedup_affs: List[Dict[str, Any]] = []
            for aff in merged["affiliations"]:
                key = (
                    (aff.get("institution_id") or ""),
                    (aff.get("institution_name") or ""),
                    (aff.get("country") or ""),
                )
                if key in seen:
                    continue
                seen.add(key)
                dedup_affs.append(aff)
            merged["affiliations"] = dedup_affs

        merged["fields_of_study"] = list(merged["fields_of_study"]) if merged["fields_of_study"] else []
        merged["sources"] = list({s for s in merged["sources"]})

        # Confidence score: number of authoritative profiles + presence of key fields
        score = 0.0
        profile_sources = {s for s in merged["sources"] if s in {"openalex", "semantic_scholar", "dblp"}}
        score += 0.3 * min(len(profile_sources), 2)  # up to 0.6 from profiles
        if merged["paper_count"]:
            score += 0.2
        if merged["citation_count"]:
            score += 0.2
        if merged["orcid"]:
            score += 0.1
        if merged["h_index"]:
            score += 0.1
        merged["confidence_score"] = round(min(score, 1.0), 2)

        return merged

    async def _fetch_semantic_scholar_author_details(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed Semantic Scholar author profile by ID."""
        url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
        params = {"fields": "authorId,name,homepage,externalIds,hIndex,paperCount,citationCount,affiliations"}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                resp = await client.get(url, params=params, headers={"User-Agent": "ScholarAI/1.0"})
                resp.raise_for_status()
                a = resp.json() or {}
                affiliations: List[Dict[str, Any]] = []
                if a.get("affiliations") and isinstance(a["affiliations"], list):
                    for aff in a["affiliations"]:
                        if isinstance(aff, str):
                            affiliations.append({"institution_name": aff})
                        elif isinstance(aff, dict):
                            affiliations.append({"institution_name": aff.get("name") or aff.get("displayName")})
                return {
                    "name": a.get("name"),
                    "author_id": str(a.get("authorId")) if a.get("authorId") else None,
                    "paper_count": a.get("paperCount"),
                    "citation_count": a.get("citationCount"),
                    "h_index": a.get("hIndex"),
                    "homepage_url": a.get("homepage"),
                    "orcid": (a.get("externalIds") or {}).get("ORCID"),
                    "affiliations": affiliations,
                    "sources": ["semantic_scholar"],
                }
        except Exception as e:
            logger.warning(f"S2 author detail fetch failed: {e}")
            return None

    async def _fetch_openalex_author_details(self, author_id: str) -> Optional[Dict[str, Any]]:
        """Fetch detailed OpenAlex author profile by ID."""
        url = f"https://api.openalex.org/authors/{author_id}"
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                resp = await client.get(url, headers={"User-Agent": "ScholarAI/1.0"})
                resp.raise_for_status()
                a = resp.json() or {}
                affiliations: List[Dict[str, Any]] = []
                if a.get("last_known_institution"):
                    inst = a["last_known_institution"]
                    affiliations.append({
                        "institution_id": inst.get("id"),
                        "institution_name": inst.get("display_name"),
                        "country": inst.get("country_code"),
                    })
                # Concepts as fields of study
                fields = []
                for c in a.get("x_concepts", []) or []:
                    n = c.get("display_name")
                    if n:
                        fields.append(n)
                return {
                    "name": a.get("display_name"),
                    "author_id": a.get("id"),
                    "paper_count": a.get("works_count"),
                    "citation_count": a.get("cited_by_count"),
                    "orcid": (a.get("orcid")) or ((a.get("ids") or {}).get("orcid")),
                    "homepage_url": a.get("homepage_url"),
                    "profile_image_url": a.get("image_url"),
                    "affiliations": affiliations,
                    "fields_of_study": fields,
                    "sources": ["openalex"],
                }
        except Exception as e:
            logger.warning(f"OpenAlex author detail fetch failed: {e}")
            return None

    async def _fetch_orcid_author_record(self, orcid_id: str) -> Optional[Dict[str, Any]]:
        """Fetch ORCID public record to enrich affiliations."""
        url = f"https://pub.orcid.org/v3.0/{orcid_id}/record"
        headers = {"Accept": "application/json", "User-Agent": "ScholarAI/1.0"}
        try:
            async with httpx.AsyncClient(follow_redirects=True, timeout=20) as client:
                resp = await client.get(url, headers=headers)
                if resp.status_code >= 400:
                    return None
                data = resp.json() or {}
                affiliations: List[Dict[str, Any]] = []
                # Extract employment summaries
                empl = (((data.get("activities-summary") or {}).get("employments")) or {}).get("affiliation-group", [])
                for g in empl:
                    summ = (g.get("summaries") or [])
                    for s in summ:
                        emp = ((s.get("employment-summary")) or {})
                        org = (emp.get("organization") or {})
                        addr = org.get("address") or {}
                        start = ((emp.get("start-date") or {}).get("year") or {}).get("value")
                        end = ((emp.get("end-date") or {}).get("year") or {}).get("value")
                        affiliations.append({
                            "institution_name": org.get("name"),
                            "country": addr.get("country"),
                            "start_date": f"{start}-01-01" if start else None,
                            "end_date": f"{end}-01-01" if end else None,
                        })
                return {
                    "orcid": orcid_id,
                    "affiliations": [a for a in affiliations if a.get("institution_name")],
                    "sources": ["orcid"],
                }
        except Exception as e:
            logger.warning(f"ORCID record fetch failed: {e}")
            return None

    def _normalize_identifiers(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize IDs and URLs to clean identifiers where possible."""
        out = dict(data)
        aid = out.get("author_id")
        if isinstance(aid, str):
            if "openalex.org/" in aid:
                out["author_id"] = aid.split("/")[-1]
        orcid = out.get("orcid")
        if isinstance(orcid, str) and "/" in orcid:
            # store canonical id
            out["orcid"] = orcid.split("/")[-1]
        return out

# Initialize the service
author_service = AuthorSearchService()

@router.post("/search", response_model=AuthorResponse)
async def search_author(request: AuthorSearchRequest):
    """Search for comprehensive author information across multiple academic sources."""
    try:
        author_data = await author_service.search_author(
            name=request.name,
            institution=request.institution,
            field_of_study=request.field_of_study,
            email=request.email
        )
        if author_data.paper_count == 0 and not author_data.citation_count and not author_data.orcid:
            raise HTTPException(status_code=404, detail=f"No author information found for '{request.name}'")
        return author_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in author search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")

@router.get("/search/{name}", response_model=AuthorResponse)
async def search_author_by_name(
    name: str,
    institution: Optional[str] = Query(None, description="Institution name"),
    field_of_study: Optional[str] = Query(None, description="Field of study"),
    email: Optional[str] = Query(None, description="Email address")
):
    """Search for author information by name using GET request."""
    try:
        author_data = await author_service.search_author(
            name=name,
            institution=institution,
            field_of_study=field_of_study,
            email=email
        )
        if author_data.paper_count == 0 and not author_data.citation_count and not author_data.orcid:
            raise HTTPException(status_code=404, detail=f"No author information found for '{name}'")
        return author_data
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in author search: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")
