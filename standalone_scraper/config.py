"""
Configuration for Standalone Evo.com Scraper
Isolated from main hexar-backend configuration
"""

import os
from typing import Dict, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class ScraperConfig:
    """Standalone scraper configuration"""
    
    # Database Configuration
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
    
    # Scraper Configuration
    USER_AGENT = os.getenv(
        "SCRAPER_USER_AGENT", 
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
    DELAY_SECONDS = float(os.getenv("SCRAPER_DELAY_SECONDS", "2.0"))
    TIMEOUT_SECONDS = float(os.getenv("SCRAPER_TIMEOUT_SECONDS", "15.0"))
    MAX_RETRIES = int(os.getenv("SCRAPER_MAX_RETRIES", "3"))
    
    # Target Configuration
    TARGET_PRODUCTS_TOTAL = int(os.getenv("TARGET_PRODUCTS_TOTAL", "50"))
    MATRIX_VALIDATION = os.getenv("TARGET_MATRIX_VALIDATION", "true").lower() == "true"
    
    # Debug Configuration
    DEBUG_MODE = os.getenv("DEBUG_MODE", "false").lower() == "true"
    VERBOSE_LOGGING = os.getenv("VERBOSE_LOGGING", "true").lower() == "true"
    SAVE_HTML_FILES = os.getenv("SAVE_HTML_FILES", "false").lower() == "true"

class SamplingMatrix:
    """Product sampling matrix for balanced dataset"""
    
    # Skill levels in order of progression
    SKILL_LEVELS = ["beginner", "intermediate", "advanced", "expert"]
    
    # Riding styles with Evo.com URL patterns
    RIDING_STYLES = {
        "all-mountain": "/shop/snowboard/snowboards/all-mountain",
        "freeride": "/shop/snowboard/snowboards/freeride", 
        "freestyle": "/shop/snowboard/snowboards/freestyle",
        "powder": "/shop/snowboard/snowboards/powder",
        "carving": "/shop/snowboard/snowboards/carving"
    }
    
    # Target distribution matrix (skill_level -> riding_style -> count)
    SAMPLING_MATRIX: Dict[str, Dict[str, int]] = {
        "beginner": {
            "all-mountain": 3,
            "freeride": 2, 
            "freestyle": 3,
            "powder": 1,
            "carving": 1
        },
        "intermediate": {
            "all-mountain": 4,
            "freeride": 3,
            "freestyle": 4, 
            "powder": 2,
            "carving": 2
        },
        "advanced": {
            "all-mountain": 4,
            "freeride": 4,
            "freestyle": 4,
            "powder": 3,
            "carving": 2
        },
        "expert": {
            "all-mountain": 2,
            "freeride": 2,
            "freestyle": 2,
            "powder": 1,
            "carving": 1
        }
    }
    
    @classmethod
    def get_total_target(cls) -> int:
        """Calculate total products from matrix"""
        total = 0
        for skill_targets in cls.SAMPLING_MATRIX.values():
            total += sum(skill_targets.values())
        return total
    
    @classmethod
    def get_category_targets(cls, skill_level: str, riding_style: str) -> int:
        """Get target count for specific category"""
        return cls.SAMPLING_MATRIX.get(skill_level, {}).get(riding_style, 0)
    
    @classmethod
    def get_all_categories(cls) -> List[tuple]:
        """Get all (skill_level, riding_style) combinations with targets > 0"""
        categories = []
        for skill_level, style_targets in cls.SAMPLING_MATRIX.items():
            for riding_style, target_count in style_targets.items():
                if target_count > 0:
                    categories.append((skill_level, riding_style, target_count))
        return categories

class EvoUrls:
    """Evo.com URL configuration"""
    
    BASE_URL = "https://www.evo.com"
    
    # Main snowboard categories
    SNOWBOARDS_BASE = "/shop/snowboard/snowboards"
    
    # Category-specific URLs
    CATEGORY_URLS = {
        "all-mountain": f"{SNOWBOARDS_BASE}/all-mountain",
        "freeride": f"{SNOWBOARDS_BASE}/freeride", 
        "freestyle": f"{SNOWBOARDS_BASE}/freestyle",
        "powder": f"{SNOWBOARDS_BASE}/powder",
        "carving": f"{SNOWBOARDS_BASE}/carving"
    }
    
    # Filter parameters (if available)
    SKILL_LEVEL_FILTERS = {
        "beginner": "skill_level=beginner",
        "intermediate": "skill_level=intermediate", 
        "advanced": "skill_level=advanced",
        "expert": "skill_level=expert"
    }
    
    @classmethod
    def build_category_url(cls, riding_style: str, page: int = 1) -> str:
        """Build URL for specific category and page"""
        base_url = cls.CATEGORY_URLS.get(riding_style, cls.SNOWBOARDS_BASE)
        if page > 1:
            return f"{cls.BASE_URL}{base_url}?page={page}"
        return f"{cls.BASE_URL}{base_url}"
    
    @classmethod
    def build_product_url(cls, product_path: str) -> str:
        """Build absolute URL for product page"""
        if product_path.startswith("http"):
            return product_path
        if not product_path.startswith("/"):
            product_path = "/" + product_path
        return f"{cls.BASE_URL}{product_path}"

# Validation
if __name__ == "__main__":
    print(f"Sampling Matrix Total: {SamplingMatrix.get_total_target()}")
    print(f"Target Products: {ScraperConfig.TARGET_PRODUCTS_TOTAL}")
    
    print("\nMatrix Breakdown:")
    for skill_level, style_targets in SamplingMatrix.SAMPLING_MATRIX.items():
        for riding_style, count in style_targets.items():
            print(f"  {skill_level} × {riding_style}: {count}")
    
    print(f"\nAll Categories: {len(SamplingMatrix.get_all_categories())}")