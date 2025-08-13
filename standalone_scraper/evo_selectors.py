"""
CSS selectors and parsing logic for Evo.com
Isolated scraping configuration
"""

import re
from typing import List, Optional, Dict, Any
from bs4 import BeautifulSoup, Tag
import logging

logger = logging.getLogger(__name__)

class EvoSelectors:
    """CSS selectors and parsing patterns for Evo.com"""
    
    # Product listing page selectors
    PRODUCT_CONTAINERS = [
        '.product-thumb-details',      # Primary Evo.com product container
        '.product-thumb',              # Fallback container
        '.js-product-thumb',           # JavaScript-enhanced container
        '.larger-image-product-thumb', # Larger format products
        '.product-tile',               # Alternative layout
        '.product-item',               # Generic fallback
        '[data-productid]',            # Products with data attributes
        '.product-card',               # Card layout
        '.tile'                        # Generic tile
    ]
    
    # Product name selectors (in order of preference)
    NAME_SELECTORS = [
        '.product-thumb-title',        # Primary Evo product title
        '.product-title',              
        '.product-name',
        '.title',
        'h3', 'h4', 'h2',
        '[data-testid*="title"]',
        '.name',
        'a[title]'                     # Link title attribute
    ]
    
    # Price selectors (in order of preference)  
    PRICE_SELECTORS = [
        '.product-thumb-price .discount',     # Sale price in discount span
        '.product-thumb-price:not(.slash)',  # Regular price (not crossed out)
        '.product-thumb-price',              # Any price element
        '.price',
        '.product-price',
        '.cost',
        '[data-testid*="price"]',
        '.price-current',
        '.sale-price',
        '.regular-price',
        '.amount'
    ]
    
    # Product URL selectors
    URL_SELECTORS = [
        '.product-thumb-link',
        '.js-product-thumb-details-link',
        'a[href*="/snowboards/"]',
        'a[href*="/shop/"]',
        'a[href]'
    ]
    
    # Image selectors
    IMAGE_SELECTORS = [
        '.product-thumb-image',
        '.js-product-thumb-image',
        'img[src]',
        'img[data-src]',
        'img[data-lazy]',
        'img[data-original]'
    ]
    
    # Product detail page selectors
    DETAIL_NAME_SELECTORS = [
        '.product-title',
        '.pdp-product-title',
        'h1.title',
        'h1',
        '.product-name'
    ]
    
    DETAIL_PRICE_SELECTORS = [
        '.price-current',
        '.product-price',
        '.price',
        '.cost',
        '.price-display'
    ]
    
    DETAIL_DESCRIPTION_SELECTORS = [
        '.product-description',
        '.pdp-description',
        '.description',
        '.product-details',
        '.product-content'
    ]
    
    DETAIL_SPECS_SELECTORS = [
        '.product-specs',
        '.specifications',
        '.product-details-table',
        '.specs-table',
        'table.specs',
        '.product-attributes'
    ]
    
    DETAIL_FEATURES_SELECTORS = [
        '.product-features',
        '.key-features',
        '.features-list',
        '.bullet-points',
        '.product-highlights'
    ]

class EvoParser:
    """Parser for extracting product data from Evo.com HTML"""
    
    @staticmethod
    def extract_text(element: Tag, selectors: List[str]) -> Optional[str]:
        """Extract text from element using selector priority list"""
        if not element:
            return None
        
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found:
                    text = found.get_text(strip=True)
                    if text and len(text) > 0:
                        return text
            except Exception as e:
                logger.debug(f"Selector '{selector}' failed: {e}")
                continue
        
        return None
    
    @staticmethod
    def extract_url(element: Tag, selectors: List[str]) -> Optional[str]:
        """Extract URL from element using selector priority list"""
        if not element:
            return None
        
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found and found.get('href'):
                    return found.get('href')
            except Exception as e:
                logger.debug(f"URL selector '{selector}' failed: {e}")
                continue
        
        return None
    
    @staticmethod
    def extract_image_url(element: Tag, selectors: List[str] = None) -> Optional[str]:
        """Extract image URL from element"""
        if not element:
            return None
        
        if selectors is None:
            selectors = EvoSelectors.IMAGE_SELECTORS
        
        for selector in selectors:
            try:
                found = element.select_one(selector)
                if found:
                    # Try different image attributes
                    for attr in ['src', 'data-src', 'data-lazy', 'data-original']:
                        url = found.get(attr)
                        if url and url.startswith(('http', '/')):
                            return url
            except Exception as e:
                logger.debug(f"Image selector '{selector}' failed: {e}")
                continue
        
        return None
    
    @staticmethod
    def parse_price(price_text: str) -> Optional[float]:
        """Parse price from text string"""
        if not price_text:
            return None
        
        try:
            # Remove currency symbols and extra text
            cleaned = re.sub(r'[^\d.,]', '', price_text)
            # Remove commas
            cleaned = cleaned.replace(',', '')
            
            # Extract numeric price
            price_match = re.search(r'\d+\.?\d*', cleaned)
            if price_match:
                return float(price_match.group())
        except Exception as e:
            logger.debug(f"Price parsing failed for '{price_text}': {e}")
        
        return None
    
    @staticmethod
    def ensure_absolute_url(url: str, base_url: str = "https://www.evo.com") -> str:
        """Ensure URL is absolute"""
        if not url:
            return base_url
        
        if url.startswith('http'):
            return url
        
        if url.startswith('//'):
            return f"https:{url}"
        
        if not url.startswith('/'):
            url = f"/{url}"
        
        return f"{base_url}{url}"
    
    @staticmethod
    def extract_brand_from_title(title: str) -> Optional[str]:
        """Extract brand name from product title"""
        if not title:
            return None
        
        # Common snowboard brands
        brands = [
            'Burton', 'Lib Tech', 'Jones', 'Capita', 'Never Summer',
            'Salomon', 'K2', 'Rossignol', 'Arbor', 'Ride', 'GNU',
            'Nitro', 'Yes', 'Rome', 'Flow', 'Bataleon', 'Atomic',
            'Head', 'Volkl', 'Slash', 'Weston', 'Prior', 'Korua',
            'Bataleon', 'CAPiTA', 'Dinosaurs Will Die', 'Endeavor'
        ]
        
        title_words = title.split()
        for word in title_words:
            for brand in brands:
                if word.lower() == brand.lower():
                    return brand
        
        # Return first word as potential brand
        return title_words[0] if title_words else None
    
    @staticmethod
    def classify_skill_level(title: str, description: str = "") -> str:
        """Classify skill level from product title and description"""
        text = f"{title} {description}".lower()
        
        # Expert indicators
        if any(keyword in text for keyword in ['expert', 'pro', 'advanced', 'aggressive', 'stiff', 'competition']):
            return 'expert'
        
        # Advanced indicators
        if any(keyword in text for keyword in ['advanced', 'performance', 'high-end', 'precision', 'responsive']):
            return 'advanced'
        
        # Beginner indicators
        if any(keyword in text for keyword in ['beginner', 'learning', 'first', 'starter', 'easy', 'forgiving', 'soft']):
            return 'beginner'
        
        # Default to intermediate
        return 'intermediate'
    
    @staticmethod
    def classify_riding_style(title: str, description: str = "", url: str = "") -> str:
        """Classify riding style from product information"""
        text = f"{title} {description} {url}".lower()
        
        # Freestyle indicators
        if any(keyword in text for keyword in ['freestyle', 'park', 'pipe', 'jib', 'twin', 'street']):
            return 'freestyle'
        
        # Freeride indicators  
        if any(keyword in text for keyword in ['freeride', 'backcountry', 'mountain', 'big mountain', 'charging']):
            return 'freeride'
        
        # Powder indicators
        if any(keyword in text for keyword in ['powder', 'deep', 'float', 'surf', 'tapered']):
            return 'powder'
        
        # Carving indicators
        if any(keyword in text for keyword in ['carving', 'carve', 'groomed', 'piste', 'racing']):
            return 'carving'
        
        # Default to all-mountain
        return 'all-mountain'
    
    @staticmethod
    def extract_board_lengths(text: str) -> List[str]:
        """Extract board lengths from text"""
        if not text:
            return []
        
        # Look for patterns like "154, 157, 160, 163" or "154cm"
        length_patterns = [
            r'(\d{3})\s*cm',           # "154cm"
            r'(\d{3})(?=\s*[,\s])',    # "154" followed by comma or space
            r'(\d{3})(?=\s*$)',        # "154" at end of string
        ]
        
        lengths = set()
        for pattern in length_patterns:
            matches = re.findall(pattern, text)
            for match in matches:
                length = int(match)
                if 140 <= length <= 180:  # Valid snowboard length range
                    lengths.add(str(length))
        
        return sorted(list(lengths))
    
    @staticmethod
    def extract_flex_rating(text: str) -> Optional[str]:
        """Extract flex rating from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if any(keyword in text_lower for keyword in ['soft', 'forgiving', 'playful']):
            return 'soft'
        elif any(keyword in text_lower for keyword in ['stiff', 'aggressive', 'responsive']):
            return 'stiff'
        elif any(keyword in text_lower for keyword in ['medium', 'moderate', 'balanced']):
            return 'medium'
        
        return None
    
    @staticmethod
    def extract_camber_profile(text: str) -> Optional[str]:
        """Extract camber profile from text"""
        if not text:
            return None
        
        text_lower = text.lower()
        
        if 'rocker' in text_lower:
            return 'rocker'
        elif 'camber' in text_lower:
            if 'hybrid' in text_lower or 'combo' in text_lower:
                return 'hybrid'
            return 'camber'
        elif any(keyword in text_lower for keyword in ['hybrid', 'combo', 'mixed']):
            return 'hybrid'
        
        return None

if __name__ == "__main__":
    # Test parsing functions
    test_cases = [
        {
            'title': 'Burton Custom Snowboard 2024',
            'price': '$599.95',
            'description': 'All-mountain performance board for intermediate to advanced riders'
        },
        {
            'title': 'Lib Tech T.Rice Pro HP Snowboard',
            'price': '749.99',
            'description': 'Aggressive freeride board with hybrid camber profile'
        }
    ]
    
    for case in test_cases:
        print(f"\nTesting: {case['title']}")
        print(f"Brand: {EvoParser.extract_brand_from_title(case['title'])}")
        print(f"Price: {EvoParser.parse_price(case['price'])}")
        print(f"Skill Level: {EvoParser.classify_skill_level(case['title'], case['description'])}")
        print(f"Riding Style: {EvoParser.classify_riding_style(case['title'], case['description'])}")