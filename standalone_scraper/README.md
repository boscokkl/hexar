# Standalone Evo.com Scraper

Isolated web scraper for building a real snowboard product database to test Hexar agents.

## 🎯 Purpose

Create a balanced dataset of 50 snowboards across skill levels and riding styles:

| Skill Level | All-Mountain | Freeride | Freestyle | Powder | Carving | **Total** |
|-------------|--------------|----------|-----------|---------|---------|-----------|
| Beginner    | 3            | 2        | 3         | 1       | 1       | **10**    |
| Intermediate| 4            | 3        | 4         | 2       | 2       | **15**    |
| Advanced    | 4            | 4        | 4         | 3       | 2       | **17**    |
| Expert      | 2            | 2        | 2         | 1       | 1       | **8**     |
| **Total**   | **13**       | **11**   | **13**    | **7**   | **6**   | **50**    |

## 🏗️ Architecture

**Completely Isolated** from main hexar-backend codebase:

```
standalone_scraper/
├── scraper.py              # Main scraper with matrix sampling
├── config.py              # Configuration and matrix definitions  
├── database.py            # Supabase connection and operations
├── models.py              # Pydantic models for scraped data
├── selectors.py           # CSS selectors and parsing logic
├── matrix_manager.py      # Sampling matrix management
├── create_table.sql       # Database schema
├── requirements.txt       # Dependencies
└── .env.example           # Configuration template
```

## 🚀 Setup

### 1. Install Dependencies

```bash
cd standalone_scraper
pip install -r requirements.txt
```

### 2. Environment Configuration

```bash
cp .env.example .env
# Edit .env with your Supabase credentials
```

Required environment variables:
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_KEY=your-service-role-key-here
```

### 3. Create Database Table

Run the SQL in `create_table.sql` in your Supabase SQL Editor:

```sql
-- Creates: scraped_snowboard_products table
-- With proper indexes and permissions
```

### 4. Test Configuration

```bash
python config.py     # Verify matrix configuration
python database.py   # Test database connection
```

## 🏃‍♂️ Usage

### Run Full Scraper

```bash
python scraper.py
```

**Features:**
- ✅ Matrix-driven sampling (balanced across categories)
- ✅ Progress tracking with colored output  
- ✅ Duplicate detection
- ✅ Rate limiting (2-second delays)
- ✅ Graceful error handling
- ✅ Real-time progress tables

### Test Small Sample

```bash
# Modify TARGET_PRODUCTS_TOTAL in .env for testing
TARGET_PRODUCTS_TOTAL=10
python scraper.py
```

### Monitor Progress

The scraper provides real-time progress updates:

```
📊 Matrix Sampling Progress
================================================================================
Category                  Current  Target   Complete   Priority  
--------------------------------------------------------------------------------
beginner_all-mountain     0        3        ❌ No      3.0       
intermediate_freestyle     1        4        ❌ No      4.5       
advanced_freeride         2        4        ❌ No      3.0       
...
--------------------------------------------------------------------------------
Total: 15/50 (30.0%)
🎯 Next priority: intermediate × freestyle
```

## 📊 Database Schema

**Table:** `scraped_snowboard_products`

**Key Fields:**
- `product_id` - Unique identifier
- `name`, `brand`, `evo_url` - Basic product info  
- `skill_level`, `riding_style` - Matrix classification (required)
- `current_price`, `original_price` - Pricing data
- `board_lengths[]`, `flex_rating`, `camber_profile` - Technical specs
- `review_count`, `average_rating` - Review data
- `scraped_at`, `scraper_version` - Metadata

**Compatibility:** Schema matches existing Hexar `Product` and `static_product_specs` models.

## 🎛️ Configuration

### Sampling Matrix

Modify `config.py` to adjust target distribution:

```python
SAMPLING_MATRIX = {
    "beginner": {
        "all-mountain": 3,
        "freestyle": 3, 
        # ...
    },
    # ...
}
```

### Scraper Settings

Adjust in `.env`:

```bash
SCRAPER_DELAY_SECONDS=2.0      # Rate limiting
SCRAPER_TIMEOUT_SECONDS=15.0   # Request timeout
TARGET_PRODUCTS_TOTAL=50       # Total target products
```

## 🔍 Data Quality

**Extracted Data:**
- ✅ Product names and brands (auto-detected)
- ✅ Current pricing (parsed from strings)
- ✅ Product URLs and images
- ✅ Skill level classification (from content)
- ✅ Riding style classification (from category)
- ✅ Technical specs (when available)

**Validation:**
- Pydantic model validation
- Duplicate detection by product_id
- Matrix quota enforcement
- Price parsing with fallbacks

## 🎯 Integration with Hexar

**Schema Compatibility:**
```python
# Scraped data maps directly to existing schemas
scraped_product = ScrapedProduct(...)
hexar_product = Product(
    name=scraped_product.name,
    price=f"${scraped_product.current_price}",
    image_url=scraped_product.image_urls[0],
    # ...
)
```

**Testing Agent Performance:**
1. Run scraper to populate database
2. Point agents to `scraped_snowboard_products` table  
3. Test agent queries against real product data
4. Measure performance improvements vs. sample data

## 🛠️ Troubleshooting

**Database Connection Issues:**
```bash
python database.py  # Test connection
# Check SUPABASE_URL and SUPABASE_SERVICE_KEY
```

**No Products Found:**
- Check Evo.com site structure changes
- Update CSS selectors in `selectors.py`  
- Test with DEBUG_MODE=true

**Rate Limiting:**
- Increase SCRAPER_DELAY_SECONDS
- Monitor Evo.com response times
- Consider using proxy rotation

## 📈 Performance

**Expected Performance:**
- ~2-5 products per minute (with 2s delays)
- 50 products in 10-25 minutes
- Database storage: ~5-10KB per product

**Optimization:**
- Parallel category scraping (future)
- Enhanced CSS selector targeting
- Improved price/spec extraction

## 🔒 Ethical Considerations

- ✅ Respects robots.txt guidelines
- ✅ Rate limiting (2-second delays)
- ✅ User-Agent identification  
- ✅ Non-aggressive scraping patterns
- ✅ Educational/testing purpose only

## 📝 Next Steps

1. **Run Initial Scrape:** Populate 50-product dataset
2. **Agent Integration:** Connect agents to scraped data
3. **Performance Testing:** Measure agent improvements
4. **Data Enhancement:** Add more detailed specs
5. **Multi-Vendor:** Extend to other snowboard sites

---

**Status:** ✅ Ready for production scraping
**Isolation:** ✅ Completely separate from main codebase  
**Database:** ✅ Schema compatible with existing agents