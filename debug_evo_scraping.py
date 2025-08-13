#!/usr/bin/env python3
"""
Debug Evo.com scraping selectors to verify if website structure changed
"""

import requests
from bs4 import BeautifulSoup
import time

def test_evo_selectors():
    """Test current Evo.com selectors"""
    
    print("🔍 Testing Evo.com scraping selectors")
    print("=" * 50)
    
    # Enhanced headers to avoid bot detection
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'DNT': '1',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    url = "https://www.evo.com/shop/snowboard/snowboards"
    
    try:
        print(f"📡 Fetching: {url}")
        response = requests.get(url, headers=headers, timeout=10)
        print(f"✅ Response status: {response.status_code}")
        
        if response.status_code != 200:
            print(f"❌ Failed to fetch page: HTTP {response.status_code}")
            return
        
        soup = BeautifulSoup(response.text, 'html.parser')
        print(f"📄 Page size: {len(response.text):,} characters")
        
        # Check page title
        title = soup.find('title')
        if title:
            print(f"📰 Page title: {title.get_text()}")
        
        # Test each selector from the agent
        selectors_to_test = [
            '.product-thumb',           # Primary Evo selector
            '.js-product-thumb',        # JS-enhanced selector  
            '.larger-image-product-thumb',  # Large format
            '.product-tile',            # Generic tile
            '.product-item',            # Generic item
            '.product-card',            # Generic card
            '[data-productid]',         # Data attribute
            '[data-testid*="product"]', # Test ID
            '.tile',                    # Simple tile
            '.item',                    # Simple item
            'article[data-product]',    # Article element
            '.product',                 # Generic product
            '[class*="product"]'        # Any class containing "product"
        ]
        
        print(f"\n🎯 Testing {len(selectors_to_test)} selectors:")
        print("-" * 30)
        
        found_any = False
        
        for selector in selectors_to_test:
            elements = soup.select(selector)
            count = len(elements)
            
            if count > 0:
                print(f"✅ {selector:<25} → {count} elements")
                found_any = True
                
                # Show sample content for first match
                if count > 0:
                    sample = elements[0]
                    text = sample.get_text(strip=True)[:100]
                    if text:
                        print(f"   Sample: {text}...")
                    
                    # Check for links and images
                    links = sample.find_all('a', href=True)
                    images = sample.find_all('img')
                    if links:
                        print(f"   Links: {len(links)}")
                    if images:
                        print(f"   Images: {len(images)}")
                    
            else:
                print(f"❌ {selector:<25} → 0 elements")
        
        if not found_any:
            print(f"\n⚠️ NO PRODUCT ELEMENTS FOUND!")
            print("This confirms the issue: Evo.com structure changed")
            
            # Let's check what's actually on the page
            print(f"\n🔍 Analyzing page structure...")
            
            # Look for any div with common e-commerce classes
            common_classes = soup.find_all('div', class_=True)
            class_counts = {}
            
            for div in common_classes[:50]:  # Check first 50 divs
                for class_name in div.get('class', []):
                    if any(term in class_name.lower() for term in ['product', 'item', 'tile', 'card', 'thumb']):
                        class_counts[class_name] = class_counts.get(class_name, 0) + 1
            
            if class_counts:
                print("📊 Potential product-related classes found:")
                for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:10]:
                    print(f"   {class_name}: {count} instances")
            
            # Check for JavaScript-rendered content indicators
            scripts = soup.find_all('script')
            js_indicators = 0
            for script in scripts:
                if script.string and any(term in script.string.lower() for term in ['react', 'angular', 'vue', 'product']):
                    js_indicators += 1
            
            if js_indicators > 0:
                print(f"⚡ Found {js_indicators} scripts with JS framework indicators")
                print("💡 Page may be client-side rendered (needs browser automation)")
            
        else:
            print(f"\n✅ Found working selectors!")
            
    except requests.RequestException as e:
        print(f"❌ Network error: {e}")
    except Exception as e:
        print(f"❌ Parsing error: {e}")

if __name__ == "__main__":
    test_evo_selectors()