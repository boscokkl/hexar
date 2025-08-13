"""
Pydantic models for standalone scraper
Isolated from main hexar-backend models
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field, validator
import hashlib
import re

class ScrapedProduct(BaseModel):
    """Model for scraped snowboard product data"""
    
    # Basic Product Info  
    product_id: Optional[str] = Field(None, description="Unique identifier generated from name/brand")
    name: str = Field(..., min_length=3, description="Product name")
    brand: Optional[str] = Field(None, description="Brand name extracted from product name")
    model_year: Optional[str] = Field(None, description="Model year if available")
    evo_url: str = Field(..., description="Full Evo.com product URL")
    image_urls: List[str] = Field(default_factory=list, description="Product image URLs")
    
    # Pricing
    current_price: Optional[float] = Field(None, ge=0, description="Current price in USD")
    original_price: Optional[float] = Field(None, ge=0, description="Original/MSRP price")
    sale_price: Optional[float] = Field(None, ge=0, description="Sale price if on sale")
    
    # Classification Matrix Fields (required)
    skill_level: str = Field(..., description="Target skill level")
    riding_style: str = Field(..., description="Primary riding style")
    
    # Technical Specs
    board_lengths: List[str] = Field(default_factory=list, description="Available board lengths")
    flex_rating: Optional[str] = Field(None, description="Flex rating (soft/medium/stiff)")
    camber_profile: Optional[str] = Field(None, description="Camber profile type")
    shape: Optional[str] = Field(None, description="Board shape (directional/twin/etc)")
    
    # Detailed Specs (optional)
    core_material: Optional[str] = Field(None, description="Core material")
    base_material: Optional[str] = Field(None, description="Base material")
    construction_type: Optional[str] = Field(None, description="Construction type")
    effective_edge: Optional[str] = Field(None, description="Effective edge measurement")
    
    # Marketing Content
    manufacturer_description: Optional[str] = Field(None, description="Product description")
    key_features: List[str] = Field(default_factory=list, description="Key product features")
    terrain_suitability: List[str] = Field(default_factory=list, description="Suitable terrain types")
    
    # Reviews & Ratings
    review_count: int = Field(default=0, ge=0, description="Number of reviews")
    average_rating: Optional[float] = Field(None, ge=0, le=10, description="Average review rating")
    evo_rating: Optional[float] = Field(None, ge=0, le=10, description="Evo staff rating")
    
    # Availability
    availability_status: str = Field(default="unknown", description="Stock availability")
    sizes_in_stock: List[str] = Field(default_factory=list, description="Available sizes")
    
    # Metadata
    scraped_at: datetime = Field(default_factory=datetime.utcnow, description="Scraping timestamp")
    scraper_version: str = Field(default="1.0", description="Scraper version")
    
    @validator('skill_level')
    def validate_skill_level(cls, v):
        valid_levels = ['beginner', 'intermediate', 'advanced', 'expert']
        if v not in valid_levels:
            raise ValueError(f'skill_level must be one of {valid_levels}')
        return v
    
    @validator('riding_style')
    def validate_riding_style(cls, v):
        valid_styles = ['all-mountain', 'freeride', 'freestyle', 'powder', 'carving']
        if v not in valid_styles:
            raise ValueError(f'riding_style must be one of {valid_styles}')
        return v
    
    @validator('availability_status')
    def validate_availability(cls, v):
        valid_statuses = ['in_stock', 'out_of_stock', 'limited', 'backorder', 'unknown']
        if v not in valid_statuses:
            raise ValueError(f'availability_status must be one of {valid_statuses}')
        return v
    
    def __init__(self, **data):
        """Initialize product and generate ID if not provided"""
        if not data.get('product_id') and data.get('name'):
            # Generate product ID from name
            name = data['name']
            hash_suffix = hashlib.md5(name.encode()).hexdigest()[:12]
            
            # Create readable prefix from first few words
            safe_name_words = re.sub(r'[^a-z0-9\s]', '', name.lower()).split()[:2]
            safe_name = '_'.join(safe_name_words) if safe_name_words else "product"
            
            data['product_id'] = f"evo_{safe_name}_{hash_suffix}"
        
        super().__init__(**data)
    
    @validator('brand', pre=True, always=True)
    def extract_brand(cls, v, values):
        """Extract brand from product name if not provided"""
        if v:  # If brand is already provided, use it
            return v
        
        name = values.get('name', '')
        if not name:
            return None
        
        # Common snowboard brands
        brands = [
            'Burton', 'Lib Tech', 'Jones', 'Capita', 'Never Summer',
            'Salomon', 'K2', 'Rossignol', 'Arbor', 'Ride', 'GNU',
            'Nitro', 'Yes', 'Rome', 'Flow', 'Bataleon', 'Atomic',
            'Head', 'Volkl', 'Slash', 'Weston', 'Prior', 'Korua'
        ]
        
        name_words = name.split()
        for word in name_words:
            for brand in brands:
                if word.lower() == brand.lower():
                    return brand
        
        # If no brand found, use first word as brand
        return name_words[0] if name_words else None
    
    @validator('current_price', 'original_price', 'sale_price', pre=True)
    def parse_price(cls, v):
        """Parse price from string or return None"""
        if v is None:
            return None
        
        if isinstance(v, (int, float)):
            return float(v)
        
        if isinstance(v, str):
            # Remove currency symbols and extra text
            price_match = re.search(r'[\d,]+\.?\d*', v.replace(',', ''))
            if price_match:
                return float(price_match.group())
        
        return None
    
    def get_matrix_category(self) -> str:
        """Get matrix category string for tracking"""
        return f"{self.skill_level}_{self.riding_style}"
    
    def to_database_dict(self) -> Dict[str, Any]:
        """Convert to dictionary suitable for database insertion"""
        return {
            'product_id': self.product_id,
            'name': self.name,
            'brand': self.brand,
            'model_year': self.model_year,
            'evo_url': self.evo_url,
            'image_urls': self.image_urls,
            'current_price': self.current_price,
            'original_price': self.original_price,
            'sale_price': self.sale_price,
            'skill_level': self.skill_level,
            'riding_style': self.riding_style,
            'board_lengths': self.board_lengths,
            'flex_rating': self.flex_rating,
            'camber_profile': self.camber_profile,
            'shape': self.shape,
            'core_material': self.core_material,
            'base_material': self.base_material,
            'construction_type': self.construction_type,
            'effective_edge': self.effective_edge,
            'manufacturer_description': self.manufacturer_description,
            'key_features': self.key_features,
            'terrain_suitability': self.terrain_suitability,
            'review_count': self.review_count,
            'average_rating': self.average_rating,
            'evo_rating': self.evo_rating,
            'availability_status': self.availability_status,
            'sizes_in_stock': self.sizes_in_stock,
            'scraped_at': self.scraped_at.isoformat() if self.scraped_at else None,
            'scraper_version': self.scraper_version
        }

class MatrixProgress(BaseModel):
    """Track sampling matrix progress"""
    
    skill_level: str
    riding_style: str
    target_count: int
    current_count: int = 0
    scraped_products: List[str] = Field(default_factory=list)  # product_ids
    
    @property
    def is_complete(self) -> bool:
        """Check if this category has reached its target"""
        return self.current_count >= self.target_count
    
    @property
    def remaining_needed(self) -> int:
        """How many more products needed for this category"""
        return max(0, self.target_count - self.current_count)
    
    def add_product(self, product_id: str) -> bool:
        """Add a product to this category. Returns True if successfully added."""
        if self.is_complete:
            return False
        
        if product_id not in self.scraped_products:
            self.scraped_products.append(product_id)
            self.current_count += 1
            return True
        
        return False

class ScrapingSession(BaseModel):
    """Track overall scraping session progress"""
    
    session_id: str = Field(default_factory=lambda: datetime.utcnow().strftime("%Y%m%d_%H%M%S"))
    started_at: datetime = Field(default_factory=datetime.utcnow)
    target_total: int = Field(default=50)
    
    # Progress tracking
    matrix_progress: Dict[str, MatrixProgress] = Field(default_factory=dict)
    total_scraped: int = 0
    successful_products: List[str] = Field(default_factory=list)
    failed_urls: List[str] = Field(default_factory=list)
    
    # Performance metrics
    pages_scraped: int = 0
    requests_made: int = 0
    total_time_seconds: float = 0
    
    @property
    def is_complete(self) -> bool:
        """Check if session has reached target"""
        return self.total_scraped >= self.target_total
    
    @property
    def completion_percentage(self) -> float:
        """Get completion percentage"""
        return min(100.0, (self.total_scraped / self.target_total) * 100)
    
    def add_product(self, product: ScrapedProduct) -> bool:
        """Add a product and update matrix progress"""
        category_key = product.get_matrix_category()
        
        # Initialize category progress if needed
        if category_key not in self.matrix_progress:
            from config import SamplingMatrix
            skill_level, riding_style = product.skill_level, product.riding_style
            target = SamplingMatrix.get_category_targets(skill_level, riding_style)
            
            self.matrix_progress[category_key] = MatrixProgress(
                skill_level=skill_level,
                riding_style=riding_style,
                target_count=target
            )
        
        # Try to add to category
        category_progress = self.matrix_progress[category_key]
        if category_progress.add_product(product.product_id):
            self.total_scraped += 1
            self.successful_products.append(product.product_id)
            return True
        
        return False
    
    def get_status_summary(self) -> Dict[str, Any]:
        """Get session status summary"""
        completed_categories = sum(1 for mp in self.matrix_progress.values() if mp.is_complete)
        total_categories = len(self.matrix_progress)
        
        return {
            'session_id': self.session_id,
            'completion_percentage': self.completion_percentage,
            'total_scraped': self.total_scraped,
            'target_total': self.target_total,
            'completed_categories': completed_categories,
            'total_categories': total_categories,
            'pages_scraped': self.pages_scraped,
            'requests_made': self.requests_made,
            'failed_urls_count': len(self.failed_urls),
            'elapsed_time_minutes': self.total_time_seconds / 60
        }

if __name__ == "__main__":
    # Test model validation
    test_product = ScrapedProduct(
        name="Burton Custom Snowboard 2024",
        evo_url="https://www.evo.com/snowboards/burton-custom",
        skill_level="intermediate",
        riding_style="all-mountain",
        current_price="599.95"
    )
    
    print(f"Product ID: {test_product.product_id}")
    print(f"Brand: {test_product.brand}")
    print(f"Price: ${test_product.current_price}")
    print(f"Matrix Category: {test_product.get_matrix_category()}")