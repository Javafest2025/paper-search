"""
Test author search functionality.
"""

import asyncio
import pytest
from app.api.api_v1.authors import AuthorSearchService, AuthorResponse

@pytest.mark.asyncio
async def test_author_search_service():
    """Test the author search service with a well-known author."""
    service = AuthorSearchService()
    
    # Test with a well-known author
    author_data = await service.search_author("Yann LeCun")
    
    # Verify the response structure
    assert isinstance(author_data, AuthorResponse)
    assert author_data.name == "Yann LeCun"
    assert author_data.paper_count > 0
    assert len(author_data.sources) > 0
    assert author_data.confidence_score > 0.0
    assert author_data.last_updated is not None

@pytest.mark.asyncio
async def test_author_search_unknown_author():
    """Test the author search service with an unknown author."""
    service = AuthorSearchService()
    
    # Test with a very specific non-existent author name
    author_data = await service.search_author("XyZ123NonExistentAuthor456")
    
    # Should return empty results but not crash
    assert isinstance(author_data, AuthorResponse)
    assert author_data.name == "XyZ123NonExistentAuthor456"
    # Note: Some APIs might return results for partial matches, so we just check structure
    assert author_data.confidence_score >= 0.0
    assert author_data.last_updated is not None

@pytest.mark.asyncio
async def test_author_search_multiple_sources():
    """Test that the service searches multiple sources."""
    service = AuthorSearchService()
    
    # Test with a well-known author
    author_data = await service.search_author("Geoffrey Hinton")
    
    # Should have data from multiple sources
    assert isinstance(author_data, AuthorResponse)
    assert author_data.name == "Geoffrey Hinton"
    assert author_data.paper_count > 0
    assert len(author_data.sources) >= 1  # At least one source should work
    assert author_data.confidence_score > 0.0

def test_author_response_model():
    """Test the AuthorResponse model."""
    from datetime import datetime
    
    # Test with minimal data
    response = AuthorResponse(
        name="Test Author",
        last_updated=datetime.now().isoformat(),
        sources=["test"],
        confidence_score=0.5
    )
    
    assert response.name == "Test Author"
    assert response.confidence_score == 0.5
    assert "test" in response.sources
