#!/usr/bin/env python3
"""Quick inspection of Evo.com page structure"""

import requests
from bs4 import BeautifulSoup
import re

def inspect_evo_structure():
    url = 'https://www.evo.com/shop/snowboard/snowboards/all-mountain'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    print(f"Inspecting: {url}")
    
    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    print(f"Status: {response.status_code}")
    print(f"Page length: {len(response.text)}")
    
    # Look for product links
    product_links = soup.find_all('a', href=re.compile(r'/snowboards/[^/]+/[^/]+$'))
    print(f"\nFound {len(product_links)} potential product links")

    if product_links:
        for i, link in enumerate(product_links[:3]):
            print(f"\nProduct {i+1}:")
            print(f"  URL: {link.get('href')}")
            print(f"  Text: '{link.get_text().strip()}'")
            print(f"  Link classes: {link.get('class', [])}")
            
            # Get parent container
            parent = link.parent
            if parent:
                print(f"  Parent: {parent.name} with classes {parent.get('class', [])}")
                
                # Look for price in surrounding area
                grandparent = parent.parent if parent.parent else None
                if grandparent:
                    price_text = grandparent.get_text()
                    price_match = re.search(r'\$[\d,]+\.?\d*', price_text)
                    if price_match:
                        print(f"  Price found: {price_match.group()}")
    
    # Also look for grid/listing containers
    print(f"\nLooking for grid containers:")
    grid_selectors = [
        '.product-grid',
        '.results-grid', 
        '.listing-grid',
        '.products-container',
        '[class*="grid"]',
        '[class*="result"]'
    ]
    
    for selector in grid_selectors:
        elements = soup.select(selector)
        if elements:
            print(f"  Found {len(elements)} elements with selector: {selector}")
            elem = elements[0]
            print(f"    Classes: {elem.get('class', [])}")
            children = elem.find_all(['div', 'article', 'a'], recursive=False)
            print(f"    Direct children: {len(children)}")

if __name__ == "__main__":
    inspect_evo_structure()