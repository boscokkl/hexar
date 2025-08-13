#!/usr/bin/env python3
"""Find the actual product containers"""

import requests
from bs4 import BeautifulSoup

def find_product_containers():
    url = 'https://www.evo.com/shop/snowboard/snowboards/all-mountain'
    headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'}

    response = requests.get(url, headers=headers)
    soup = BeautifulSoup(response.text, 'html.parser')

    # Find review containers and work up to find product containers
    review_containers = soup.find_all('div', class_='review-container')
    print(f"Found {len(review_containers)} review containers")
    
    if review_containers:
        first_review = review_containers[0]
        print(f"\nAnalyzing first review container:")
        print(f"Product ID: {first_review.get('data-product-id')}")
        
        # Walk up the DOM tree to find the product container
        current = first_review
        level = 0
        while current and level < 5:
            print(f"\nLevel {level}: {current.name} with classes {current.get('class', [])}")
            
            # Look for product name, price, or image in this container
            if current.name != 'div' or level == 0:
                current = current.parent
                level += 1
                continue
                
            # Check if this looks like a product container
            text = current.get_text()
            has_price = '$' in text
            has_snowboard = 'snowboard' in text.lower()
            
            if has_price or has_snowboard:
                print(f"  Contains price: {has_price}")
                print(f"  Contains 'snowboard': {has_snowboard}")
                
                # Look for specific elements
                links = current.find_all('a', href=True)
                product_links = [l for l in links if '/snowboards/' in l.get('href', '')]
                if product_links:
                    print(f"  Product links: {len(product_links)}")
                    for link in product_links[:1]:
                        print(f"    {link.get('href')} -> '{link.get_text().strip()}'")
                
                images = current.find_all('img', src=True)
                if images:
                    print(f"  Images: {len(images)}")
                    for img in images[:1]:
                        print(f"    {img.get('src')}")
                        print(f"    Alt: {img.get('alt', 'No alt')}")
                
                # This might be our product container
                if product_links and images:
                    print(f"  *** This looks like a product container! ***")
                    break
            
            current = current.parent
            level += 1

if __name__ == "__main__":
    find_product_containers()