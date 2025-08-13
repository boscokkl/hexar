#!/usr/bin/env python3
"""
Detail enrichment scraper: Visit individual product pages to extract detailed specs
This will fill in the missing technical specifications and optional fields
"""

import asyncio
import time
import logging
import requests
import re
from typing import List, Dict, Optional
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# Initialize colorama
init()

from config import ScraperConfig
from models import ScrapedProduct
from database import ScraperDatabase

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class DetailEnrichmentScraper:
    """Scraper that enriches existing products with detailed specifications"""
    
    def __init__(self):
        self.db = ScraperDatabase()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ScraperConfig.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        # Detail page selectors for Evo.com product pages
        self.detail_selectors = {
            'model_year': [
                '.product-details__year',
                '.product-year', 
                '[data-testid="product-year"]'
            ],
            'board_lengths': [
                '.product-sizes',
                '.size-selector option',
                '.product-options .size',
                '.sizes-available'
            ],
            'flex_rating': [
                '.flex-rating',
                '.product-flex', 
                '[data-testid="flex"]',
                '.specs-flex'
            ],
            'camber_profile': [
                '.camber-profile',
                '.product-camber',
                '[data-testid="camber"]',
                '.specs-camber'
            ],
            'shape': [
                '.board-shape',
                '.product-shape',
                '[data-testid="shape"]',
                '.specs-shape'
            ],
            'description': [
                '.product-description',
                '.product-details__description',
                '[data-testid="description"]',
                '.pdp-description'
            ],
            'specifications': [
                '.product-specifications',
                '.specs-table',
                '.product-specs',
                '.specifications'
            ],
            'features': [
                '.product-features',
                '.key-features',
                '[data-testid="features"]',
                '.features-list'
            ],
            'reviews': [
                '.reviews-summary',
                '.product-reviews',
                '[data-testid="reviews"]'
            ],
            'price_original': [
                '.price-original',
                '.msrp-price',
                '.original-price',
                '.strikethrough-price'
            ],
            'price_sale': [
                '.price-sale',
                '.sale-price',
                '.discounted-price'
            ]
        }
    
    async def enrich_existing_products(self) -> bool:
        """Enrich existing products with detailed specifications"""
        
        print(f"{Fore.GREEN}🔍 Detail Enrichment Scraper{Style.RESET_ALL}")
        print(f"   Strategy: Visit each product page for detailed specs")
        
        # Get all existing products
        try:
            result = self.db.client.table("scraped_snowboard_products").select("*").execute()
            products = result.data
            
            if not products:
                print(f"{Fore.RED}❌ No products found to enrich{Style.RESET_ALL}")
                return False
            
            print(f"   Found {len(products)} products to enrich")
            
        except Exception as e:
            print(f"{Fore.RED}❌ Error fetching products: {e}{Style.RESET_ALL}")
            return False
        
        enriched_count = 0
        failed_count = 0
        
        # Process each product
        for i, product in enumerate(products):
            print(f"\n{Fore.CYAN}📄 [{i+1}/{len(products)}] Enriching: {product['name'][:50]}...{Style.RESET_ALL}")
            
            try:
                enriched_data = await self._enrich_product_details(product)
                
                if enriched_data:
                    # Update database with enriched data
                    update_result = self.db.client.table("scraped_snowboard_products")\
                        .update(enriched_data)\
                        .eq("product_id", product["product_id"])\
                        .execute()
                    
                    if update_result.data:
                        enriched_count += 1
                        print(f"   ✅ Updated with {len([k for k, v in enriched_data.items() if v])} new fields")
                    else:
                        failed_count += 1
                        print(f"   ❌ Database update failed")
                else:
                    failed_count += 1
                    print(f"   ⚠️ No additional data found")
                
                # Rate limiting to be respectful
                await asyncio.sleep(ScraperConfig.DELAY_SECONDS)
                
            except Exception as e:
                failed_count += 1
                print(f"   ❌ Error: {e}")
                await asyncio.sleep(1.0)  # Brief pause on error
        
        # Generate summary
        await self._generate_enrichment_summary(enriched_count, failed_count, len(products))
        
        return enriched_count > 0
    
    async def _enrich_product_details(self, product: Dict) -> Optional[Dict]:
        """Scrape detailed specs from product page"""
        
        product_url = product.get('evo_url')
        if not product_url or not product_url.startswith('https://'):
            return None
        
        try:
            response = self.session.get(product_url, timeout=15.0)
            
            if response.status_code != 200:
                return None
            
            soup = BeautifulSoup(response.text, 'html.parser')
            enriched_data = {}
            
            # Extract model year
            model_year = self._extract_model_year(soup, product['name'])
            if model_year:
                enriched_data['model_year'] = model_year
            
            # Extract board lengths/sizes
            board_lengths = self._extract_board_lengths(soup)
            if board_lengths:
                enriched_data['board_lengths'] = board_lengths
            
            # Extract technical specifications
            specs = self._extract_specifications(soup)
            enriched_data.update(specs)
            
            # Extract pricing details
            pricing = self._extract_pricing_details(soup, product.get('current_price'))
            enriched_data.update(pricing)
            
            # Extract description and features
            content = self._extract_content_details(soup)
            enriched_data.update(content)
            
            # Extract review information
            reviews = self._extract_review_details(soup)
            enriched_data.update(reviews)
            
            # Filter out None values
            return {k: v for k, v in enriched_data.items() if v is not None}
            
        except Exception as e:
            logger.error(f"Error enriching {product_url}: {e}")
            return None
    
    def _extract_model_year(self, soup: BeautifulSoup, product_name: str) -> Optional[str]:
        """Extract model year from page or product name"""
        
        # Try selectors first
        for selector in self.detail_selectors['model_year']:
            element = soup.select_one(selector)
            if element:
                year_text = element.get_text(strip=True)
                year_match = re.search(r'20\d{2}', year_text)
                if year_match:
                    return year_match.group()
        
        # Try extracting from product name
        year_match = re.search(r'20(2[4-9]|3[0-9])', product_name)
        if year_match:
            return year_match.group()
        
        return None
    
    def _extract_board_lengths(self, soup: BeautifulSoup) -> Optional[List[str]]:
        """Extract available board lengths"""
        
        lengths = []
        
        # Try size selectors
        for selector in self.detail_selectors['board_lengths']:
            elements = soup.select(selector)
            for element in elements:
                text = element.get_text(strip=True)
                # Look for measurements like "154cm", "157", "160W"
                length_matches = re.findall(r'(\d{3}[W]?)\s*(?:cm)?', text)
                for match in length_matches:
                    if match not in lengths and len(match) >= 3:
                        lengths.append(match)
        
        # Look in general text for common snowboard sizes
        page_text = soup.get_text()
        common_sizes = ['146', '149', '151', '154', '156', '157', '159', '160', '162', '163', '165', '168']
        for size in common_sizes:
            if f"{size}cm" in page_text or f" {size} " in page_text:
                if size not in lengths:
                    lengths.append(size)
        
        return lengths if lengths else None
    
    def _extract_specifications(self, soup: BeautifulSoup) -> Dict:
        """Extract technical specifications"""
        
        specs = {}
        
        # Look for specification tables or sections
        spec_sections = soup.select('.product-specifications, .specs-table, .product-specs, .specifications')
        
        for section in spec_sections:
            spec_text = section.get_text().lower()
            
            # Extract flex rating
            flex_match = re.search(r'flex[:\s]*([0-9]+(?:/10)?|soft|medium|stiff|very stiff)', spec_text)
            if flex_match and not specs.get('flex_rating'):
                specs['flex_rating'] = flex_match.group(1)
            
            # Extract camber profile
            camber_keywords = ['camber', 'rocker', 'hybrid', 'flat', 'reverse camber']
            for keyword in camber_keywords:
                if keyword in spec_text and not specs.get('camber_profile'):
                    # Look for the full camber description
                    camber_match = re.search(f'{keyword}[^.]*', spec_text)
                    if camber_match:
                        specs['camber_profile'] = camber_match.group().strip()
                    break
            
            # Extract shape
            shape_keywords = ['directional', 'twin', 'asymmetrical', 'tapered']
            for keyword in shape_keywords:
                if keyword in spec_text and not specs.get('shape'):
                    specs['shape'] = keyword.title()
                    break
            
            # Extract core material
            core_keywords = ['wood core', 'poplar', 'bamboo', 'foam core']
            for keyword in core_keywords:
                if keyword in spec_text and not specs.get('core_material'):
                    specs['core_material'] = keyword.title()
                    break
            
            # Extract base material
            base_keywords = ['sintered', 'extruded', 'ptex']
            for keyword in base_keywords:
                if keyword in spec_text and not specs.get('base_material'):
                    specs['base_material'] = keyword.title()
                    break
        
        return specs
    
    def _extract_pricing_details(self, soup: BeautifulSoup, current_price: Optional[float]) -> Dict:
        """Extract original and sale pricing"""
        
        pricing = {}
        
        # Look for original/MSRP price
        for selector in self.detail_selectors['price_original']:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text(strip=True)
                price_match = re.search(r'\$?([0-9,]+\.?\d*)', price_text.replace(',', ''))
                if price_match:
                    original_price = float(price_match.group(1))
                    if original_price > (current_price or 0):
                        pricing['original_price'] = original_price
                break
        
        # Look for sale price indicators
        sale_indicators = soup.select('.sale, .discount, .price-sale')
        if sale_indicators and current_price:
            pricing['sale_price'] = current_price
        
        return pricing
    
    def _extract_content_details(self, soup: BeautifulSoup) -> Dict:
        """Extract description and features"""
        
        content = {}
        
        # Extract description
        for selector in self.detail_selectors['description']:
            element = soup.select_one(selector)
            if element:
                description = element.get_text(strip=True)
                if len(description) > 50:  # Only meaningful descriptions
                    content['manufacturer_description'] = description[:500]  # Limit length
                break
        
        # Extract key features
        features = []
        for selector in self.detail_selectors['features']:
            elements = soup.select(selector)
            for element in elements:
                feature_text = element.get_text(strip=True)
                if feature_text and len(feature_text) > 5:
                    features.append(feature_text)
        
        if features:
            content['key_features'] = features[:10]  # Limit to top 10 features
        
        # Extract terrain suitability from description
        if content.get('manufacturer_description'):
            desc_lower = content['manufacturer_description'].lower()
            terrain_types = []
            terrain_keywords = {
                'park': ['park', 'jib', 'rail'],
                'pipe': ['pipe', 'halfpipe'],
                'groomed': ['groomed', 'piste', 'carving'],
                'powder': ['powder', 'deep snow', 'float'],
                'backcountry': ['backcountry', 'touring', 'splitboard'],
                'all-mountain': ['all mountain', 'versatile', 'anywhere']
            }
            
            for terrain, keywords in terrain_keywords.items():
                if any(keyword in desc_lower for keyword in keywords):
                    terrain_types.append(terrain)
            
            if terrain_types:
                content['terrain_suitability'] = terrain_types
        
        return content
    
    def _extract_review_details(self, soup: BeautifulSoup) -> Dict:
        """Extract review and rating information"""
        
        reviews = {}
        
        # Look for review counts
        review_count_selectors = [
            '.review-count', '.reviews-count', '[data-testid="review-count"]',
            '.rating-count', 'span:contains("review")'
        ]
        
        for selector in review_count_selectors:
            element = soup.select_one(selector)
            if element:
                count_text = element.get_text()
                count_match = re.search(r'(\d+)', count_text)
                if count_match:
                    reviews['review_count'] = int(count_match.group(1))
                break
        
        # Look for average ratings
        rating_selectors = [
            '.average-rating', '.rating-average', '[data-testid="rating"]',
            '.stars-rating', '.product-rating'
        ]
        
        for selector in rating_selectors:
            element = soup.select_one(selector)
            if element:
                # Try data attributes first
                rating = element.get('data-rating') or element.get('data-score')
                if rating:
                    try:
                        reviews['average_rating'] = float(rating)
                        break
                    except:
                        pass
                
                # Try text content
                rating_text = element.get_text()
                rating_match = re.search(r'([0-9]\.?[0-9]*)\s*(?:out of|/|\s+)?\s*[0-9]?', rating_text)
                if rating_match:
                    try:
                        reviews['average_rating'] = float(rating_match.group(1))
                        break
                    except:
                        pass
        
        return reviews
    
    async def _generate_enrichment_summary(self, enriched_count: int, failed_count: int, total_count: int):
        """Generate enrichment summary"""
        
        print(f"\n{Fore.GREEN}🎉 Detail Enrichment Complete!{Style.RESET_ALL}")
        print("=" * 70)
        
        print(f"📊 **Enrichment Summary:**")
        print(f"   Total products processed: {total_count}")
        print(f"   Successfully enriched: {enriched_count}")
        print(f"   Failed to enrich: {failed_count}")
        print(f"   Success rate: {(enriched_count/total_count)*100:.1f}%")
        
        # Run analysis to show new fill rates
        print(f"\n🔄 Running updated analysis...")
        await asyncio.sleep(1.0)

async def main():
    """Main entry point"""
    scraper = DetailEnrichmentScraper()
    
    try:
        result = await scraper.enrich_existing_products()
        
        if result:
            print(f"\n{Fore.GREEN}✅ Success! Products enriched with detailed specs.{Style.RESET_ALL}")
            print(f"\n💡 Next steps:")
            print(f"   1. Run analyze_results.py to see improved fill rates")
            print(f"   2. Review enriched product specifications")
            print(f"   3. Test agents with comprehensive product data")
        else:
            print(f"\n{Fore.RED}❌ Enrichment failed.{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())