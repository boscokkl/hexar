#!/usr/bin/env python3
"""
Analyze scraped results and generate column fill rate report
"""

import json
from typing import Dict, Any
from database import ScraperDatabase
from colorama import init, Fore, Style

init()

class ResultsAnalyzer:
    """Analyze scraped product data quality"""
    
    def __init__(self):
        self.db = ScraperDatabase()
    
    def analyze_all(self):
        """Generate comprehensive analysis"""
        
        print(f"{Fore.GREEN}📊 Standalone Scraper Results Analysis{Style.RESET_ALL}")
        print("=" * 70)
        
        # Get all data
        try:
            result = self.db.client.table("scraped_snowboard_products").select("*").execute()
            products = result.data
            
            if not products:
                print(f"{Fore.RED}❌ No products found in database{Style.RESET_ALL}")
                return
            
            print(f"📦 **Dataset Overview:**")
            print(f"   Total products: {len(products)}")
            
            # Column fill rate analysis
            self._analyze_column_fill_rates(products)
            
            # Distribution analysis
            self._analyze_distributions(products)
            
            # Data quality analysis
            self._analyze_data_quality(products)
            
            # Sample data
            self._show_sample_products(products)
            
        except Exception as e:
            print(f"{Fore.RED}❌ Analysis failed: {e}{Style.RESET_ALL}")
    
    def _analyze_column_fill_rates(self, products):
        """Analyze fill rates for each column"""
        
        print(f"\n📈 **Column Fill Rate Analysis:**")
        
        total_count = len(products)
        
        # Define expected columns and their importance
        columns = {
            # Core fields (required)
            'product_id': 'Core',
            'name': 'Core', 
            'evo_url': 'Core',
            'skill_level': 'Core',
            'riding_style': 'Core',
            
            # Important fields
            'brand': 'Important',
            'current_price': 'Important',
            'image_urls': 'Important',
            'availability_status': 'Important',
            
            # Nice-to-have fields
            'original_price': 'Optional',
            'sale_price': 'Optional',
            'model_year': 'Optional',
            'board_lengths': 'Optional', 
            'flex_rating': 'Optional',
            'camber_profile': 'Optional',
            'shape': 'Optional',
            'core_material': 'Optional',
            'base_material': 'Optional',
            'construction_type': 'Optional',
            'effective_edge': 'Optional',
            'manufacturer_description': 'Optional',
            'key_features': 'Optional',
            'terrain_suitability': 'Optional',
            'review_count': 'Optional',
            'average_rating': 'Optional',
            'evo_rating': 'Optional',
            'sizes_in_stock': 'Optional',
            'scraped_at': 'Meta',
            'scraper_version': 'Meta'
        }
        
        # Analyze each column
        column_stats = {}
        
        for column, importance in columns.items():
            filled_count = 0
            non_empty_count = 0
            
            for product in products:
                value = product.get(column)
                
                # Count non-null values
                if value is not None:
                    filled_count += 1
                    
                    # Count non-empty values (for strings and arrays)
                    if isinstance(value, str) and value.strip():
                        non_empty_count += 1
                    elif isinstance(value, list) and len(value) > 0:
                        non_empty_count += 1
                    elif isinstance(value, (int, float)) and value != 0:
                        non_empty_count += 1
                    elif not isinstance(value, (str, list)):
                        non_empty_count += 1
            
            fill_rate = (filled_count / total_count) * 100
            quality_rate = (non_empty_count / total_count) * 100
            
            column_stats[column] = {
                'filled_count': filled_count,
                'non_empty_count': non_empty_count,
                'fill_rate': fill_rate,
                'quality_rate': quality_rate,
                'importance': importance
            }
        
        # Display results by importance
        importance_order = ['Core', 'Important', 'Optional', 'Meta']
        
        for importance in importance_order:
            print(f"\n   {importance} Fields:")
            
            relevant_columns = [(col, stats) for col, stats in column_stats.items() 
                              if columns.get(col) == importance]
            
            for column, stats in relevant_columns:
                fill_pct = stats['fill_rate']
                quality_pct = stats['quality_rate']
                
                # Color coding for fill rates
                if fill_pct >= 95:
                    color = Fore.GREEN
                elif fill_pct >= 80:
                    color = Fore.YELLOW  
                else:
                    color = Fore.RED
                
                print(f"     {column:25s}: {color}{fill_pct:5.1f}%{Style.RESET_ALL} filled, {quality_pct:5.1f}% quality ({stats['non_empty_count']}/{total_count})")
    
    def _analyze_distributions(self, products):
        """Analyze data distributions"""
        
        print(f"\n🎯 **Data Distribution Analysis:**")
        
        # Skill level distribution
        skill_dist = {}
        for product in products:
            skill = product.get('skill_level')
            skill_dist[skill] = skill_dist.get(skill, 0) + 1
        
        print(f"\n   Skill Level Distribution:")
        for skill, count in sorted(skill_dist.items()):
            pct = (count / len(products)) * 100
            print(f"     {skill:12s}: {count:2d} products ({pct:4.1f}%)")
        
        # Riding style distribution
        style_dist = {}
        for product in products:
            style = product.get('riding_style')
            style_dist[style] = style_dist.get(style, 0) + 1
        
        print(f"\n   Riding Style Distribution:")
        for style, count in sorted(style_dist.items()):
            pct = (count / len(products)) * 100
            print(f"     {style:12s}: {count:2d} products ({pct:4.1f}%)")
        
        # Brand distribution (top 10)
        brand_dist = {}
        for product in products:
            brand = product.get('brand')
            if brand:
                brand_dist[brand] = brand_dist.get(brand, 0) + 1
        
        print(f"\n   Top Brands:")
        sorted_brands = sorted(brand_dist.items(), key=lambda x: x[1], reverse=True)[:10]
        for brand, count in sorted_brands:
            pct = (count / len(products)) * 100
            print(f"     {brand:15s}: {count:2d} products ({pct:4.1f}%)")
        
        # Price analysis
        prices = [p.get('current_price') for p in products if p.get('current_price')]
        if prices:
            print(f"\n   Price Analysis:")
            print(f"     Products with prices: {len(prices)}/{len(products)} ({len(prices)/len(products)*100:.1f}%)")
            print(f"     Price range: ${min(prices):.2f} - ${max(prices):.2f}")
            print(f"     Average price: ${sum(prices)/len(prices):.2f}")
    
    def _analyze_data_quality(self, products):
        """Analyze data quality metrics"""
        
        print(f"\n✅ **Data Quality Assessment:**")
        
        # Check for complete products (core fields filled)
        core_fields = ['product_id', 'name', 'evo_url', 'skill_level', 'riding_style']
        complete_products = 0
        
        for product in products:
            if all(product.get(field) for field in core_fields):
                complete_products += 1
        
        complete_rate = (complete_products / len(products)) * 100
        print(f"   Complete products (all core fields): {complete_products}/{len(products)} ({complete_rate:.1f}%)")
        
        # Check for rich products (important fields filled)
        important_fields = ['brand', 'current_price', 'image_urls']
        rich_products = 0
        
        for product in products:
            filled_important = sum(1 for field in important_fields if product.get(field))
            if filled_important >= 2:  # At least 2/3 important fields
                rich_products += 1
        
        rich_rate = (rich_products / len(products)) * 100
        print(f"   Rich products (2+ important fields): {rich_products}/{len(products)} ({rich_rate:.1f}%)")
        
        # Check for unique products
        unique_names = len(set(p.get('name', '') for p in products))
        unique_rate = (unique_names / len(products)) * 100
        print(f"   Unique product names: {unique_names}/{len(products)} ({unique_rate:.1f}%)")
        
        # Check URL validity
        valid_urls = sum(1 for p in products if p.get('evo_url', '').startswith('https://'))
        url_rate = (valid_urls / len(products)) * 100
        print(f"   Valid URLs: {valid_urls}/{len(products)} ({url_rate:.1f}%)")
    
    def _show_sample_products(self, products):
        """Show sample products for validation"""
        
        print(f"\n🔍 **Sample Products:**")
        
        # Show first 5 products with key info
        for i, product in enumerate(products[:5]):
            print(f"\n   Product {i+1}:")
            print(f"     ID: {product.get('product_id', 'N/A')}")
            print(f"     Name: {product.get('name', 'N/A')}")
            print(f"     Brand: {product.get('brand', 'N/A')}")
            print(f"     Classification: {product.get('skill_level', 'N/A')} × {product.get('riding_style', 'N/A')}")
            print(f"     Price: ${product.get('current_price', 'N/A')}")
            print(f"     URL: {product.get('evo_url', 'N/A')[:60]}...")
            
            images = product.get('image_urls', [])
            if images:
                print(f"     Image: {images[0][:60]}...")

if __name__ == "__main__":
    analyzer = ResultsAnalyzer()
    analyzer.analyze_all()