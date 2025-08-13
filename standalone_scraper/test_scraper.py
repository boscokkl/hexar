"""
Test script for standalone scraper
Quick validation before full run
"""

import asyncio
import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

async def test_configuration():
    """Test configuration and imports"""
    print("🔧 Testing Configuration...")
    
    try:
        from config import ScraperConfig, SamplingMatrix, EvoUrls
        
        print(f"   ✅ Target products: {ScraperConfig.TARGET_PRODUCTS_TOTAL}")
        print(f"   ✅ Matrix total: {SamplingMatrix.get_total_target()}")
        print(f"   ✅ Categories: {len(SamplingMatrix.get_all_categories())}")
        print(f"   ✅ Base URL: {EvoUrls.BASE_URL}")
        
        # Check required environment variables
        if not ScraperConfig.SUPABASE_URL:
            print("   ❌ Missing SUPABASE_URL")
            return False
        if not ScraperConfig.SUPABASE_SERVICE_KEY:
            print("   ❌ Missing SUPABASE_SERVICE_KEY")
            return False
            
        print("   ✅ Environment variables configured")
        return True
        
    except Exception as e:
        print(f"   ❌ Configuration error: {e}")
        return False

async def test_database_connection():
    """Test database connection"""
    print("\n🗄️ Testing Database Connection...")
    
    try:
        from database import ScraperDatabase
        
        db = ScraperDatabase()
        
        # Test table access
        table_exists = await db.ensure_table_exists()
        if table_exists:
            print("   ✅ Database table accessible")
            
            # Get current stats
            stats = db.get_database_stats()
            if 'error' not in stats:
                print(f"   ✅ Current products in DB: {stats.get('total_products', 0)}")
                
                # Show matrix breakdown if any products exist
                if stats.get('total_products', 0) > 0:
                    print("   📊 Current matrix breakdown:")
                    for skill, styles in stats.get('matrix_breakdown', {}).items():
                        for style, count in styles.items():
                            print(f"      {skill} × {style}: {count}")
            else:
                print(f"   ⚠️ Database stats error: {stats['error']}")
            
            return True
        else:
            print("   ❌ Database table not accessible")
            print("   💡 Please run the SQL in create_table.sql first")
            return False
            
    except Exception as e:
        print(f"   ❌ Database connection error: {e}")
        return False

async def test_matrix_manager():
    """Test matrix manager functionality"""
    print("\n📊 Testing Matrix Manager...")
    
    try:
        from matrix_manager import MatrixManager
        from models import ScrapedProduct
        
        manager = MatrixManager(target_total=10)  # Small target for testing
        
        print("   ✅ Matrix manager initialized")
        
        # Test priority categories
        priorities = manager.get_priority_categories(limit=3)
        print(f"   ✅ Priority categories: {len(priorities)}")
        for skill, style in priorities[:3]:
            print(f"      {skill} × {style}")
        
        # Test adding a product
        test_product = ScrapedProduct(
            name="Test Burton Custom",
            evo_url="https://www.evo.com/test",
            skill_level="intermediate",
            riding_style="all-mountain",
            product_id="test_product_123"  # Add required product_id
        )
        
        can_accept = manager.can_accept_product("intermediate", "all-mountain")
        print(f"   ✅ Can accept test product: {can_accept}")
        
        if can_accept:
            added = manager.add_product(test_product)
            print(f"   ✅ Test product added: {added}")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Matrix manager error: {e}")
        return False

async def test_selectors():
    """Test CSS selectors and parsing"""
    print("\n🎯 Testing Selectors and Parsing...")
    
    try:
        from evo_selectors import EvoParser
        
        # Test price parsing
        test_prices = ["$599.95", "749.99", "$1,299.00", "Price not available"]
        for price_text in test_prices:
            parsed = EvoParser.parse_price(price_text)
            print(f"   Price '{price_text}' → {parsed}")
        
        # Test brand extraction
        test_names = [
            "Burton Custom Snowboard 2024",
            "Lib Tech T.Rice Pro HP",
            "Jones Mind Expander Snowboard"
        ]
        for name in test_names:
            brand = EvoParser.extract_brand_from_title(name)
            print(f"   Brand from '{name}' → '{brand}'")
        
        # Test classification
        test_product = {
            'title': 'Burton Custom All-Mountain Snowboard',
            'description': 'Perfect for intermediate to advanced riders',
            'url': '/snowboards/all-mountain/burton-custom'
        }
        
        skill = EvoParser.classify_skill_level(test_product['title'], test_product['description'])
        style = EvoParser.classify_riding_style(test_product['title'], test_product['description'], test_product['url'])
        
        print(f"   Classification: {skill} × {style}")
        print("   ✅ Selector tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Selector test error: {e}")
        return False

async def test_small_scrape():
    """Test actual scraping with a single page"""
    print("\n🕷️ Testing Small Scrape...")
    
    try:
        from scraper import EvoScraper
        from config import EvoUrls
        
        # Create scraper with minimal target
        original_target = os.environ.get('TARGET_PRODUCTS_TOTAL', '50')
        os.environ['TARGET_PRODUCTS_TOTAL'] = '3'  # Test with 3 products
        
        scraper = EvoScraper()
        
        # Test single page scrape
        test_url = EvoUrls.build_category_url('all-mountain')
        print(f"   Testing URL: {test_url}")
        
        # Make a single request to test connectivity
        response = scraper._make_request(test_url)
        if response:
            print(f"   ✅ Successfully fetched page (status: {response.status_code})")
            
            # Test HTML parsing
            from bs4 import BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            product_elements = scraper._find_product_elements(soup)
            print(f"   ✅ Found {len(product_elements)} product elements")
            
            if product_elements:
                # Test product extraction
                first_element = product_elements[0]
                test_product = scraper._extract_product(first_element, 'intermediate', 'all-mountain')
                
                if test_product:
                    print(f"   ✅ Extracted test product: {test_product.name}")
                    print(f"      Brand: {test_product.brand}")
                    print(f"      Price: ${test_product.current_price}")
                    print(f"      URL: {test_product.evo_url}")
                else:
                    print("   ⚠️ Could not extract product data")
            else:
                print("   ⚠️ No product elements found - may need selector updates")
        else:
            print("   ❌ Failed to fetch page")
            return False
        
        # Restore original target
        os.environ['TARGET_PRODUCTS_TOTAL'] = original_target
        
        print("   ✅ Small scrape test completed")
        return True
        
    except Exception as e:
        print(f"   ❌ Small scrape test error: {e}")
        return False

async def main():
    """Run all tests"""
    print("🧪 Standalone Scraper Test Suite")
    print("=" * 50)
    
    tests = [
        ("Configuration", test_configuration),
        ("Database Connection", test_database_connection),
        ("Matrix Manager", test_matrix_manager),
        ("Selectors & Parsing", test_selectors),
        ("Small Scrape", test_small_scrape)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = await test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"   ❌ Test '{test_name}' failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("🎯 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"   {status:<10} {test_name}")
        if result:
            passed += 1
    
    total = len(results)
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! Ready for production scraping.")
        print("\nNext steps:")
        print("   1. Run: python scraper.py")
        print("   2. Monitor progress tables")
        print("   3. Check database for results")
    else:
        print(f"\n⚠️ {total - passed} tests failed. Please fix issues before scraping.")
        
        if not results[1][1]:  # Database test failed
            print("\n💡 Database Fix:")
            print("   1. Copy SQL from create_table.sql")
            print("   2. Run in Supabase SQL Editor")
            print("   3. Check .env configuration")
    
    return passed == total

if __name__ == "__main__":
    try:
        success = asyncio.run(main())
        exit_code = 0 if success else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n👋 Test interrupted")
        sys.exit(1)