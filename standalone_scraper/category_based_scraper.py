#!/usr/bin/env python3
"""
Category-based scraper: Scrape from specific Evo.com style category pages
This will give us real style diversity instead of guessing from names
"""

import asyncio
import time
import logging
import requests
from typing import List, Dict
from bs4 import BeautifulSoup
from colorama import init, Fore, Style

# Initialize colorama
init()

from config import ScraperConfig
from models import ScrapedProduct
from database import ScraperDatabase
from evo_selectors import EvoSelectors, EvoParser

# Setup logging
logging.basicConfig(level=logging.WARNING)
logger = logging.getLogger(__name__)

class CategoryBasedScraper:
    """Scraper that collects products from specific Evo.com style categories"""
    
    def __init__(self):
        self.db = ScraperDatabase()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ScraperConfig.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        # Evo.com category URLs for different riding styles
        self.category_urls = {
            'all-mountain': 'https://www.evo.com/shop/snowboard/snowboards/all-mountain',
            'freestyle': 'https://www.evo.com/shop/snowboard/snowboards/freestyle',  
            'freeride': 'https://www.evo.com/shop/snowboard/snowboards/freeride',
            'powder': 'https://www.evo.com/shop/snowboard/snowboards/powder',
            # Note: Evo might not have separate carving category, will check all-mountain for those
        }
        
        # Target products per style (total ~50)
        self.style_targets = {
            'all-mountain': 15,  # Most popular
            'freestyle': 12,     # Popular
            'freeride': 12,      # Popular  
            'powder': 8,         # Niche
            'carving': 3         # Very niche - will manually classify from all-mountain
        }
        
        # Skill level distribution within each style
        self.skill_distribution = ['beginner', 'intermediate', 'advanced', 'expert']
    
    async def scrape_by_categories(self) -> bool:
        """Main scraping function organized by riding style categories"""
        
        print(f"{Fore.GREEN}🚀 Category-Based Evo.com Scraper{Style.RESET_ALL}")
        print(f"   Strategy: Scrape from actual style category pages")
        print(f"   Target: {sum(self.style_targets.values())} products total")
        
        # Check database
        if not await self.db.ensure_table_exists():
            print(f"{Fore.RED}❌ Database not accessible{Style.RESET_ALL}")
            return False
        
        # Clear for fresh start
        self.db.clear_all_scraped_products()
        print(f"{Fore.BLUE}🗑️ Cleared existing products{Style.RESET_ALL}")
        
        total_scraped = 0
        
        # Scrape each style category
        for riding_style, target_count in self.style_targets.items():
            if riding_style == 'carving':
                continue  # Handle carving separately
                
            print(f"\n{Fore.CYAN}🎯 Scraping {riding_style} style ({target_count} products){Style.RESET_ALL}")
            
            category_products = await self._scrape_style_category(riding_style, target_count)
            total_scraped += len(category_products)
            
            print(f"   ✅ Collected {len(category_products)} {riding_style} products")
            
            # Rate limiting between categories
            await asyncio.sleep(2.0)
        
        # Handle carving boards (classify from all-mountain)
        print(f"\n{Fore.CYAN}🎯 Identifying carving boards from all-mountain{Style.RESET_ALL}")
        carving_count = await self._find_carving_boards()
        total_scraped += carving_count
        print(f"   ✅ Identified {carving_count} carving boards")
        
        # Generate final summary
        await self._generate_summary(total_scraped)
        
        return total_scraped > 0
    
    async def _scrape_style_category(self, riding_style: str, target_count: int) -> List[ScrapedProduct]:
        """Scrape products from a specific style category"""
        
        if riding_style not in self.category_urls:
            print(f"   ⚠️ No URL found for {riding_style}")
            return []
        
        products_collected = []
        page = 1
        max_pages = 3
        skill_counter = 0  # Rotate through skill levels
        
        while len(products_collected) < target_count and page <= max_pages:
            print(f"   📄 Page {page}: ", end="", flush=True)
            
            try:
                # Get page
                page_url = f"{self.category_urls[riding_style]}?page={page}" if page > 1 else self.category_urls[riding_style]
                response = self.session.get(page_url, timeout=15.0)
                
                if response.status_code != 200:
                    print(f"HTTP {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                product_elements = soup.select('.product-thumb-details')
                
                if not product_elements:
                    print("No products found")
                    break
                
                # Extract products for this style
                page_count = 0
                for element in product_elements:
                    if len(products_collected) >= target_count:
                        break
                    
                    try:
                        # Assign skill level in rotation for diversity
                        skill_level = self.skill_distribution[skill_counter % len(self.skill_distribution)]
                        skill_counter += 1
                        
                        product = self._extract_product_for_style(element, riding_style, skill_level)
                        if product and self.db.insert_product(product):
                            products_collected.append(product)
                            page_count += 1
                            
                    except Exception as e:
                        logger.debug(f"Error extracting product: {e}")
                        continue
                
                print(f"Found {page_count} products")
                
                if page_count == 0:
                    break
                
                page += 1
                await asyncio.sleep(ScraperConfig.DELAY_SECONDS)
                
            except Exception as e:
                print(f"Error: {e}")
                break
        
        return products_collected
    
    def _extract_product_for_style(self, element, riding_style: str, skill_level: str) -> ScrapedProduct:
        """Extract product and assign specific style + skill level"""
        
        # Extract basic info
        name = EvoParser.extract_text(element, EvoSelectors.NAME_SELECTORS)
        if not name or len(name) < 3:
            return None
        
        price_text = EvoParser.extract_text(element, EvoSelectors.PRICE_SELECTORS)
        current_price = EvoParser.parse_price(price_text) if price_text else None
        
        url_path = EvoParser.extract_url(element, EvoSelectors.URL_SELECTORS)
        evo_url = EvoParser.ensure_absolute_url(url_path) if url_path else 'https://www.evo.com'
        
        image_url = EvoParser.extract_image_url(element, EvoSelectors.IMAGE_SELECTORS)
        if image_url:
            image_url = EvoParser.ensure_absolute_url(image_url)
        
        brand = EvoParser.extract_brand_from_title(name)
        
        return ScrapedProduct(
            name=name,
            brand=brand,
            evo_url=evo_url,
            image_urls=[image_url] if image_url else [],
            current_price=current_price,
            skill_level=skill_level,
            riding_style=riding_style,  # Direct assignment from category
            availability_status="in_stock"
        )
    
    async def _find_carving_boards(self) -> int:
        """Find carving boards from all-mountain category by analyzing names"""
        
        carving_keywords = [
            'carving', 'carve', 'racing', 'alpine', 'gs', 'slalom',
            'eurocarve', 'piste', 'groomed', 'hardpack'
        ]
        
        # Get some all-mountain products and look for carving indicators
        try:
            url = self.category_urls['all-mountain']
            response = self.session.get(url, timeout=15.0)
            soup = BeautifulSoup(response.text, 'html.parser')
            product_elements = soup.select('.product-thumb-details')
            
            carving_count = 0
            target_carving = self.style_targets['carving']
            
            for element in product_elements:
                if carving_count >= target_carving:
                    break
                
                try:
                    name = EvoParser.extract_text(element, EvoSelectors.NAME_SELECTORS)
                    if not name:
                        continue
                    
                    name_lower = name.lower()
                    
                    # Check for carving keywords or board characteristics
                    is_carving = any(keyword in name_lower for keyword in carving_keywords)
                    
                    # Additional heuristics for carving boards
                    if not is_carving:
                        # Look for directional/stiff characteristics that suggest carving
                        if any(word in name_lower for word in ['directional', 'stiff', 'responsive']):
                            is_carving = True
                    
                    if is_carving:
                        # Extract as carving board
                        price_text = EvoParser.extract_text(element, EvoSelectors.PRICE_SELECTORS)
                        current_price = EvoParser.parse_price(price_text) if price_text else None
                        
                        url_path = EvoParser.extract_url(element, EvoSelectors.URL_SELECTORS)
                        evo_url = EvoParser.ensure_absolute_url(url_path) if url_path else 'https://www.evo.com'
                        
                        image_url = EvoParser.extract_image_url(element, EvoSelectors.IMAGE_SELECTORS)
                        if image_url:
                            image_url = EvoParser.ensure_absolute_url(image_url)
                        
                        brand = EvoParser.extract_brand_from_title(name)
                        
                        # Assign skill level (carving boards are usually intermediate+)
                        skill_level = 'advanced' if carving_count % 2 == 0 else 'intermediate'
                        
                        product = ScrapedProduct(
                            name=name,
                            brand=brand,
                            evo_url=evo_url,
                            image_urls=[image_url] if image_url else [],
                            current_price=current_price,
                            skill_level=skill_level,
                            riding_style='carving',
                            availability_status="in_stock"
                        )
                        
                        if self.db.insert_product(product):
                            carving_count += 1
                            
                except Exception as e:
                    logger.debug(f"Error extracting carving product: {e}")
                    continue
            
            return carving_count
            
        except Exception as e:
            print(f"   Error finding carving boards: {e}")
            return 0
    
    async def _generate_summary(self, total_scraped: int):
        """Generate detailed summary with style breakdown"""
        
        print(f"\n{Fore.GREEN}🎉 Category-Based Scraping Complete!{Style.RESET_ALL}")
        print("=" * 70)
        
        # Get database statistics
        try:
            stats = self.db.get_database_stats()
            
            print(f"📊 **Summary:**")
            print(f"   Total products scraped: {total_scraped}")
            print(f"   Database total: {stats.get('total_products', 0)}")
            
            print(f"\n🎨 **Riding Style Breakdown:**")
            for style, counts in stats.get('riding_style_totals', {}).items():
                target = self.style_targets.get(style, 0)
                print(f"   {style:12s}: {counts:2d}/{target:2d} products")
            
            print(f"\n📈 **Skill Level Breakdown:**")
            for skill, counts in stats.get('skill_level_totals', {}).items():
                print(f"   {skill:12s}: {counts:2d} products")
            
            print(f"\n🏷️ **Sample Products by Style:**")
            # Show examples from each style
            try:
                for style in ['all-mountain', 'freestyle', 'freeride', 'powder', 'carving']:
                    sample_result = self.db.client.table("scraped_snowboard_products")\
                        .select("name, skill_level, current_price")\
                        .eq("riding_style", style)\
                        .limit(2).execute()
                    
                    if sample_result.data:
                        print(f"\n   {style.title()} Examples:")
                        for product in sample_result.data:
                            name = product['name'][:35] + "..." if len(product['name']) > 35 else product['name']
                            print(f"     {product['skill_level']:12s} | ${product['current_price'] or 'N/A':>6s} | {name}")
                            
            except Exception as e:
                logger.error(f"Error getting sample products: {e}")
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")

async def main():
    """Main entry point"""
    scraper = CategoryBasedScraper()
    
    try:
        result = await scraper.scrape_by_categories()
        
        if result:
            print(f"\n{Fore.GREEN}✅ Success! Diverse product styles saved to database.{Style.RESET_ALL}")
            print(f"\n💡 Next steps:")
            print(f"   1. Review database: scraped_snowboard_products table")
            print(f"   2. Verify style diversity with analysis script")
            print(f"   3. Test agents with diverse product data")
        else:
            print(f"\n{Fore.RED}❌ Scraping failed.{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())