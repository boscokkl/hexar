"""
Database operations for standalone scraper
Isolated Supabase connection and table management
"""

import os
import logging
from typing import List, Optional, Dict, Any
from supabase import create_client, Client
from models import ScrapedProduct, ScrapingSession
from config import ScraperConfig

logger = logging.getLogger(__name__)

class ScraperDatabase:
    """Isolated database manager for standalone scraper"""
    
    def __init__(self):
        """Initialize Supabase client"""
        if not ScraperConfig.SUPABASE_URL or not ScraperConfig.SUPABASE_SERVICE_KEY:
            raise ValueError("SUPABASE_URL and SUPABASE_SERVICE_KEY must be set in environment")
        
        self.client: Client = create_client(
            ScraperConfig.SUPABASE_URL,
            ScraperConfig.SUPABASE_SERVICE_KEY
        )
        
        self.table_name = "scraped_snowboard_products"
        
        logger.info(f"Connected to Supabase: {ScraperConfig.SUPABASE_URL}")
    
    async def ensure_table_exists(self) -> bool:
        """Ensure the scraped products table exists"""
        try:
            # Test table existence with a simple query
            result = self.client.table(self.table_name).select("id").limit(1).execute()
            logger.info(f"Table '{self.table_name}' exists and is accessible")
            return True
            
        except Exception as e:
            logger.error(f"Table '{self.table_name}' does not exist or is not accessible: {e}")
            logger.info("Please run the database schema creation script first")
            return False
    
    def insert_product(self, product: ScrapedProduct) -> bool:
        """Insert a single product into the database"""
        try:
            data = product.to_database_dict()
            
            result = self.client.table(self.table_name).insert(data).execute()
            
            if result.data:
                logger.info(f"✅ Inserted product: {product.name} (ID: {product.product_id})")
                return True
            else:
                logger.error(f"❌ Failed to insert product: {product.name}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Error inserting product {product.name}: {e}")
            return False
    
    def insert_products_batch(self, products: List[ScrapedProduct]) -> tuple[int, int]:
        """Insert multiple products in batch. Returns (success_count, total_count)"""
        if not products:
            return 0, 0
        
        try:
            data_list = [product.to_database_dict() for product in products]
            
            result = self.client.table(self.table_name).insert(data_list).execute()
            
            success_count = len(result.data) if result.data else 0
            total_count = len(products)
            
            logger.info(f"✅ Batch insert: {success_count}/{total_count} products successful")
            
            return success_count, total_count
            
        except Exception as e:
            logger.error(f"❌ Batch insert error: {e}")
            return 0, len(products)
    
    def check_product_exists(self, product_id: str) -> bool:
        """Check if a product already exists in database"""
        try:
            result = self.client.table(self.table_name).select("product_id").eq("product_id", product_id).execute()
            return len(result.data) > 0
            
        except Exception as e:
            logger.error(f"Error checking product existence: {e}")
            return False
    
    def get_matrix_progress(self) -> Dict[str, Dict[str, int]]:
        """Get current matrix progress from database"""
        try:
            result = self.client.table(self.table_name).select("skill_level, riding_style").execute()
            
            progress = {}
            for row in result.data:
                skill_level = row['skill_level']
                riding_style = row['riding_style']
                
                if skill_level not in progress:
                    progress[skill_level] = {}
                
                if riding_style not in progress[skill_level]:
                    progress[skill_level][riding_style] = 0
                
                progress[skill_level][riding_style] += 1
            
            return progress
            
        except Exception as e:
            logger.error(f"Error getting matrix progress: {e}")
            return {}
    
    def get_total_scraped_count(self) -> int:
        """Get total number of scraped products"""
        try:
            result = self.client.table(self.table_name).select("id", count="exact").execute()
            return result.count or 0
            
        except Exception as e:
            logger.error(f"Error getting total count: {e}")
            return 0
    
    def get_products_by_category(self, skill_level: str, riding_style: str) -> List[Dict[str, Any]]:
        """Get products for specific skill level and riding style"""
        try:
            result = self.client.table(self.table_name)\
                .select("*")\
                .eq("skill_level", skill_level)\
                .eq("riding_style", riding_style)\
                .execute()
            
            return result.data or []
            
        except Exception as e:
            logger.error(f"Error getting products for {skill_level} {riding_style}: {e}")
            return []
    
    def delete_product(self, product_id: str) -> bool:
        """Delete a product by ID"""
        try:
            result = self.client.table(self.table_name).delete().eq("product_id", product_id).execute()
            
            if result.data:
                logger.info(f"🗑️ Deleted product: {product_id}")
                return True
            else:
                logger.warning(f"Product not found for deletion: {product_id}")
                return False
                
        except Exception as e:
            logger.error(f"Error deleting product {product_id}: {e}")
            return False
    
    def clear_all_scraped_products(self) -> bool:
        """Clear all scraped products (use with caution!)"""
        try:
            result = self.client.table(self.table_name).delete().neq("id", "00000000-0000-0000-0000-000000000000").execute()
            
            deleted_count = len(result.data) if result.data else 0
            logger.info(f"🗑️ Cleared {deleted_count} scraped products")
            return True
            
        except Exception as e:
            logger.error(f"Error clearing scraped products: {e}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            # Get total count
            total_result = self.client.table(self.table_name).select("id", count="exact").execute()
            total_count = total_result.count or 0
            
            # Get matrix breakdown
            matrix_result = self.client.table(self.table_name)\
                .select("skill_level, riding_style")\
                .execute()
            
            # Process matrix data
            matrix_breakdown = {}
            skill_totals = {}
            style_totals = {}
            
            for row in matrix_result.data:
                skill = row['skill_level']
                style = row['riding_style']
                
                # Matrix breakdown
                if skill not in matrix_breakdown:
                    matrix_breakdown[skill] = {}
                if style not in matrix_breakdown[skill]:
                    matrix_breakdown[skill][style] = 0
                matrix_breakdown[skill][style] += 1
                
                # Skill totals
                if skill not in skill_totals:
                    skill_totals[skill] = 0
                skill_totals[skill] += 1
                
                # Style totals
                if style not in style_totals:
                    style_totals[style] = 0
                style_totals[style] += 1
            
            # Get recent scraping activity
            recent_result = self.client.table(self.table_name)\
                .select("scraped_at")\
                .order("scraped_at", desc=True)\
                .limit(1)\
                .execute()
            
            last_scraped = None
            if recent_result.data:
                last_scraped = recent_result.data[0]['scraped_at']
            
            return {
                'total_products': total_count,
                'matrix_breakdown': matrix_breakdown,
                'skill_level_totals': skill_totals,
                'riding_style_totals': style_totals,
                'last_scraped': last_scraped,
                'table_name': self.table_name
            }
            
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {'error': str(e)}

def create_table_schema() -> str:
    """Return SQL schema for creating the scraped products table"""
    return """
    -- Create table for scraped snowboard products
    CREATE TABLE IF NOT EXISTS scraped_snowboard_products (
        id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
        
        -- Basic Product Info
        product_id TEXT UNIQUE NOT NULL,
        name TEXT NOT NULL,
        brand TEXT,
        model_year TEXT,
        evo_url TEXT NOT NULL,
        image_urls TEXT[],
        
        -- Pricing
        current_price NUMERIC(10,2),
        original_price NUMERIC(10,2),
        sale_price NUMERIC(10,2),
        
        -- Classification Matrix Fields (required)
        skill_level TEXT NOT NULL CHECK (skill_level IN ('beginner', 'intermediate', 'advanced', 'expert')),
        riding_style TEXT NOT NULL CHECK (riding_style IN ('all-mountain', 'freeride', 'freestyle', 'powder', 'carving')),
        
        -- Technical Specs
        board_lengths TEXT[],  -- ['154', '157', '160', '163']
        flex_rating TEXT,      -- 'soft', 'medium', 'stiff'
        camber_profile TEXT,   -- 'camber', 'rocker', 'hybrid'
        shape TEXT,           -- 'directional', 'twin', 'directional-twin'
        
        -- Detailed Specs (if available)
        core_material TEXT,
        base_material TEXT,
        construction_type TEXT,
        effective_edge TEXT,
        
        -- Marketing Content
        manufacturer_description TEXT,
        key_features TEXT[],
        terrain_suitability TEXT[],
        
        -- Reviews & Ratings
        review_count INTEGER DEFAULT 0,
        average_rating NUMERIC(3,1),
        evo_rating NUMERIC(3,1),
        
        -- Availability
        availability_status TEXT DEFAULT 'unknown',
        sizes_in_stock TEXT[],
        
        -- Metadata
        scraped_at TIMESTAMPTZ DEFAULT NOW(),
        last_updated TIMESTAMPTZ DEFAULT NOW(),
        scraper_version TEXT DEFAULT '1.0',
        
        -- Matrix tracking (computed column)
        matrix_category TEXT GENERATED ALWAYS AS (skill_level || '_' || riding_style) STORED
    );
    
    -- Create indexes for performance
    CREATE INDEX IF NOT EXISTS idx_scraped_products_product_id ON scraped_snowboard_products(product_id);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_name ON scraped_snowboard_products(name);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_brand ON scraped_snowboard_products(brand);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_skill_level ON scraped_snowboard_products(skill_level);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_riding_style ON scraped_snowboard_products(riding_style);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_matrix_category ON scraped_snowboard_products(matrix_category);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_scraped_at ON scraped_snowboard_products(scraped_at);
    CREATE INDEX IF NOT EXISTS idx_scraped_products_price ON scraped_snowboard_products(current_price);
    
    -- Disable RLS for standalone scraper table
    ALTER TABLE scraped_snowboard_products DISABLE ROW LEVEL SECURITY;
    
    -- Grant permissions
    GRANT ALL ON scraped_snowboard_products TO service_role;
    GRANT SELECT ON scraped_snowboard_products TO authenticated;
    
    SELECT 'Scraped snowboard products table created successfully!' as status;
    """

if __name__ == "__main__":
    # Test database connection
    try:
        db = ScraperDatabase()
        print("✅ Database connection successful")
        
        # Print schema for manual creation
        print("\n📋 SQL Schema for table creation:")
        print(create_table_schema())
        
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        print("Please check your .env file configuration")