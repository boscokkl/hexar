"""
Main standalone scraper for Evo.com snowboard products
Matrix-driven sampling with isolated architecture
"""

import asyncio
import time
import logging
import requests
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup
from tqdm import tqdm
from colorama import init, Fore, Style

# Initialize colorama for colored output
init()

# Local imports
from config import ScraperConfig, EvoUrls, SamplingMatrix
from models import ScrapedProduct
from database import ScraperDatabase
from matrix_manager import MatrixManager
from evo_selectors import EvoSelectors, EvoParser

# Setup logging
logging.basicConfig(
    level=logging.INFO if ScraperConfig.VERBOSE_LOGGING else logging.WARNING,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EvoScraper:
    """Standalone scraper for Evo.com snowboards"""
    
    def __init__(self):
        """Initialize scraper"""
        self.config = ScraperConfig()
        self.database = ScraperDatabase()
        self.matrix_manager = MatrixManager(target_total=ScraperConfig.TARGET_PRODUCTS_TOTAL)
        
        # Setup requests session
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': ScraperConfig.USER_AGENT,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Performance tracking
        self.stats = {
            'pages_scraped': 0,
            'products_found': 0,
            'products_added': 0,
            'products_rejected': 0,
            'requests_made': 0,
            'start_time': time.time()
        }
        
        print(f"{Fore.GREEN}🚀 EvoScraper initialized{Style.RESET_ALL}")
        print(f"   Target: {ScraperConfig.TARGET_PRODUCTS_TOTAL} products")
        print(f"   Matrix: {len(SamplingMatrix.get_all_categories())} categories")
    
    async def scrape_products(self) -> bool:
        """Main scraping function with matrix-driven sampling"""
        try:
            # Check database connection
            if not await self.database.ensure_table_exists():
                print(f"{Fore.RED}❌ Database table not accessible{Style.RESET_ALL}")
                return False
            
            # Load existing progress
            await self._load_existing_progress()
            
            print(f"\n{Fore.CYAN}📊 Starting Matrix-Driven Scraping{Style.RESET_ALL}")
            self.matrix_manager.print_progress_table()
            
            # Main scraping loop
            while not self.matrix_manager.is_complete():
                # Get next priority category
                next_category = self.matrix_manager.get_next_search_category()
                if not next_category:
                    print(f"{Fore.YELLOW}⚠️ No more categories to scrape{Style.RESET_ALL}")
                    break
                
                skill_level, riding_style = next_category
                print(f"\n{Fore.BLUE}🎯 Scraping: {skill_level} × {riding_style}{Style.RESET_ALL}")
                
                # Scrape category
                success = await self._scrape_category(skill_level, riding_style)
                if not success:
                    print(f"{Fore.YELLOW}⚠️ Failed to scrape {skill_level} × {riding_style}{Style.RESET_ALL}")
                
                # Rate limiting
                await asyncio.sleep(ScraperConfig.DELAY_SECONDS)
                
                # Progress update
                if self.stats['products_added'] % 5 == 0:
                    self._print_progress()
            
            # Final summary
            self._print_final_summary()
            return True
            
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}⏹️ Scraping interrupted by user{Style.RESET_ALL}")
            self._print_final_summary()
            return False
        except Exception as e:
            print(f"{Fore.RED}❌ Scraping failed: {e}{Style.RESET_ALL}")
            logger.error(f"Scraping error: {e}", exc_info=True)
            return False
    
    async def _load_existing_progress(self):
        """Load existing progress from database"""
        try:
            database_progress = self.database.get_matrix_progress()
            if database_progress:
                self.matrix_manager.load_existing_progress(database_progress)
                print(f"{Fore.GREEN}✅ Loaded existing progress{Style.RESET_ALL}")
            else:
                print(f"{Fore.BLUE}ℹ️ Starting fresh scraping session{Style.RESET_ALL}")
        except Exception as e:
            logger.warning(f"Could not load existing progress: {e}")
    
    async def _scrape_category(self, skill_level: str, riding_style: str, max_pages: int = 3) -> bool:
        """Scrape products from a specific category"""
        try:
            # Build URL for category
            base_url = EvoUrls.build_category_url(riding_style)
            
            products_found_in_category = 0
            
            # Scrape multiple pages if needed
            for page in range(1, max_pages + 1):
                if not self.matrix_manager.can_accept_product(skill_level, riding_style):
                    print(f"   Category complete, stopping at page {page}")
                    break
                
                page_url = f"{base_url}?page={page}" if page > 1 else base_url
                
                print(f"   📄 Scraping page {page}: {page_url}")
                
                # Fetch page
                page_products = await self._scrape_page(page_url, skill_level, riding_style)
                products_found_in_category += len(page_products)
                
                self.stats['pages_scraped'] += 1
                
                # If no products found, stop pagination
                if not page_products:
                    print(f"   No products found on page {page}, stopping pagination")
                    break
                
                # Rate limiting between pages
                await asyncio.sleep(ScraperConfig.DELAY_SECONDS * 0.5)
            
            print(f"   ✅ Found {products_found_in_category} products in {skill_level} × {riding_style}")
            return products_found_in_category > 0
            
        except Exception as e:
            logger.error(f"Error scraping category {skill_level} × {riding_style}: {e}")
            return False
    
    async def _scrape_page(self, url: str, skill_level: str, riding_style: str) -> List[ScrapedProduct]:
        """Scrape products from a single page"""
        try:
            # Make request
            response = self._make_request(url)
            if not response:
                return []
            
            self.stats['requests_made'] += 1
            
            # Parse HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find product containers
            product_elements = self._find_product_elements(soup)
            
            if not product_elements:
                logger.warning(f"No product elements found on page: {url}")
                return []
            
            print(f"     Found {len(product_elements)} product elements")
            
            # Extract products
            scraped_products = []
            for element in product_elements:
                try:
                    product = self._extract_product(element, skill_level, riding_style)
                    if product:
                        # Check if we can accept this product
                        if self.matrix_manager.can_accept_product(skill_level, riding_style):
                            # Check for duplicates
                            if not self.database.check_product_exists(product.product_id):
                                # Add to matrix and database
                                if self.matrix_manager.add_product(product):
                                    if self.database.insert_product(product):
                                        scraped_products.append(product)
                                        self.stats['products_added'] += 1
                                        print(f"     ✅ Added: {product.name}")
                                    else:
                                        print(f"     ❌ Database insert failed: {product.name}")
                                else:
                                    self.stats['products_rejected'] += 1
                                    print(f"     ➖ Matrix rejected: {product.name}")
                            else:
                                print(f"     🔄 Duplicate skipped: {product.name}")
                        else:
                            self.stats['products_rejected'] += 1
                            print(f"     ➖ Category full: {product.name}")
                    
                    self.stats['products_found'] += 1
                    
                except Exception as e:
                    logger.debug(f"Error extracting product: {e}")
                    continue
            
            return scraped_products
            
        except Exception as e:
            logger.error(f"Error scraping page {url}: {e}")
            return []
    
    def _make_request(self, url: str) -> Optional[requests.Response]:
        """Make HTTP request with error handling"""
        try:
            response = self.session.get(
                url,
                timeout=ScraperConfig.TIMEOUT_SECONDS
            )
            
            if response.status_code == 200:
                return response
            else:
                logger.warning(f"HTTP {response.status_code} for {url}")
                return None
                
        except Exception as e:
            logger.error(f"Request failed for {url}: {e}")
            return None
    
    def _find_product_elements(self, soup: BeautifulSoup) -> List:
        """Find product container elements"""
        for selector in EvoSelectors.PRODUCT_CONTAINERS:
            elements = soup.select(selector)
            if elements:
                logger.debug(f"Found {len(elements)} products with selector: {selector}")
                return elements
        
        logger.warning("No product elements found with any selector")
        return []
    
    def _extract_product(self, element, skill_level: str, riding_style: str) -> Optional[ScrapedProduct]:
        """Extract product data from HTML element"""
        try:
            # Extract basic info
            name = EvoParser.extract_text(element, EvoSelectors.NAME_SELECTORS)
            if not name or len(name) < 3:
                return None
            
            # Extract price
            price_text = EvoParser.extract_text(element, EvoSelectors.PRICE_SELECTORS)
            current_price = EvoParser.parse_price(price_text) if price_text else None
            
            # Extract URL
            url_path = EvoParser.extract_url(element, EvoSelectors.URL_SELECTORS)
            evo_url = EvoParser.ensure_absolute_url(url_path) if url_path else EvoUrls.BASE_URL
            
            # Extract image
            image_url = EvoParser.extract_image_url(element, EvoSelectors.IMAGE_SELECTORS)
            if image_url:
                image_url = EvoParser.ensure_absolute_url(image_url)
            
            # Extract brand
            brand = EvoParser.extract_brand_from_title(name)
            
            # Create product
            product = ScrapedProduct(
                name=name,
                brand=brand,
                evo_url=evo_url,
                image_urls=[image_url] if image_url else [],
                current_price=current_price,
                skill_level=skill_level,
                riding_style=riding_style,
                availability_status="in_stock"  # Assume in stock if listed
            )
            
            return product
            
        except Exception as e:
            logger.debug(f"Error extracting product: {e}")
            return None
    
    def _print_progress(self):
        """Print current progress"""
        elapsed = time.time() - self.stats['start_time']
        print(f"\n{Fore.CYAN}📈 Progress Update{Style.RESET_ALL}")
        print(f"   Products added: {self.stats['products_added']}")
        print(f"   Products found: {self.stats['products_found']}")
        print(f"   Pages scraped: {self.stats['pages_scraped']}")
        print(f"   Elapsed time: {elapsed/60:.1f} minutes")
        
        if self.stats['products_added'] > 0:
            rate = self.stats['products_added'] / (elapsed / 60)
            print(f"   Rate: {rate:.1f} products/minute")
    
    def _print_final_summary(self):
        """Print final scraping summary"""
        elapsed = time.time() - self.stats['start_time']
        
        print(f"\n{Fore.GREEN}🎉 Scraping Complete!{Style.RESET_ALL}")
        print("=" * 60)
        
        # Final matrix status
        self.matrix_manager.print_progress_table()
        
        print(f"\n{Fore.CYAN}📊 Final Statistics{Style.RESET_ALL}")
        print(f"   Products added: {self.stats['products_added']}")
        print(f"   Products found: {self.stats['products_found']}")
        print(f"   Products rejected: {self.stats['products_rejected']}")
        print(f"   Pages scraped: {self.stats['pages_scraped']}")
        print(f"   Requests made: {self.stats['requests_made']}")
        print(f"   Total time: {elapsed/60:.1f} minutes")
        
        if self.stats['products_added'] > 0:
            rate = self.stats['products_added'] / (elapsed / 60)
            print(f"   Average rate: {rate:.1f} products/minute")
        
        # Database stats
        try:
            db_stats = self.database.get_database_stats()
            print(f"\n{Fore.BLUE}🗄️ Database Status{Style.RESET_ALL}")
            print(f"   Total products in DB: {db_stats.get('total_products', 0)}")
            print(f"   Last scraped: {db_stats.get('last_scraped', 'Unknown')}")
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")

async def main():
    """Main entry point"""
    print(f"{Fore.CYAN}🔧 Standalone Evo.com Scraper{Style.RESET_ALL}")
    print(f"   Target: {ScraperConfig.TARGET_PRODUCTS_TOTAL} products")
    print(f"   Matrix validation: {ScraperConfig.MATRIX_VALIDATION}")
    
    scraper = EvoScraper()
    success = await scraper.scrape_products()
    
    if success:
        print(f"\n{Fore.GREEN}✅ Scraping completed successfully!{Style.RESET_ALL}")
    else:
        print(f"\n{Fore.RED}❌ Scraping completed with errors{Style.RESET_ALL}")
    
    return success

if __name__ == "__main__":
    # Run the scraper
    try:
        result = asyncio.run(main())
        exit_code = 0 if result else 1
        exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Fore.YELLOW}👋 Goodbye!{Style.RESET_ALL}")
        exit(1)