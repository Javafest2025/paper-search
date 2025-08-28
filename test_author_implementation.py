#!/usr/bin/env python3
"""
Simple test script for the Author Search implementation
"""

import asyncio
import json
from app.api.api_v1.authors import SemanticScholarAuthorService, AuthorSearchRequest


async def test_author_search():
    """Test the author search functionality"""
    
    print("🧪 Testing Author Search Implementation...")
    
    # Initialize the service
    service = SemanticScholarAuthorService()
    
    # Test 1: Basic search with exact match
    print("\n1. Testing basic author search with exact match...")
    try:
        result = await service.search_authors(
            query="Jun Wu",
            limit=5,
            fields="name,affiliations,paperCount",
            exact_match=True
        )
        
        print(f"✅ Success! Found {len(result.get('data', []))} exact matches")
        print(f"   Total results: {result.get('total', 0)}")
        
        if result.get('data'):
            for i, author in enumerate(result['data']):
                print(f"   Author {i+1}: {author.get('name', 'N/A')}")
                print(f"   Affiliations: {author.get('affiliations', [])}")
                print(f"   Paper count: {author.get('paperCount', 'N/A')}")
                print(f"   External IDs: {author.get('externalIds', {})}")
                if author.get('papers'):
                    print(f"   Papers included: {len(author['papers'])} papers")
                print()
            
    except Exception as e:
        print(f"❌ Error in basic search: {str(e)}")
    
    # Test 2: Search without exact match (all variations)
    print("\n2. Testing search without exact match (all variations)...")
    try:
        result = await service.search_authors(
            query="Jun Wu",
            limit=10,
            offset=0,
            fields="name,paperCount,citationCount",
            exact_match=False
        )
        
        print(f"✅ Success! Found {len(result.get('data', []))} total matches")
        print(f"   Total results: {result.get('total', 0)}")
        print(f"   Next offset: {result.get('next', 'N/A')}")
        
        if result.get('data'):
            print("   All variations found:")
            for i, author in enumerate(result['data'][:5]):  # Show first 5
                print(f"     {i+1}. {author.get('name', 'N/A')} (Papers: {author.get('paperCount', 'N/A')})")
            if len(result['data']) > 5:
                print(f"     ... and {len(result['data']) - 5} more")
        
    except Exception as e:
        print(f"❌ Error in all variations test: {str(e)}")
    
    # Test 3: Search with papers (exact match)
    print("\n3. Testing search with papers (exact match)...")
    try:
        result = await service.search_authors(
            query="Jun Wu",
            limit=2,
            fields="name,affiliations,papers.title,papers.year",
            exact_match=True
        )
        
        print(f"✅ Success! Found {len(result.get('data', []))} exact matches")
        if result.get('data'):
            for i, author in enumerate(result['data']):
                print(f"   Author {i+1}: {author.get('name', 'N/A')}")
                if author.get('papers'):
                    print(f"   Papers found: {len(author['papers'])}")
                    if author['papers']:
                        first_paper = author['papers'][0]
                        print(f"   First paper: {first_paper.get('title', 'N/A')} ({first_paper.get('year', 'N/A')})")
                print()
        
    except Exception as e:
        print(f"❌ Error in papers test: {str(e)}")
    
    # Test 4: Test request model
    print("\n4. Testing request model...")
    try:
        request = AuthorSearchRequest(
            query="Test Author",
            limit=10,
            fields="name,affiliations"
        )
        
        print(f"✅ Request model works!")
        print(f"   Query: {request.query}")
        print(f"   Limit: {request.limit}")
        print(f"   Fields: {request.fields}")
        
    except Exception as e:
        print(f"❌ Error in request model: {str(e)}")
    
    print("\n🎉 Author Search Implementation Test Complete!")


if __name__ == "__main__":
    asyncio.run(test_author_search())
