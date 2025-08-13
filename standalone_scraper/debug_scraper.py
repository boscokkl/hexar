#!/usr/bin/env python3
"""Debug version of scraper to test actual product extraction"""

import requests
from bs4 import BeautifulSoup
import sys
import os
sys.path.append('.')

from evo_selectors import EvoSelectors, EvoParser
from models import ScrapedProduct
from database import ScraperDatabase

def debug_scrape():
    url = 'https://www.evo.com/shop/snowboard/snowboards/all-mountain'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    print(f"Debugging: {url}")
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')
    
    print(f"Status: {response.status_code}")
    print(f"Page length: {len(response.text)}")
    
    # Test each selector individually
    for selector in EvoSelectors.PRODUCT_CONTAINERS:
        elements = soup.select(selector)
        print(f"Selector '{selector}': {len(elements)} elements")
        
        if elements and len(elements) > 0:
            print(f"  Using selector: {selector}")
            
            # Try to extract from first few products
            for i, element in enumerate(elements[:3]):
                print(f"\n  Product {i+1}:")
                
                # Extract basic info
                name = EvoParser.extract_text(element, EvoSelectors.NAME_SELECTORS)
                price_text = EvoParser.extract_text(element, EvoSelectors.PRICE_SELECTORS)
                url_path = EvoParser.extract_url(element, EvoSelectors.URL_SELECTORS)
                image_url = EvoParser.extract_image_url(element, EvoSelectors.IMAGE_SELECTORS)
                
                print(f"    Name: {name}")
                print(f"    Price text: {price_text}")
                print(f"    URL: {url_path}")
                print(f"    Image: {image_url}")
                
                if name:
                    # Try to create a product
                    try:
                        current_price = EvoParser.parse_price(price_text) if price_text else None
                        brand = EvoParser.extract_brand_from_title(name)
                        evo_url = EvoParser.ensure_absolute_url(url_path) if url_path else 'https://www.evo.com'
                        
                        product = ScrapedProduct(
                            name=name,
                            brand=brand,
                            evo_url=evo_url,
                            image_urls=[image_url] if image_url else [],
                            current_price=current_price,
                            skill_level="intermediate",  # Test classification
                            riding_style="all-mountain"
                        )
                        
                        print(f"    ✅ Created product: {product.product_id}")
                        print(f"    Brand: {product.brand}")
                        print(f"    Price: ${product.current_price}")
                        
                        # Test database insertion
                        try:
                            db = ScraperDatabase()
                            if db.insert_product(product):
                                print(f"    ✅ Database insert successful")
                            else:
                                print(f"    ❌ Database insert failed")
                        except Exception as e:
                            print(f"    ❌ Database error: {e}")
                        
                    except Exception as e:
                        print(f"    ❌ Product creation failed: {e}")
                else:
                    print(f"    ❌ No name found")
            
            # If we found working products, we're done
            if elements:
                break
    
    print(f"\nDebug complete!")

if __name__ == "__main__":
    debug_scrape()