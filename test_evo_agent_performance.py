#!/usr/bin/env python3
"""
Performance test for optimized Evo Agent with real vendor integration
Tests the live market data performance improvements with actual Evo agent

Usage:
    cd hexar-backend  
    python ../test_evo_agent_performance.py
"""

import asyncio
import time
import sys
import os
from typing import List, Dict, Any

# Add the backend directory to the Python path
sys.path.append('/Users/boscolam/Documents/Projects/hexar/hexar-backend')

from services.live_market_service import create_live_market_service
from agents.vendor_agents.base_vendor import ProductSearchRequest

# Mock agent configuration function
def mock_get_agent_config(vendor_id):
    """Mock agent configuration for testing"""
    configs = {
        "evo_com": {
            "agent_id": "evo_com",
            "base_url": "https://www.evo.com",
            "enabled": True
        },
        "evo_standard": {
            "agent_id": "evo_standard", 
            "base_url": "https://www.evo.com",
            "enabled": True
        },
        "evo_light": {
            "agent_id": "evo_light",
            "base_url": "https://www.evo.com", 
            "enabled": True
        }
    }
    return configs.get(vendor_id)

# Patch the config import
import sys
from unittest.mock import patch

# Import with mocked config
with patch('config.get_agent_config', side_effect=mock_get_agent_config):
    from agents.vendor_agents.evo_agent import EvoVendorAgent

# Mock Redis client for testing
class MockRedisClient:
    def __init__(self):
        self.cache = {}
    
    async def get(self, key):
        return self.cache.get(key)
    
    async def setex(self, key, ttl, value):
        self.cache[key] = value
    
    async def delete(self, *keys):
        for key in keys:
            self.cache.pop(key, None)

# Test Agent Registry with real Evo agents
class TestAgentRegistry:
    def __init__(self):
        # Create both standard and light mode Evo agents for comparison
        with patch('config.get_agent_config', side_effect=mock_get_agent_config):
            self.agents = {
                "evo_standard": EvoVendorAgent("evo_standard", "standard"),
                "evo_light": EvoVendorAgent("evo_light", "light")
            }
    
    def get_all_agents(self, include_degraded=True):
        return self.agents

async def test_evo_agent_direct():
    """Test Evo agent performance directly"""
    
    print("🏂 Testing Evo Agent Direct Performance")
    print("=" * 60)
    
    # Test both standard and light mode
    with patch('config.get_agent_config', side_effect=mock_get_agent_config):
        agents = {
            "Standard Mode": EvoVendorAgent("evo_standard", "standard"),
            "Light Mode": EvoVendorAgent("evo_light", "light")
        }
    
    search_request = ProductSearchRequest(
        query="snowboard",
        filters={},
        max_results=5
    )
    
    results = {}
    
    for mode_name, agent in agents.items():
        print(f"\n🧪 Testing {mode_name}")
        print("-" * 30)
        
        try:
            start_time = time.time()
            response = await agent.search_products(search_request)
            end_time = time.time()
            
            response_time = (end_time - start_time) * 1000
            
            print(f"⏱️  Response time: {response_time:.1f}ms")
            print(f"📦 Products found: {len(response.products)}")
            print(f"📊 Status: {response.status}")
            print(f"🎯 Vendor: {response.vendor_id}")
            
            # Show first product as sample
            if response.products:
                first_product = response.products[0]
                print(f"🏂 Sample product: {first_product.name}")
                print(f"💰 Price: {first_product.price}")
                print(f"⭐ Rating: {first_product.rating}")
            
            results[mode_name] = {
                'response_time_ms': response_time,
                'products_found': len(response.products),
                'status': response.status,
                'success': response.status == 'success'
            }
            
        except Exception as e:
            print(f"❌ {mode_name} failed: {e}")
            results[mode_name] = {
                'response_time_ms': float('inf'),
                'products_found': 0,
                'status': 'error',
                'success': False
            }
    
    return results

async def test_evo_in_live_market_service():
    """Test Evo agent through Live Market Service"""
    
    print("\n🔄 Testing Evo Agent through Live Market Service")
    print("=" * 60)
    
    # Create mock Redis client
    redis_client = MockRedisClient()
    
    # Create live market service
    live_market_service = create_live_market_service(redis_client=redis_client)
    
    # Create test agent registry with real Evo agents
    test_registry = TestAgentRegistry()
    
    async def get_test_agents():
        return test_registry.get_all_agents()
    
    # Patch the service to use our test agent registry
    live_market_service._get_available_vendor_agents = get_test_agents
    
    # Test products
    test_products = [
        {
            'product_id': 'test_snowboard_1',
            'name': 'Burton Custom Snowboard',
            'brand': 'Burton',
            'base_price': '$599.99',
            'vendor_sources': ['evo_com']
        },
        {
            'product_id': 'test_snowboard_2', 
            'name': 'Lib Tech Skate Banana',
            'brand': 'Lib Tech',
            'base_price': '$549.99',
            'vendor_sources': ['evo_com']
        },
        {
            'product_id': 'test_snowboard_3',
            'name': 'Jones Flagship',
            'brand': 'Jones',
            'base_price': '$699.99',
            'vendor_sources': ['evo_com']
        }
    ]
    
    print(f"📦 Testing with {len(test_products)} snowboard products")
    print("🎯 Target: <3000ms total enrichment time")
    print("-" * 60)
    
    # Test cold cache (first run)
    print("🧊 Cold Cache Test")
    start_time = time.time()
    
    try:
        enriched_products = await live_market_service.enrich_with_live_market_data(
            test_products,
            force_refresh=True
        )
        
        cold_cache_time = (time.time() - start_time) * 1000
        
        print(f"⏱️  Total time: {cold_cache_time:.1f}ms")
        print(f"📊 Products enriched: {len(enriched_products)}")
        
        # Show enrichment details
        for product in enriched_products:
            data_freshness = product.get('data_freshness', 'unknown')
            vendor_details = product.get('vendor_details', [])
            print(f"  🏂 {product['name']}: {data_freshness} data, {len(vendor_details)} vendors")
        
        # Performance metrics
        metrics = live_market_service.get_performance_metrics()
        print(f"\n📈 Performance Metrics:")
        print(f"  🎯 Success rate: {metrics['success_rate']:.1f}%")
        print(f"  ⚡ Avg response time: {metrics['average_response_time_ms']:.1f}ms")
        print(f"  🔍 Cache hit rate: {metrics['cache_hit_rate']:.1f}%")
        print(f"  🚀 Concurrent vendors: {metrics['max_concurrent_vendors']}")
        print(f"  ⏱️  Vendor timeout: {metrics['vendor_timeout_seconds']}s")
        
    except Exception as e:
        print(f"❌ Cold cache test failed: {e}")
        import traceback
        traceback.print_exc()
        cold_cache_time = float('inf')
    
    print("-" * 60)
    
    # Test warm cache (second run)
    print("🔥 Warm Cache Test")
    start_time = time.time()
    
    try:
        enriched_products = await live_market_service.enrich_with_live_market_data(
            test_products,
            force_refresh=False
        )
        
        warm_cache_time = (time.time() - start_time) * 1000
        
        print(f"⏱️  Total time: {warm_cache_time:.1f}ms")
        print(f"📊 Products enriched: {len(enriched_products)}")
        
        # Updated metrics
        metrics = live_market_service.get_performance_metrics()
        print(f"🔍 Updated cache hit rate: {metrics['cache_hit_rate']:.1f}%")
        print(f"🗂️  Dedup cache size: {metrics['deduplication_cache_size']}")
        
    except Exception as e:
        print(f"❌ Warm cache test failed: {e}")
        warm_cache_time = float('inf')
    
    return {
        'cold_cache_time_ms': cold_cache_time,
        'warm_cache_time_ms': warm_cache_time,
        'target_met': cold_cache_time <= 3000
    }

async def main():
    """Main test execution"""
    
    print("🚀 EVO AGENT PERFORMANCE TEST")
    print("Testing real Evo.com agent with optimizations")
    print("=" * 60)
    
    try:
        # Test 1: Direct agent performance
        direct_results = await test_evo_agent_direct()
        
        # Test 2: Agent through live market service
        service_results = await test_evo_in_live_market_service()
        
        print("\n" + "=" * 60)
        print("📊 FINAL RESULTS SUMMARY")
        print("=" * 60)
        
        # Direct agent results
        print("🏂 Direct Agent Performance:")
        for mode, result in direct_results.items():
            status_icon = "✅" if result['success'] else "❌"
            print(f"  {status_icon} {mode}: {result['response_time_ms']:.1f}ms ({result['products_found']} products)")
        
        # Service integration results
        print(f"\n🔄 Live Market Service Performance:")
        print(f"  🧊 Cold cache: {service_results['cold_cache_time_ms']:.1f}ms")
        print(f"  🔥 Warm cache: {service_results['warm_cache_time_ms']:.1f}ms")
        
        # Performance analysis
        target_time = 3000
        original_time = 12000
        
        if service_results['target_met']:
            improvement = ((original_time - service_results['cold_cache_time_ms']) / original_time) * 100
            print(f"\n🎉 SUCCESS: Performance target achieved!")
            print(f"   📈 {improvement:.1f}% improvement over baseline")
            print(f"   ⚡ {service_results['cold_cache_time_ms']:.1f}ms < {target_time}ms target")
        else:
            remaining = service_results['cold_cache_time_ms'] - target_time
            print(f"\n⚠️  NEEDS WORK: Target not fully met")
            print(f"   🔧 Additional optimization needed: {remaining:.1f}ms")
        
        # Light mode comparison
        if 'Light Mode' in direct_results and 'Standard Mode' in direct_results:
            light_time = direct_results['Light Mode']['response_time_ms']
            standard_time = direct_results['Standard Mode']['response_time_ms']
            if light_time < standard_time:
                speedup = ((standard_time - light_time) / standard_time) * 100
                print(f"\n⚡ Light mode optimization: {speedup:.1f}% faster than standard mode")
        
        return service_results['target_met']
        
    except Exception as e:
        print(f"\n❌ TEST EXECUTION FAILED: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)