"""
Test DuckDuckGo search functionality
No API key required - completely free!
"""
from services.serp_service import SerpService


def test_duckduckgo():
    """Test DuckDuckGo search"""
    print("="*60)
    print("Testing DuckDuckGo Search")
    print("="*60)
    
    try:
        print("\n1. Initializing SerpService...")
        service = SerpService()
        print(f"   ✅ Provider: {service.provider}")
        
        print("\n2. Performing test search...")
        query = "fintech startup Russia"
        results = service.search(query, country="RU", language="ru", num_results=5)
        
        print(f"   ✅ Found {len(results)} results")
        
        if results:
            print("\n3. Sample results:")
            print("-" * 60)
            for i, result in enumerate(results[:3], 1):
                print(f"\n{i}. {result['title']}")
                print(f"   URL: {result['url'][:80]}...")
                if result['snippet']:
                    print(f"   Snippet: {result['snippet'][:100]}...")
            print("-" * 60)
        
        print("\n✅ DuckDuckGo search is working correctly!")
        print("\nBenefits:")
        print("  • Completely FREE - no API key needed")
        print("  • No rate limits (reasonable usage)")
        print("  • Good coverage for most queries")
        print("  • Privacy-focused")
        return True
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print("\nTroubleshooting:")
        print("1. Check internet connection")
        print("2. DuckDuckGo may be blocked in some regions - try VPN")
        print("3. Try switching to SerpAPI if issues persist")
        return False


if __name__ == "__main__":
    import sys
    success = test_duckduckgo()
    sys.exit(0 if success else 1)
