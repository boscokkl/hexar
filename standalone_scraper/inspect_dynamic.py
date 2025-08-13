#!/usr/bin/env python3
"""Check if Evo.com loads products dynamically"""

import requests
from bs4 import BeautifulSoup
import json
import re

def inspect_dynamic_content():
    url = 'https://www.evo.com/shop/snowboard/snowboards/all-mountain'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    print("Looking for dynamic content indicators...")
    
    # Look for JSON data in script tags
    script_tags = soup.find_all('script')
    print(f"Found {len(script_tags)} script tags")
    
    for i, script in enumerate(script_tags):
        if script.string:
            content = script.string.strip()
            
            # Look for product data patterns
            if any(keyword in content.lower() for keyword in ['product', 'snowboard', 'price', 'item']):
                print(f"\nScript {i+1} contains potential product data:")
                print(f"  Length: {len(content)}")
                
                # Try to find JSON objects
                json_matches = re.findall(r'\{[^{}]*"[^"]*product[^"]*"[^{}]*\}', content, re.IGNORECASE)
                if json_matches:
                    print(f"  Found {len(json_matches)} potential product JSON objects")
                    for j, match in enumerate(json_matches[:2]):
                        print(f"    JSON {j+1}: {match[:100]}...")
                
                # Look for specific patterns
                if 'window.' in content and ('products' in content.lower() or 'items' in content.lower()):
                    print(f"  Contains window object assignments")
                    
                if content.count('"') > 50:  # Likely contains structured data
                    print(f"  High quote count ({content.count('"')}) - likely structured data")
    
    # Look for any elements that might contain product data
    print(f"\nLooking for elements with data attributes...")
    data_elements = soup.find_all(attrs={"data-product": True})
    print(f"Found {len(data_elements)} elements with data-product")
    
    data_id_elements = soup.find_all(attrs={"data-product-id": True})
    print(f"Found {len(data_id_elements)} elements with data-product-id")
    
    # Look for React/Vue mounting points
    react_elements = soup.find_all(attrs={"id": re.compile(r'(app|react|vue|root)', re.I)})
    print(f"Found {len(react_elements)} potential SPA mounting points")
    
    for elem in react_elements:
        print(f"  {elem.name} with id='{elem.get('id')}' classes={elem.get('class', [])}")

if __name__ == "__main__":
    inspect_dynamic_content()