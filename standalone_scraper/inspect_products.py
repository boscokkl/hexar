#!/usr/bin/env python3
"""Examine actual product elements on Evo.com"""

import requests
from bs4 import BeautifulSoup

def inspect_product_elements():
    url = 'https://www.evo.com/shop/snowboard/snowboards/all-mountain'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find elements with data-product-id
    product_elements = soup.find_all(attrs={"data-product-id": True})
    print(f"Found {len(product_elements)} elements with data-product-id")
    
    for i, elem in enumerate(product_elements[:5]):
        print(f"\nProduct Element {i+1}:")
        print(f"  Tag: {elem.name}")
        print(f"  Classes: {elem.get('class', [])}")
        print(f"  Product ID: {elem.get('data-product-id')}")
        
        # Look for product name
        text_content = elem.get_text().strip()
        if text_content:
            print(f"  Text (first 100 chars): {text_content[:100]}")
        
        # Look for links within
        links = elem.find_all('a', href=True)
        for link in links[:2]:
            href = link.get('href')
            link_text = link.get_text().strip()
            if href and link_text:
                print(f"  Link: {href} -> '{link_text}'")
        
        # Look for images
        images = elem.find_all('img', src=True)
        for img in images[:1]:
            print(f"  Image: {img.get('src')}")
            print(f"  Alt text: {img.get('alt', 'No alt text')}")
        
        # Look for price elements
        price_elements = elem.find_all(string=lambda text: text and '$' in text)
        for price in price_elements[:2]:
            if price.strip():
                print(f"  Price text: '{price.strip()}'")

if __name__ == "__main__":
    inspect_product_elements()