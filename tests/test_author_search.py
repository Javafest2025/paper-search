"""
Tests for Author Search API endpoints
"""

import pytest
import httpx
from unittest.mock import AsyncMock, patch
from app.api.api_v1.authors import SemanticScholarAuthorService, AuthorSearchRequest


@pytest.fixture
def author_service():
    return SemanticScholarAuthorService()


@pytest.fixture
def mock_response():
    return {
        "total": 15117,
        "offset": 0,
        "next": 100,
        "data": [
            {
                "authorId": "1741101",
                "name": "Oren Etzioni",
                "url": "https://www.semanticscholar.org/author/1741101",
                "affiliations": ["Allen Institute for AI"],
                "homepage": "https://allenai.org/",
                "paperCount": 10,
                "citationCount": 50,
                "hIndex": 5,
                "externalIds": {
                    "DBLP": [123]
                },
                "papers": [
                    {
                        "paperId": "5c5751d45e298cea054f32b392c12c61027d2fe7",
                        "corpusId": 215416146,
                        "title": "Construction of the Literature Graph in Semantic Scholar",
                        "year": 2020,
                        "citationCount": 453,
                        "venue": "Annual Meeting of the Association for Computational Linguistics"
                    }
                ]
            }
        ]
    }


class TestSemanticScholarAuthorService:
    """Test the Semantic Scholar Author Service"""
    
    @pytest.mark.asyncio
    async def test_search_authors_success(self, author_service, mock_response):
        """Test successful author search"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            result = await author_service.search_authors(
                query="Oren Etzioni",
                limit=10,
                fields="name,affiliations,url"
            )
            
            assert result == mock_response
            mock_get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_search_authors_with_defaults(self, author_service, mock_response):
        """Test author search with default parameters"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = mock_response
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            result = await author_service.search_authors(query="test")
            
            assert result == mock_response
            # Verify default parameters were used
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == 100
            assert call_args[1]['params']['offset'] == 0
    
    @pytest.mark.asyncio
    async def test_search_authors_limit_validation(self, author_service):
        """Test that limit is properly validated"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = {"total": 0, "data": []}
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            # Test with limit > 1000 (should be capped)
            await author_service.search_authors(query="test", limit=1500)
            
            call_args = mock_get.call_args
            assert call_args[1]['params']['limit'] == 1000
    
    @pytest.mark.asyncio
    async def test_search_authors_offset_validation(self, author_service):
        """Test that offset is properly validated"""
        with patch('httpx.AsyncClient.get') as mock_get:
            mock_response_obj = AsyncMock()
            mock_response_obj.json.return_value = {"total": 0, "data": []}
            mock_response_obj.raise_for_status.return_value = None
            mock_get.return_value = mock_response_obj
            
            # Test with negative offset (should be set to 0)
            await author_service.search_authors(query="test", offset=-10)
            
            call_args = mock_get.call_args
            assert call_args[1]['params']['offset'] == 0


class TestAuthorSearchRequest:
    """Test the AuthorSearchRequest model"""
    
    def test_valid_request(self):
        """Test valid request creation"""
        request = AuthorSearchRequest(
            query="Oren Etzioni",
            limit=50,
            offset=10,
            fields="name,affiliations"
        )
        
        assert request.query == "Oren Etzioni"
        assert request.limit == 50
        assert request.offset == 10
        assert request.fields == "name,affiliations"
    
    def test_default_values(self):
        """Test default values"""
        request = AuthorSearchRequest(query="test")
        
        assert request.query == "test"
        assert request.limit == 100
        assert request.offset == 0
        assert "name" in request.fields
        assert "affiliations" in request.fields


if __name__ == "__main__":
    pytest.main([__file__])
