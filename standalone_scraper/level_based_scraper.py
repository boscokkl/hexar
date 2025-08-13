#!/usr/bin/env python3
"""
Level-based scraper: Collect products by skill level, then classify by style
Strategy: 4 levels × ~12-13 products each = 50 total
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

class LevelBasedScraper:
    """Scraper that collects products by skill level first"""
    
    def __init__(self):
        self.db = ScraperDatabase()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ScraperConfig.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Connection': 'keep-alive',
        })
        
        # Target distribution by skill level
        self.level_targets = {
            'beginner': 12,
            'intermediate': 13, 
            'advanced': 13,
            'expert': 12
        }
        
        # Style classification patterns for automatic assignment
        self.style_patterns = {
            'freestyle': ['freestyle', 'park', 'pipe', 'jib', 'twin', 'street', 'rail'],
            'freeride': ['freeride', 'backcountry', 'mountain', 'big mountain', 'charging', 'deep'],
            'powder': ['powder', 'float', 'surf', 'tapered', 'deep snow'],
            'carving': ['carving', 'carve', 'groomed', 'piste', 'racing', 'alpine'],
            'all-mountain': []  # Default catch-all
        }
        
        # Base URL for all-mountain (has most products)
        self.base_url = 'https://www.evo.com/shop/snowboard/snowboards/all-mountain'
    
    async def scrape_by_levels(self) -> bool:
        """Main scraping function organized by skill levels"""
        
        print(f"{Fore.GREEN}🚀 Level-Based Evo.com Scraper{Style.RESET_ALL}")
        print(f"   Strategy: Collect by skill level, classify by style")
        print(f"   Target: {sum(self.level_targets.values())} products total")
        
        # Check database
        if not await self.db.ensure_table_exists():
            print(f"{Fore.RED}❌ Database not accessible{Style.RESET_ALL}")
            return False
        
        # Clear for fresh start
        self.db.clear_all_scraped_products()
        print(f"{Fore.BLUE}🗑️ Cleared existing products{Style.RESET_ALL}")
        
        total_scraped = 0
        
        # Scrape for each skill level
        for skill_level, target_count in self.level_targets.items():
            print(f"\n{Fore.CYAN}🎯 Scraping {skill_level} level ({target_count} products){Style.RESET_ALL}")
            
            level_products = await self._scrape_skill_level(skill_level, target_count)
            total_scraped += len(level_products)
            
            print(f"   ✅ Collected {len(level_products)} {skill_level} products")
            
            # Rate limiting between levels
            await asyncio.sleep(1.0)
        
        # Generate final summary
        await self._generate_summary(total_scraped)
        
        return total_scraped > 0
    
    async def _scrape_skill_level(self, skill_level: str, target_count: int) -> List[ScrapedProduct]:
        """Scrape products for a specific skill level"""
        
        products_collected = []
        page = 1
        max_pages = 5
        
        while len(products_collected) < target_count and page <= max_pages:
            print(f"   📄 Page {page}: ", end="", flush=True)
            
            try:
                # Get page
                page_url = f"{self.base_url}?page={page}" if page > 1 else self.base_url
                response = self.session.get(page_url, timeout=15.0)
                
                if response.status_code != 200:
                    print(f"HTTP {response.status_code}")
                    break
                
                soup = BeautifulSoup(response.text, 'html.parser')
                product_elements = soup.select('.product-thumb-details')
                
                if not product_elements:
                    print("No products found")
                    break
                
                # Extract products for this skill level
                page_count = 0
                for element in product_elements:
                    if len(products_collected) >= target_count:
                        break
                    
                    try:
                        product = self._extract_product_for_level(element, skill_level)
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
    
    def _extract_product_for_level(self, element, skill_level: str) -> ScrapedProduct:
        """Extract product and assign skill level + auto-classify style"""
        
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
        
        # Auto-classify riding style based on name and description
        riding_style = self._classify_riding_style(name.lower())
        
        return ScrapedProduct(
            name=name,
            brand=brand,
            evo_url=evo_url,
            image_urls=[image_url] if image_url else [],
            current_price=current_price,
            skill_level=skill_level,
            riding_style=riding_style,
            availability_status="in_stock"
        )
    
    def _classify_riding_style(self, name_lower: str) -> str:
        """Auto-classify riding style based on product name"""
        
        # Check each style pattern
        for style, keywords in self.style_patterns.items():
            if style == 'all-mountain':  # Skip default
                continue
            
            if any(keyword in name_lower for keyword in keywords):
                return style
        
        # Default to all-mountain
        return 'all-mountain'
    
    async def _generate_summary(self, total_scraped: int):
        """Generate detailed summary of scraped products"""
        
        print(f"\n{Fore.GREEN}🎉 Scraping Complete!{Style.RESET_ALL}")
        print("=" * 70)
        
        # Get database statistics
        try:
            stats = self.db.get_database_stats()
            
            print(f"📊 **Summary:**")
            print(f"   Total products scraped: {total_scraped}")
            print(f"   Database total: {stats.get('total_products', 0)}")
            
            print(f"\n📈 **Skill Level Breakdown:**")
            for skill, counts in stats.get('skill_level_totals', {}).items():
                target = self.level_targets.get(skill, 0)
                print(f"   {skill:12s}: {counts:2d}/{target:2d} products")
            
            print(f"\n🎨 **Riding Style Breakdown:**")
            for style, counts in stats.get('riding_style_totals', {}).items():
                print(f"   {style:12s}: {counts:2d} products")
            
            print(f"\n🏷️ **Sample Products:**")
            # Show some examples
            try:
                sample_result = self.db.client.table("scraped_snowboard_products")\
                    .select("name, skill_level, riding_style, current_price")\
                    .limit(5).execute()
                
                for product in sample_result.data:
                    name = product['name'][:40] + "..." if len(product['name']) > 40 else product['name']
                    print(f"   {product['skill_level']:12s} × {product['riding_style']:12s} | ${product['current_price'] or 'N/A':>6s} | {name}")
                    
            except Exception as e:
                logger.error(f"Error getting sample products: {e}")
            
        except Exception as e:
            print(f"❌ Error generating summary: {e}")

async def main():
    """Main entry point"""
    scraper = LevelBasedScraper()
    
    try:
        result = await scraper.scrape_by_levels()
        
        if result:
            print(f"\n{Fore.GREEN}✅ Success! Products saved to database.{Style.RESET_ALL}")
            print(f"\n💡 Next steps:")
            print(f"   1. Review database: scraped_snowboard_products table")
            print(f"   2. Test agents with real product data")
            print(f"   3. Analyze column fill rates")
        else:
            print(f"\n{Fore.RED}❌ Scraping failed.{Style.RESET_ALL}")
            
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Interrupted by user{Style.RESET_ALL}")
    except Exception as e:
        print(f"\n{Fore.RED}❌ Error: {e}{Style.RESET_ALL}")

if __name__ == "__main__":
    asyncio.run(main())