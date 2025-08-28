#!/usr/bin/env python3
"""
Test script for the arXiv API endpoint

This script tests the new arXiv API endpoint to ensure it works correctly
with the full workflow (excluding PDF processing and storage).
"""

import asyncio
import json
import httpx
from typing import Dict, Any


async def test_arxiv_endpoint():
    """Test the arXiv API endpoint"""
    
    # Test request data
    test_request = {
        "queryTerms": ["machine learning", "optimization"],
        "domain": "Computer Science",
        "batchSize": 5,
        "correlationId": "test-123"
    }
    
    print("🧪 Testing arXiv API endpoint...")
    print(f"📤 Request: {json.dumps(test_request, indent=2)}")
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Test the endpoint
            response = await client.post(
                "http://localhost:8001/api/v1/arxiv/test",
                json=test_request,
                headers={"Content-Type": "application/json"}
            )
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Success!")
                print(f"📊 Response Summary:")
                print(f"   - Status: {result.get('status')}")
                print(f"   - Papers found: {result.get('batchSize')}")
                print(f"   - Search strategy: {result.get('searchStrategy')}")
                print(f"   - Sources used: {result.get('totalSourcesUsed')}")
                print(f"   - AI enhanced: {result.get('aiEnhanced')}")
                print(f"   - Search rounds: {result.get('searchRounds')}")
                
                # Show deduplication stats
                dedup_stats = result.get('deduplicationStats', {})
                print(f"   - Deduplication: {dedup_stats.get('unique_papers', 0)} unique papers")
                
                # Show first paper details
                papers = result.get('papers', [])
                if papers:
                    first_paper = papers[0]
                    print(f"\n📄 First paper:")
                    print(f"   - Title: {first_paper.get('title', 'N/A')[:80]}...")
                    print(f"   - Authors: {len(first_paper.get('authors', []))} authors")
                    print(f"   - DOI: {first_paper.get('doi', 'N/A')}")
                    print(f"   - Source: {first_paper.get('source', 'N/A')}")
                    print(f"   - Year: {first_paper.get('publicationDate', 'N/A')}")
                
                return True
            else:
                print(f"❌ Error: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Exception: {str(e)}")
        return False


async def test_health_endpoint():
    """Test the health endpoint"""
    
    print("\n🏥 Testing health endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/api/v1/arxiv/health")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Health check passed!")
                print(f"   - Status: {result.get('status')}")
                print(f"   - Service: {result.get('service')}")
                print(f"   - Connectivity: {result.get('connectivity')}")
                return True
            else:
                print(f"❌ Health check failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Health check exception: {str(e)}")
        return False


async def test_stats_endpoint():
    """Test the stats endpoint"""
    
    print("\n📊 Testing stats endpoint...")
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get("http://localhost:8001/api/v1/arxiv/stats")
            
            if response.status_code == 200:
                result = response.json()
                print("✅ Stats retrieved!")
                print(f"   - Service: {result.get('service')}")
                print(f"   - AI available: {result.get('ai_available')}")
                print(f"   - AI ready: {result.get('ai_ready')}")
                print(f"   - Config: {result.get('config')}")
                return True
            else:
                print(f"❌ Stats failed: {response.status_code}")
                print(f"Response: {response.text}")
                return False
                
    except Exception as e:
        print(f"❌ Stats exception: {str(e)}")
        return False


async def main():
    """Run all tests"""
    print("🚀 Starting arXiv API endpoint tests...")
    print("=" * 50)
    
    # Test health endpoint first
    health_ok = await test_health_endpoint()
    
    if health_ok:
        # Test stats endpoint
        stats_ok = await test_stats_endpoint()
        
        # Test main endpoint
        main_ok = await test_arxiv_endpoint()
        
        print("\n" + "=" * 50)
        print("📋 Test Results:")
        print(f"   - Health: {'✅ PASS' if health_ok else '❌ FAIL'}")
        print(f"   - Stats: {'✅ PASS' if stats_ok else '❌ FAIL'}")
        print(f"   - Main: {'✅ PASS' if main_ok else '❌ FAIL'}")
        
        if all([health_ok, stats_ok, main_ok]):
            print("\n🎉 All tests passed! arXiv API endpoint is working correctly.")
        else:
            print("\n⚠️ Some tests failed. Check the logs above for details.")
    else:
        print("\n❌ Health check failed. Make sure the service is running on localhost:8001")


if __name__ == "__main__":
    asyncio.run(main())
