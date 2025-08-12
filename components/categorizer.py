"""
Auto-categorization system for transactions
Uses merchant patterns and keywords to assign categories
"""

import re
import logging
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class CategoryRule:
    """Category rule with patterns and priority"""
    category: str
    subcategory: Optional[str]
    patterns: List[str]  # Regex patterns to match
    keywords: List[str]  # Simple keyword matches
    priority: int = 1    # Higher number = higher priority


class TransactionCategorizer:
    """Auto-categorization system for financial transactions"""
    
    def __init__(self):
        """Initialize with default category rules"""
        self.rules = self._load_default_rules()
        self.custom_rules = []
    
    def _load_default_rules(self) -> List[CategoryRule]:
        """Load default categorization rules"""
        return [
            # Food & Dining
            CategoryRule(
                category="Food & Dining",
                subcategory="Restaurants",
                patterns=[
                    r"RESTAURANT|BISTRO|CAFE|DINER|EATERY|GRILL|BAR|PUB",
                    r"PIZZA|BURGER|SUSHI|TACO|COFFEE|STARBUCKS|TIM HORTONS",
                    r"MCDONALDS|SUBWAY|A&W|PIZZA HUT|DOMINOS"
                ],
                keywords=["restaurant", "cafe", "coffee", "bar", "pub", "diner"],
                priority=2
            ),
            CategoryRule(
                category="Food & Dining", 
                subcategory="Groceries",
                patterns=[
                    r"SUPERMARKET|GROCERY|SAFEWAY|LOBLAWS|METRO|FOOD BASICS",
                    r"COSTCO|WALMART.*SUPERCENTER|SAVE ON FOODS"
                ],
                keywords=["grocery", "supermarket", "food"],
                priority=2
            ),
            CategoryRule(
                category="Food & Dining",
                subcategory="Fast Food",
                patterns=[
                    r"MCDONALDS|SUBWAY|BURGER KING|KFC|TACO BELL|WENDYS",
                    r"A&W|DAIRY QUEEN|POPEYES|MUCHO BURRITO"
                ],
                keywords=["mcdonalds", "subway", "burger"],
                priority=3
            ),
            
            # Transportation
            CategoryRule(
                category="Transportation",
                subcategory="Rideshare",
                patterns=[r"UBER|LYFT"],
                keywords=["uber", "lyft", "rideshare"],
                priority=3
            ),
            CategoryRule(
                category="Transportation",
                subcategory="Public Transit", 
                patterns=[r"TRANSIT|PRESTO|COMPASS|MTA"],
                keywords=["transit", "presto", "metro"],
                priority=3
            ),
            CategoryRule(
                category="Transportation",
                subcategory="Gas",
                patterns=[r"PETRO|SHELL|ESSO|CHEVRON|EXXON|BP|GAS"],
                keywords=["petro", "gas", "fuel"],
                priority=2
            ),
            CategoryRule(
                category="Transportation",
                subcategory="Airlines",
                patterns=[r"AIR CANADA|WESTJET|UNITED|DELTA|AMERICAN AIR"],
                keywords=["airline", "airways", "flight"],
                priority=3
            ),
            
            # Shopping
            CategoryRule(
                category="Shopping",
                subcategory="Online",
                patterns=[r"AMAZON|PAYPAL|EBAY"],
                keywords=["amazon", "paypal", "online"],
                priority=3
            ),
            CategoryRule(
                category="Shopping",
                subcategory="Retail",
                patterns=[
                    r"WALMART|TARGET|CANADIAN TIRE|HOME DEPOT|BEST BUY",
                    r"SHOPPERS DRUG MART|DOLLARAMA|WINNERS"
                ],
                keywords=["walmart", "target", "retail"],
                priority=2
            ),
            CategoryRule(
                category="Shopping",
                subcategory="Clothing",
                patterns=[
                    r"LULULEMON|H&M|ZARA|GAP|OLD NAVY|UNIQLO",
                    r"WINNERS|MARSHALLS|NORDSTROM"
                ],
                keywords=["clothing", "fashion", "apparel"],
                priority=3
            ),
            
            # Entertainment
            CategoryRule(
                category="Entertainment",
                subcategory="Streaming",
                patterns=[r"NETFLIX|SPOTIFY|APPLE.*MUSIC|DISNEY|PRIME"],
                keywords=["netflix", "spotify", "streaming"],
                priority=3
            ),
            CategoryRule(
                category="Entertainment",
                subcategory="Events",
                patterns=[r"TICKETMASTER|STUBHUB|CONCERT|THEATRE"],
                keywords=["ticket", "concert", "show", "event"],
                priority=2
            ),
            
            # Health & Fitness
            CategoryRule(
                category="Health & Fitness",
                subcategory="Pharmacy",
                patterns=[r"SHOPPERS DRUG|PHARMACY|CVS|WALGREENS"],
                keywords=["pharmacy", "drug", "medical"],
                priority=3
            ),
            CategoryRule(
                category="Health & Fitness",
                subcategory="Gym",
                patterns=[r"GYM|FITNESS|YOGA|GOODLIFE"],
                keywords=["gym", "fitness", "workout"],
                priority=3
            ),
            
            # Bills & Utilities
            CategoryRule(
                category="Bills & Utilities",
                subcategory="Phone",
                patterns=[r"ROGERS|BELL|TELUS|FIDO|KOODO"],
                keywords=["phone", "mobile", "cellular"],
                priority=3
            ),
            
            # Transfers & Payments
            CategoryRule(
                category="Transfers",
                subcategory="Payment",
                patterns=[r"PAYMENT|PYMT|TRANSFER|TRSF"],
                keywords=["payment", "transfer", "pymt"],
                priority=4
            )
        ]
    
    def categorize_transaction(self, description: str, merchant: str = None, 
                             amount: float = None) -> Tuple[Optional[str], Optional[str]]:
        """Categorize a single transaction"""
        
        # Combine description and merchant for matching
        text_to_match = description.upper()
        if merchant:
            text_to_match += f" {merchant.upper()}"
        
        # Check all rules, prioritizing higher priority ones
        best_match = None
        best_priority = 0
        
        for rule in sorted(self.rules + self.custom_rules, key=lambda r: r.priority, reverse=True):
            # Check regex patterns
            for pattern in rule.patterns:
                if re.search(pattern, text_to_match):
                    if rule.priority >= best_priority:
                        best_match = rule
                        best_priority = rule.priority
                        break
            
            # Check keywords if no pattern match
            if not best_match or rule.priority > best_priority:
                for keyword in rule.keywords:
                    if keyword.upper() in text_to_match:
                        if rule.priority >= best_priority:
                            best_match = rule
                            best_priority = rule.priority
                        break
        
        if best_match:
            return best_match.category, best_match.subcategory
        
        return None, None
    
    def categorize_bulk(self, transactions: List[Dict]) -> List[Dict]:
        """Categorize multiple transactions"""
        categorized = []
        
        for txn in transactions:
            category, subcategory = self.categorize_transaction(
                txn.get('description', ''),
                txn.get('merchant', ''),
                txn.get('amount', 0)
            )
            
            txn_copy = txn.copy()
            if category:
                txn_copy['category'] = category
                txn_copy['subcategory'] = subcategory
            
            categorized.append(txn_copy)
        
        return categorized
    
    def add_custom_rule(self, category: str, subcategory: str, 
                       patterns: List[str] = None, keywords: List[str] = None,
                       priority: int = 5) -> None:
        """Add custom categorization rule"""
        rule = CategoryRule(
            category=category,
            subcategory=subcategory,
            patterns=patterns or [],
            keywords=keywords or [],
            priority=priority
        )
        self.custom_rules.append(rule)
        logger.info(f"Added custom rule: {category}/{subcategory}")
    
    def get_categories(self) -> List[Tuple[str, Optional[str]]]:
        """Get all available categories"""
        categories = set()
        for rule in self.rules + self.custom_rules:
            categories.add((rule.category, rule.subcategory))
        return sorted(list(categories))
    
    def explain_categorization(self, description: str, merchant: str = None) -> str:
        """Explain why a transaction was categorized as it was"""
        category, subcategory = self.categorize_transaction(description, merchant)
        
        if not category:
            return f"No category match found for '{description}'"
        
        text = description.upper()
        if merchant:
            text += f" {merchant.upper()}"
        
        # Find which rule matched
        for rule in sorted(self.rules + self.custom_rules, key=lambda r: r.priority, reverse=True):
            if rule.category == category and rule.subcategory == subcategory:
                # Check what matched
                for pattern in rule.patterns:
                    if re.search(pattern, text):
                        return f"Categorized as {category}/{subcategory} - matched pattern: {pattern}"
                
                for keyword in rule.keywords:
                    if keyword.upper() in text:
                        return f"Categorized as {category}/{subcategory} - matched keyword: {keyword}"
        
        return f"Categorized as {category}/{subcategory}"