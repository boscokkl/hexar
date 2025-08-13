"""
Matrix sampling manager for balanced dataset collection
Tracks progress and manages sampling quotas
"""

from typing import Dict, List, Tuple, Optional
from dataclasses import dataclass
from config import SamplingMatrix
from models import ScrapedProduct, MatrixProgress, ScrapingSession
import logging

logger = logging.getLogger(__name__)

@dataclass
class CategoryStatus:
    """Status of a specific matrix category"""
    skill_level: str
    riding_style: str
    target_count: int
    current_count: int
    is_complete: bool
    priority_score: float  # Higher = more urgently needed

class MatrixManager:
    """Manages sampling matrix progress and prioritization"""
    
    def __init__(self, target_total: int = 50):
        """Initialize matrix manager with target counts"""
        self.target_total = target_total
        self.session = ScrapingSession(target_total=target_total)
        self.category_status: Dict[str, CategoryStatus] = {}
        
        # Initialize all categories from sampling matrix
        self._initialize_categories()
        
        logger.info(f"MatrixManager initialized: {len(self.category_status)} categories, target {target_total} products")
    
    def _initialize_categories(self):
        """Initialize all matrix categories"""
        for skill_level, style_targets in SamplingMatrix.SAMPLING_MATRIX.items():
            for riding_style, target_count in style_targets.items():
                if target_count > 0:
                    category_key = f"{skill_level}_{riding_style}"
                    
                    self.category_status[category_key] = CategoryStatus(
                        skill_level=skill_level,
                        riding_style=riding_style,
                        target_count=target_count,
                        current_count=0,
                        is_complete=False,
                        priority_score=target_count  # Start with target as priority
                    )
                    
                    # Initialize in session
                    self.session.matrix_progress[category_key] = MatrixProgress(
                        skill_level=skill_level,
                        riding_style=riding_style,
                        target_count=target_count
                    )
    
    def can_accept_product(self, skill_level: str, riding_style: str) -> bool:
        """Check if we can accept a product for this category"""
        category_key = f"{skill_level}_{riding_style}"
        
        if category_key not in self.category_status:
            logger.warning(f"Unknown category: {category_key}")
            return False
        
        status = self.category_status[category_key]
        return not status.is_complete
    
    def add_product(self, product: ScrapedProduct) -> bool:
        """Add a product to the matrix if there's space"""
        category_key = f"{product.skill_level}_{product.riding_style}"
        
        if not self.can_accept_product(product.skill_level, product.riding_style):
            logger.debug(f"Category {category_key} is complete, rejecting product: {product.name}")
            return False
        
        # Add to session
        if self.session.add_product(product):
            # Update category status
            status = self.category_status[category_key]
            status.current_count += 1
            
            if status.current_count >= status.target_count:
                status.is_complete = True
                logger.info(f"✅ Category {category_key} completed ({status.current_count}/{status.target_count})")
            
            # Update priority scores
            self._update_priority_scores()
            
            logger.info(f"Added product to {category_key}: {product.name} ({status.current_count}/{status.target_count})")
            return True
        
        return False
    
    def _update_priority_scores(self):
        """Update priority scores based on current progress"""
        for category_key, status in self.category_status.items():
            if status.is_complete:
                status.priority_score = 0
            else:
                remaining = status.target_count - status.current_count
                completion_ratio = status.current_count / status.target_count
                
                # Higher priority for categories that are behind
                status.priority_score = remaining * (1 + (1 - completion_ratio))
    
    def get_priority_categories(self, limit: int = 5) -> List[Tuple[str, str]]:
        """Get highest priority categories that need products"""
        incomplete_categories = [
            (status.skill_level, status.riding_style, status.priority_score)
            for status in self.category_status.values()
            if not status.is_complete
        ]
        
        # Sort by priority score (descending)
        incomplete_categories.sort(key=lambda x: x[2], reverse=True)
        
        return [(skill, style) for skill, style, _ in incomplete_categories[:limit]]
    
    def get_next_search_category(self) -> Optional[Tuple[str, str]]:
        """Get the next category that should be searched"""
        priority_categories = self.get_priority_categories(limit=1)
        return priority_categories[0] if priority_categories else None
    
    def is_complete(self) -> bool:
        """Check if matrix sampling is complete"""
        return self.session.is_complete or all(status.is_complete for status in self.category_status.values())
    
    def get_completion_summary(self) -> Dict[str, any]:
        """Get detailed completion summary"""
        completed_categories = sum(1 for status in self.category_status.values() if status.is_complete)
        total_categories = len(self.category_status)
        
        # Category breakdown
        category_breakdown = {}
        for category_key, status in self.category_status.items():
            category_breakdown[category_key] = {
                'current': status.current_count,
                'target': status.target_count,
                'complete': status.is_complete,
                'priority': status.priority_score
            }
        
        # Skill level summary
        skill_summary = {}
        for skill_level in SamplingMatrix.SKILL_LEVELS:
            skill_categories = [s for s in self.category_status.values() if s.skill_level == skill_level]
            skill_summary[skill_level] = {
                'current': sum(s.current_count for s in skill_categories),
                'target': sum(s.target_count for s in skill_categories),
                'completed_categories': sum(1 for s in skill_categories if s.is_complete),
                'total_categories': len(skill_categories)
            }
        
        # Riding style summary
        style_summary = {}
        for riding_style in SamplingMatrix.RIDING_STYLES.keys():
            style_categories = [s for s in self.category_status.values() if s.riding_style == riding_style]
            style_summary[riding_style] = {
                'current': sum(s.current_count for s in style_categories),
                'target': sum(s.target_count for s in style_categories),
                'completed_categories': sum(1 for s in style_categories if s.is_complete),
                'total_categories': len(style_categories)
            }
        
        return {
            'overall': {
                'total_products': self.session.total_scraped,
                'target_products': self.target_total,
                'completion_percentage': self.session.completion_percentage,
                'is_complete': self.is_complete()
            },
            'categories': {
                'completed': completed_categories,
                'total': total_categories,
                'breakdown': category_breakdown
            },
            'skill_levels': skill_summary,
            'riding_styles': style_summary,
            'next_priority_categories': self.get_priority_categories(limit=3),
            'session_stats': self.session.get_status_summary()
        }
    
    def print_progress_table(self):
        """Print a formatted progress table"""
        print("\n📊 Matrix Sampling Progress")
        print("=" * 80)
        
        # Header
        print(f"{'Category':<25} {'Current':<8} {'Target':<8} {'Complete':<10} {'Priority':<10}")
        print("-" * 80)
        
        # Sort by priority (highest first)
        sorted_categories = sorted(
            self.category_status.items(),
            key=lambda x: x[1].priority_score,
            reverse=True
        )
        
        for category_key, status in sorted_categories:
            complete_str = "✅ Yes" if status.is_complete else "❌ No"
            priority_str = f"{status.priority_score:.1f}" if not status.is_complete else "0.0"
            
            print(f"{category_key:<25} {status.current_count:<8} {status.target_count:<8} {complete_str:<10} {priority_str:<10}")
        
        print("-" * 80)
        print(f"Total: {self.session.total_scraped}/{self.target_total} ({self.session.completion_percentage:.1f}%)")
        
        if not self.is_complete():
            next_category = self.get_next_search_category()
            if next_category:
                print(f"🎯 Next priority: {next_category[0]} × {next_category[1]}")
    
    def get_search_urls_by_priority(self) -> List[Dict[str, str]]:
        """Get search URLs ordered by priority"""
        from config import EvoUrls
        
        priority_categories = self.get_priority_categories(limit=10)
        
        search_urls = []
        for skill_level, riding_style in priority_categories:
            url = EvoUrls.build_category_url(riding_style)
            search_urls.append({
                'skill_level': skill_level,
                'riding_style': riding_style,
                'url': url,
                'priority': self.category_status[f"{skill_level}_{riding_style}"].priority_score
            })
        
        return search_urls
    
    def load_existing_progress(self, database_progress: Dict[str, Dict[str, int]]):
        """Load existing progress from database"""
        logger.info("Loading existing matrix progress from database...")
        
        for skill_level, style_counts in database_progress.items():
            for riding_style, count in style_counts.items():
                category_key = f"{skill_level}_{riding_style}"
                
                if category_key in self.category_status:
                    # Update counts
                    status = self.category_status[category_key]
                    status.current_count = min(count, status.target_count)
                    status.is_complete = status.current_count >= status.target_count
                    
                    # Update session
                    if category_key in self.session.matrix_progress:
                        progress = self.session.matrix_progress[category_key]
                        progress.current_count = status.current_count
                        # Note: We don't have product_ids from database summary
                    
                    self.session.total_scraped = sum(
                        s.current_count for s in self.category_status.values()
                    )
        
        # Update priority scores
        self._update_priority_scores()
        
        logger.info(f"Loaded progress: {self.session.total_scraped}/{self.target_total} products")

if __name__ == "__main__":
    # Test matrix manager
    manager = MatrixManager()
    
    print("Initial Matrix Status:")
    manager.print_progress_table()
    
    # Test adding products
    from models import ScrapedProduct
    
    test_products = [
        ScrapedProduct(
            name="Burton Custom", 
            evo_url="test", 
            skill_level="intermediate", 
            riding_style="all-mountain"
        ),
        ScrapedProduct(
            name="Lib Tech T.Rice", 
            evo_url="test", 
            skill_level="advanced", 
            riding_style="freeride"
        )
    ]
    
    for product in test_products:
        manager.add_product(product)
    
    print("\nAfter adding test products:")
    manager.print_progress_table()
    
    print("\nPriority URLs:")
    urls = manager.get_search_urls_by_priority()
    for url_info in urls[:5]:
        print(f"  {url_info['skill_level']} × {url_info['riding_style']}: {url_info['url']}")