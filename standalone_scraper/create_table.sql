-- SQL Schema for Standalone Scraper Table
-- Run this in your Supabase SQL Editor to create the table

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

-- Verify table creation
SELECT 'Scraped snowboard products table created successfully!' as status;

-- Show table structure
SELECT column_name, data_type, is_nullable 
FROM information_schema.columns 
WHERE table_name = 'scraped_snowboard_products' 
ORDER BY ordinal_position;