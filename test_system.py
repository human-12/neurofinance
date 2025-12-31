"""
NeuroFinance System Test Script
Tests all major components and endpoints
"""
import asyncio
import aiohttp
import json
from datetime import datetime


class SystemTester:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
        self.session = None
    
    async def setup(self):
        """Initialize test session"""
        self.session = aiohttp.ClientSession()
        print("🔧 Initializing test session...")
    
    async def cleanup(self):
        """Cleanup test session"""
        if self.session:
            await self.session.close()
        print("✅ Test session closed")
    
    async def test_health(self):
        """Test health endpoint"""
        print("\n📋 Testing health endpoint...")
        try:
            async with self.session.get(f"{self.base_url}/") as resp:
                data = await resp.json()
                assert resp.status == 200
                assert data["status"] == "operational"
                print(f"✅ Health check passed: {data}")
                return True
        except Exception as e:
            print(f"❌ Health check failed: {e}")
            return False
    
    async def test_sentiment_analysis(self):
        """Test sentiment analysis endpoint"""
        print("\n🤖 Testing sentiment analysis...")
        test_texts = [
            "Apple stock surges on strong earnings report",
            "Tesla faces regulatory scrutiny in Europe",
            "Market analysts remain cautiously optimistic"
        ]
        
        try:
            for text in test_texts:
                url = f"{self.base_url}/api/sentiment/analyze"
                params = {"text": text, "source": "test"}
                
                async with self.session.get(url, params=params) as resp:
                    data = await resp.json()
                    assert resp.status == 200
                    result = data[0]
                    print(f"   📝 '{text[:50]}...'")
                    print(f"      → Sentiment: {result['sentiment']} "
                          f"(confidence: {result['confidence']:.2%})")
                    print(f"      → Latency: {result['latency_ms']:.2f}ms")
            
            print("✅ Sentiment analysis tests passed")
            return True
        except Exception as e:
            print(f"❌ Sentiment analysis failed: {e}")
            return False
    
    async def test_news_fetch(self):
        """Test news aggregation"""
        print("\n📰 Testing news aggregation...")
        try:
            url = f"{self.base_url}/api/news/latest"
            params = {"limit": 10}
            
            async with self.session.get(url, params=params) as resp:
                data = await resp.json()
                assert resp.status == 200
                print(f"   Retrieved {len(data)} articles")
                
                if data:
                    article = data[0]
                    print(f"   Sample: {article['title']}")
                    print(f"   Source: {article['source']}")
                
                print("✅ News aggregation test passed")
                return True
        except Exception as e:
            print(f"❌ News aggregation failed: {e}")
            return False
    
    async def test_signals(self):
        """Test market signal generation"""
        print("\n📊 Testing market signal generation...")
        try:
            url = f"{self.base_url}/api/signals/current"
            
            async with self.session.get(url) as resp:
                data = await resp.json()
                assert resp.status == 200
                print(f"   Generated {len(data)} signals")
                
                for signal in data[:3]:
                    print(f"   {signal['symbol']}: {signal['signal']} "
                          f"(strength: {signal['strength']:.2%})")
                
                print("✅ Signal generation test passed")
                return True
        except Exception as e:
            print(f"❌ Signal generation failed: {e}")
            return False
    
    async def test_stats(self):
        """Test platform statistics"""
        print("\n📈 Testing platform statistics...")
        try:
            url = f"{self.base_url}/api/stats"
            
            async with self.session.get(url) as resp:
                data = await resp.json()
                assert resp.status == 200
                print(f"   Articles processed: {data['articles_processed_today']}")
                print(f"   Active connections: {data['active_connections']}")
                print(f"   Average latency: {data['average_latency_ms']:.2f}ms")
                
                print("✅ Statistics test passed")
                return True
        except Exception as e:
            print(f"❌ Statistics test failed: {e}")
            return False
    
    async def run_all_tests(self):
        """Run all system tests"""
        print("=" * 60)
        print("🧪 NeuroFinance System Test Suite")
        print("=" * 60)
        
        await self.setup()
        
        results = {
            "health": await self.test_health(),
            "sentiment": await self.test_sentiment_analysis(),
            "news": await self.test_news_fetch(),
            "signals": await self.test_signals(),
            "stats": await self.test_stats()
        }
        
        await self.cleanup()
        
        print("\n" + "=" * 60)
        print("📊 Test Results Summary")
        print("=" * 60)
        
        passed = sum(results.values())
        total = len(results)
        
        for test, result in results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            print(f"{status} - {test.capitalize()}")
        
        print("-" * 60)
        print(f"Total: {passed}/{total} tests passed")
        
        if passed == total:
            print("\n🎉 All tests passed! System is operational.")
        else:
            print("\n⚠️ Some tests failed. Please check the logs.")
        
        print("=" * 60)
        
        return passed == total


async def main():
    tester = SystemTester()
    success = await tester.run_all_tests()
    return 0 if success else 1


if __name__ == "__main__":
    exit(asyncio.run(main()))
