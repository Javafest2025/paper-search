"""
Multi-source Author Service that combines multiple academic APIs for comprehensive author information
"""

import logging
import asyncio
from typing import Dict, List, Optional, Any, Union
from dataclasses import dataclass
from pydantic import BaseModel, Field

# Import existing services
import httpx
from urllib.parse import quote

logger = logging.getLogger(__name__)


@dataclass
class AuthorMetrics:
    """Combined author metrics from multiple sources"""
    total_citations: int = 0
    h_index: int = 0
    i10_index: int = 0
    paper_count: int = 0
    first_publication_year: Optional[int] = None
    last_publication_year: Optional[int] = None
    affiliation: Optional[str] = None
    research_areas: List[str] = None
    
    def __post_init__(self):
        if self.research_areas is None:
            self.research_areas = []


class EnhancedAuthorResponse(BaseModel):
    """Enhanced author response combining multiple data sources"""
    name: str = Field(..., description="Author name")
    primary_affiliation: Optional[str] = Field(None, description="Primary affiliation")
    all_affiliations: List[str] = Field(default_factory=list, description="All known affiliations")
    
    # Identifiers
    semantic_scholar_id: Optional[str] = Field(None, description="Semantic Scholar author ID")
    orcid_id: Optional[str] = Field(None, description="ORCID ID")
    google_scholar_id: Optional[str] = Field(None, description="Google Scholar ID")
    openalex_id: Optional[str] = Field(None, description="OpenAlex ID")
    
    # Metrics (best available from any source)
    citation_count: int = Field(default=0, description="Total citation count")
    h_index: int = Field(default=0, description="H-index")
    i10_index: int = Field(default=0, description="i10-index")
    paper_count: int = Field(default=0, description="Total paper count")
    
    # Publication timeline
    first_publication_year: Optional[int] = Field(None, description="Year of first publication")
    last_publication_year: Optional[int] = Field(None, description="Year of last publication")
    
    # Research areas
    research_areas: List[str] = Field(default_factory=list, description="Research areas/interests")
    
    # Recent publications
    recent_publications: List[Dict[str, Any]] = Field(default_factory=list, description="Recent publications")
    
    # Data sources
    data_sources: List[str] = Field(default_factory=list, description="APIs used to gather this data")
    data_quality_score: float = Field(default=0.0, description="Quality score based on data completeness")


class MultiSourceAuthorSearchResponse(BaseModel):
    """Response for multi-source author search"""
    success: bool = Field(..., description="Whether the search was successful")
    author: Optional[EnhancedAuthorResponse] = Field(None, description="Author information")
    error: Optional[str] = Field(None, description="Error message if search failed")
    search_strategy: str = Field(..., description="Search strategy used")
    sources_attempted: List[str] = Field(default_factory=list, description="Data sources attempted")
    sources_successful: List[str] = Field(default_factory=list, description="Data sources that returned data")


class MultiSourceAuthorService:
    """
    Service that combines multiple academic APIs to provide comprehensive author information
    """
    
    def __init__(self):
        self.timeout = 30.0
    
    async def search_author(
        self, 
        author_name: str, 
        strategy: str = "comprehensive"
    ) -> MultiSourceAuthorSearchResponse:
        """
        Search for an author using multiple sources
        
        Args:
            author_name: Name of the author to search for
            strategy: Search strategy ("fast", "comprehensive", "semantic_scholar_only")
            
        Returns:
            MultiSourceAuthorSearchResponse with combined data
        """
        sources_attempted = []
        sources_successful = []
        combined_data = {}
        
        try:
            logger.info(f"Searching for author '{author_name}' using strategy '{strategy}'")
            
            if strategy == "semantic_scholar_only":
                # Only use Semantic Scholar
                return await self._search_semantic_scholar_only(author_name)
            
            elif strategy == "fast":
                # Quick search using Semantic Scholar + OpenAlex
                combined_data = await self._fast_search(author_name, sources_attempted, sources_successful)
            
            else:  # comprehensive
                # Search all available sources
                combined_data = await self._comprehensive_search(author_name, sources_attempted, sources_successful)
            
            if not combined_data:
                return MultiSourceAuthorSearchResponse(
                    success=False,
                    error=f"Author '{author_name}' not found in any data source",
                    search_strategy=strategy,
                    sources_attempted=sources_attempted,
                    sources_successful=sources_successful
                )
            
            # Create enhanced author response
            enhanced_author = self._create_enhanced_author(combined_data, sources_successful)
            
            return MultiSourceAuthorSearchResponse(
                success=True,
                author=enhanced_author,
                search_strategy=strategy,
                sources_attempted=sources_attempted,
                sources_successful=sources_successful
            )
            
        except Exception as e:
            logger.error(f"Error in multi-source author search for '{author_name}': {e}")
            return MultiSourceAuthorSearchResponse(
                success=False,
                error=f"Search failed: {str(e)}",
                search_strategy=strategy,
                sources_attempted=sources_attempted,
                sources_successful=sources_successful
            )
    
    async def _search_semantic_scholar_only(self, author_name: str) -> MultiSourceAuthorSearchResponse:
        """Search using only Semantic Scholar"""
        try:
            result = await self._search_semantic_scholar_api(author_name, limit=1)
            
            if result.get('data') and len(result['data']) > 0:
                author_data = result['data'][0]
                
                enhanced_author = EnhancedAuthorResponse(
                    name=author_data.get('name', author_name),
                    primary_affiliation=', '.join(author_data.get('affiliations', [])) if author_data.get('affiliations') else None,
                    semantic_scholar_id=author_data.get('authorId'),
                    citation_count=author_data.get('citationCount', 0),
                    h_index=author_data.get('hIndex', 0),
                    paper_count=author_data.get('paperCount', 0),
                    data_sources=["semantic_scholar"],
                    data_quality_score=0.7
                )
                
                return MultiSourceAuthorSearchResponse(
                    success=True,
                    author=enhanced_author,
                    search_strategy="semantic_scholar_only",
                    sources_attempted=["semantic_scholar"],
                    sources_successful=["semantic_scholar"]
                )
            else:
                return MultiSourceAuthorSearchResponse(
                    success=False,
                    error=f"Author '{author_name}' not found in Semantic Scholar",
                    search_strategy="semantic_scholar_only",
                    sources_attempted=["semantic_scholar"],
                    sources_successful=[]
                )
                
        except Exception as e:
            return MultiSourceAuthorSearchResponse(
                success=False,
                error=f"Semantic Scholar search failed: {str(e)}",
                search_strategy="semantic_scholar_only",
                sources_attempted=["semantic_scholar"],
                sources_successful=[]
            )
    
    async def _fast_search(self, author_name: str, sources_attempted: List[str], sources_successful: List[str]) -> Dict[str, Any]:
        """Fast search using Semantic Scholar + OpenAlex"""
        combined_data = {}
        
        # Search Semantic Scholar
        try:
            sources_attempted.append("semantic_scholar")
            ss_result = await self._search_semantic_scholar_api(author_name, limit=1)
            if ss_result.get('data') and len(ss_result['data']) > 0:
                combined_data['semantic_scholar'] = ss_result['data'][0]
                sources_successful.append("semantic_scholar")
                logger.info(f"Found author in Semantic Scholar: {ss_result['data'][0].get('name')}")
        except Exception as e:
            logger.warning(f"Semantic Scholar search failed: {e}")
        
        # Search OpenAlex
        try:
            sources_attempted.append("openalex")
            openalex_result = await self._search_openalex_api(author_name, limit=1)
            if openalex_result.get('results') and len(openalex_result['results']) > 0:
                combined_data['openalex'] = openalex_result['results'][0]
                sources_successful.append("openalex")
                logger.info(f"Found author in OpenAlex: {openalex_result['results'][0].get('display_name')}")
        except Exception as e:
            logger.warning(f"OpenAlex search failed: {e}")
        
        return combined_data
    
    async def _comprehensive_search(self, author_name: str, sources_attempted: List[str], sources_successful: List[str]) -> Dict[str, Any]:
        """Comprehensive search using all available sources"""
        # Start with fast search
        combined_data = await self._fast_search(author_name, sources_attempted, sources_successful)
        
        # Add ORCID search for additional author verification
        try:
            sources_attempted.append("orcid")
            orcid_result = await self._search_orcid_api(author_name, limit=1)
            if orcid_result.get('result') and len(orcid_result['result']) > 0:
                combined_data['orcid'] = orcid_result['result'][0]
                sources_successful.append("orcid")
                logger.info(f"Found author in ORCID")
        except Exception as e:
            logger.warning(f"ORCID search failed: {e}")
        
        # Add DBLP for computer science authors (publications and venues)
        try:
            sources_attempted.append("dblp")
            dblp_result = await self._search_dblp_api(author_name, limit=1)
            if dblp_result.get('result', {}).get('hits', {}).get('hit'):
                combined_data['dblp'] = dblp_result['result']['hits']['hit'][0]
                sources_successful.append("dblp")
                logger.info(f"Found author in DBLP")
        except Exception as e:
            logger.warning(f"DBLP search failed: {e}")
        
        # Add Crossref for publication timeline and research areas
        try:
            sources_attempted.append("crossref")
            crossref_result = await self._search_crossref_api(author_name, limit=10)
            if crossref_result.get('message', {}).get('items'):
                combined_data['crossref'] = crossref_result['message']['items']
                sources_successful.append("crossref")
                logger.info(f"Found publications in Crossref")
        except Exception as e:
            logger.warning(f"Crossref search failed: {e}")
        
        # Add additional Semantic Scholar details for research areas and recent publications
        if 'semantic_scholar' in combined_data and combined_data['semantic_scholar'].get('authorId'):
            try:
                sources_attempted.append("semantic_scholar_detailed")
                detailed_result = await self._get_semantic_scholar_author_details(
                    combined_data['semantic_scholar']['authorId']
                )
                if detailed_result:
                    combined_data['semantic_scholar_detailed'] = detailed_result
                    sources_successful.append("semantic_scholar_detailed")
                    logger.info(f"Found detailed info in Semantic Scholar")
            except Exception as e:
                logger.warning(f"Semantic Scholar detailed search failed: {e}")
        
        return combined_data
    
    def _create_enhanced_author(self, combined_data: Dict[str, Any], sources_successful: List[str]) -> EnhancedAuthorResponse:
        """Create enhanced author response from combined data"""
        
        # Initialize with default values
        enhanced_author = EnhancedAuthorResponse(
            name="Unknown",
            data_sources=sources_successful
        )
        
        # Extract data from Semantic Scholar
        if 'semantic_scholar' in combined_data:
            ss_data = combined_data['semantic_scholar']
            enhanced_author.name = ss_data.get('name', enhanced_author.name)
            enhanced_author.semantic_scholar_id = ss_data.get('authorId')
            enhanced_author.citation_count = max(enhanced_author.citation_count, ss_data.get('citationCount', 0))
            enhanced_author.h_index = max(enhanced_author.h_index, ss_data.get('hIndex', 0))
            enhanced_author.paper_count = max(enhanced_author.paper_count, ss_data.get('paperCount', 0))
            
            if ss_data.get('affiliations'):
                enhanced_author.all_affiliations.extend(ss_data['affiliations'])
                if not enhanced_author.primary_affiliation:
                    enhanced_author.primary_affiliation = ss_data['affiliations'][0]
            
            # Extract external IDs
            external_ids = ss_data.get('externalIds', {})
            if external_ids.get('ORCID'):
                enhanced_author.orcid_id = external_ids['ORCID']
        
        # Extract data from OpenAlex
        if 'openalex' in combined_data:
            oa_data = combined_data['openalex']
            enhanced_author.name = oa_data.get('display_name', enhanced_author.name)
            enhanced_author.openalex_id = oa_data.get('id')
            enhanced_author.citation_count = max(enhanced_author.citation_count, oa_data.get('cited_by_count', 0))
            enhanced_author.paper_count = max(enhanced_author.paper_count, oa_data.get('works_count', 0))
            
            # Extract affiliations from OpenAlex
            if oa_data.get('affiliations'):
                for affiliation in oa_data['affiliations']:
                    if affiliation.get('institution', {}).get('display_name'):
                        affiliation_name = affiliation['institution']['display_name']
                        if affiliation_name not in enhanced_author.all_affiliations:
                            enhanced_author.all_affiliations.append(affiliation_name)
                            if not enhanced_author.primary_affiliation:
                                enhanced_author.primary_affiliation = affiliation_name
            
            # Extract ORCID from OpenAlex
            if oa_data.get('orcid'):
                enhanced_author.orcid_id = oa_data['orcid'].replace('https://orcid.org/', '')
        
        # Extract data from ORCID
        if 'orcid' in combined_data:
            orcid_data = combined_data['orcid']
            if orcid_data.get('orcid-identifier', {}).get('path'):
                enhanced_author.orcid_id = orcid_data['orcid-identifier']['path']
        
        # Extract data from DBLP
        if 'dblp' in combined_data:
            dblp_data = combined_data['dblp']['info']
            if dblp_data.get('author'):
                # DBLP has clean author names and venues
                enhanced_author.name = dblp_data['author']
            
            # Extract publication venues and research areas from DBLP
            if dblp_data.get('notes', {}).get('note'):
                notes = dblp_data['notes']['note']
                if isinstance(notes, list):
                    for note in notes:
                        if isinstance(note, dict) and note.get('@type') == 'affiliation':
                            affiliation = note.get('#text', '')
                            if affiliation and affiliation not in enhanced_author.all_affiliations:
                                enhanced_author.all_affiliations.append(affiliation)
        
        # Extract publication timeline from Crossref
        if 'crossref' in combined_data:
            crossref_papers = combined_data['crossref']
            years = []
            subjects = set()
            recent_pubs = []
            
            for paper in crossref_papers[:10]:  # Process first 10 papers
                # Extract publication year
                if paper.get('published-print', {}).get('date-parts'):
                    year = paper['published-print']['date-parts'][0][0]
                    years.append(year)
                elif paper.get('published-online', {}).get('date-parts'):
                    year = paper['published-online']['date-parts'][0][0]
                    years.append(year)
                
                # Extract research subjects
                if paper.get('subject'):
                    subjects.update(paper['subject'])
                
                # Add to recent publications
                recent_pubs.append({
                    'title': paper.get('title', [''])[0] if paper.get('title') else '',
                    'year': years[-1] if years else None,
                    'journal': paper.get('container-title', [''])[0] if paper.get('container-title') else '',
                    'doi': paper.get('DOI', ''),
                    'citations': paper.get('is-referenced-by-count', 0)
                })
            
            if years:
                enhanced_author.first_publication_year = min(years)
                enhanced_author.last_publication_year = max(years)
            
            if subjects:
                enhanced_author.research_areas.extend(list(subjects)[:10])  # Limit to 10 areas
            
            if recent_pubs:
                enhanced_author.recent_publications = recent_pubs
        
        # Extract detailed info from Semantic Scholar
        if 'semantic_scholar_detailed' in combined_data:
            detailed_data = combined_data['semantic_scholar_detailed']
            
            # Extract research interests/areas
            if detailed_data.get('papers'):
                # Analyze paper titles and abstracts for research areas
                paper_texts = []
                recent_papers = []
                
                for paper in detailed_data['papers'][:10]:
                    if paper.get('title'):
                        paper_texts.append(paper['title'])
                    
                    # Add to recent publications with more details
                    recent_papers.append({
                        'title': paper.get('title', ''),
                        'year': paper.get('year'),
                        'venue': paper.get('venue', ''),
                        'citations': paper.get('citationCount', 0),
                        'url': paper.get('url', ''),
                        'paperId': paper.get('paperId', '')
                    })
                
                # Extract keywords/research areas from paper titles
                if paper_texts:
                    research_keywords = self._extract_research_areas_from_titles(paper_texts)
                    enhanced_author.research_areas.extend(research_keywords)
                
                # Update recent publications if we have better data
                if recent_papers and not enhanced_author.recent_publications:
                    enhanced_author.recent_publications = recent_papers
        
        # Remove duplicates from research areas
        enhanced_author.research_areas = list(set(enhanced_author.research_areas))[:15]  # Limit to 15
        
        # Calculate data quality score
        enhanced_author.data_quality_score = self._calculate_quality_score(enhanced_author, sources_successful)
        
        return enhanced_author
    
    def _calculate_quality_score(self, author: EnhancedAuthorResponse, sources: List[str]) -> float:
        """Calculate data quality score based on completeness"""
        score = 0.0
        
        # Base score for having data
        if author.name and author.name != "Unknown":
            score += 0.15
        
        # Score for identifiers (20% of total)
        if author.semantic_scholar_id:
            score += 0.05
        if author.orcid_id:
            score += 0.10
        if author.openalex_id:
            score += 0.05
        
        # Score for affiliations (15% of total)
        if author.primary_affiliation:
            score += 0.05
        if len(author.all_affiliations) > 1:
            score += 0.05
        if len(author.all_affiliations) > 5:
            score += 0.05
        
        # Score for metrics (25% of total)
        if author.citation_count > 0:
            score += 0.08
        if author.h_index > 0:
            score += 0.08
        if author.paper_count > 0:
            score += 0.09
        
        # Score for timeline data (15% of total)
        if author.first_publication_year:
            score += 0.08
        if author.last_publication_year:
            score += 0.07
        
        # Score for research areas (10% of total)
        if len(author.research_areas) > 0:
            score += 0.05
        if len(author.research_areas) > 3:
            score += 0.05
        
        # Score for recent publications (10% of total)
        if len(author.recent_publications) > 0:
            score += 0.05
        if len(author.recent_publications) > 5:
            score += 0.05
        
        # Bonus for multiple sources (5% of total)
        if len(sources) > 2:
            score += 0.03
        if len(sources) > 4:
            score += 0.02
        
        return min(1.0, score)
    
    async def search_authors_batch(self, author_names: List[str], strategy: str = "fast") -> List[MultiSourceAuthorSearchResponse]:
        """Search for multiple authors"""
        results = []
        
        for author_name in author_names:
            try:
                result = await self.search_author(author_name, strategy)
                results.append(result)
                
                # Small delay between requests
                await asyncio.sleep(0.5)
                
            except Exception as e:
                logger.error(f"Error in batch search for {author_name}: {e}")
                results.append(MultiSourceAuthorSearchResponse(
                    success=False,
                    error=f"Search failed: {str(e)}",
                    search_strategy=strategy,
                    sources_attempted=[],
                    sources_successful=[]
                ))
        
        return results
    
    async def _search_semantic_scholar_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search Semantic Scholar API for authors"""
        url = "https://api.semanticscholar.org/graph/v1/author/search"
        
        params = {
            "query": query,
            "limit": limit,
            "fields": "authorId,name,affiliations,paperCount,citationCount,hIndex,externalIds"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def _search_openalex_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search OpenAlex API for authors"""
        url = "https://api.openalex.org/authors"
        
        params = {
            "search": query,
            "per-page": limit,
            "select": "id,display_name,orcid,affiliations,cited_by_count,works_count"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def _search_orcid_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search ORCID API for authors"""
        url = "https://pub.orcid.org/v3.0/search/"
        
        params = {
            "q": f'given-and-family-names:"{query}"',
            "rows": limit
        }
        
        headers = {
            "Accept": "application/json"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _search_dblp_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search DBLP API for computer science authors"""
        url = "https://dblp.org/search/author/api"
        
        params = {
            "q": query,
            "format": "json",
            "h": limit
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    async def _search_crossref_api(self, query: str, limit: int = 10) -> Dict[str, Any]:
        """Search Crossref API for publications by author"""
        url = "https://api.crossref.org/works"
        
        params = {
            "query.author": query,
            "rows": limit,
            "sort": "published",
            "order": "desc"
        }
        
        headers = {
            "User-Agent": "ScholarAI/1.0 (mailto:your-email@example.com)"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params, headers=headers)
            response.raise_for_status()
            return response.json()
    
    async def _get_semantic_scholar_author_details(self, author_id: str) -> Dict[str, Any]:
        """Get detailed author information from Semantic Scholar"""
        url = f"https://api.semanticscholar.org/graph/v1/author/{author_id}"
        
        params = {
            "fields": "name,affiliations,papers.title,papers.year,papers.venue,papers.citationCount,papers.url,papers.paperId"
        }
        
        async with httpx.AsyncClient(timeout=self.timeout) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    
    def _extract_research_areas_from_titles(self, paper_titles: List[str]) -> List[str]:
        """Extract research areas from paper titles using keyword analysis"""
        # Common research area keywords
        cs_keywords = {
            'machine learning', 'deep learning', 'neural networks', 'artificial intelligence',
            'computer vision', 'natural language processing', 'nlp', 'data mining',
            'algorithms', 'distributed systems', 'databases', 'software engineering',
            'human-computer interaction', 'hci', 'cybersecurity', 'networks',
            'reinforcement learning', 'computer graphics', 'robotics', 'blockchain',
            'quantum computing', 'bioinformatics', 'optimization', 'pattern recognition',
            'image processing', 'speech recognition', 'knowledge graphs', 'recommender systems'
        }
        
        medical_keywords = {
            'cancer', 'oncology', 'cardiology', 'neuroscience', 'genomics', 'proteomics',
            'immunology', 'pathology', 'radiology', 'surgery', 'therapy', 'diagnosis',
            'clinical', 'epidemiology', 'pharmacology', 'genetics', 'biomarkers',
            'medical imaging', 'drug discovery', 'precision medicine', 'public health'
        }
        
        physics_keywords = {
            'quantum', 'particle physics', 'condensed matter', 'thermodynamics',
            'electromagnetism', 'optics', 'photonics', 'materials science',
            'nanotechnology', 'semiconductor', 'superconductivity', 'plasma physics'
        }
        
        all_keywords = cs_keywords | medical_keywords | physics_keywords
        
        found_areas = set()
        combined_text = ' '.join(paper_titles).lower()
        
        for keyword in all_keywords:
            if keyword in combined_text:
                # Capitalize properly
                found_areas.add(keyword.title())
        
        return list(found_areas)[:10]  # Limit to 10 areas
    
    def close(self):
        """Close all clients"""
        # Close any clients that need cleanup
        pass
