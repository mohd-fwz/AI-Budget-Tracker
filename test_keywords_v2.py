#!/usr/bin/env python
"""Test keyword categorization with all problematic descriptions from screenshots"""

from utils.categorizer import categorize_by_keywords

test_cases = [
    # Previous batch
    "UPI-MYNTRA-CLOTHING SHOP",
    "UPI-Ramesh-auto fare", 
    "UPI-IRCTC-RAILWAY TICKET",
    "UPI-DECATHLON-SPORTS STORE",
    "UPI-Abdul-books",
    "UPI-DOMINOS-PIZZA ORDER",
    # New batch from latest screenshot
    "UPI-VI-MOBILE BILL PAYMENT",
    "UPI-RELIANCE FRESH MARKET"
]

print("Testing all problem transactions:")
print("-" * 60)
for desc in test_cases:
    category = categorize_by_keywords(desc)
    expected = {
        "UPI-MYNTRA-CLOTHING SHOP": "Shopping",
        "UPI-Ramesh-auto fare": "Transport",
        "UPI-IRCTC-RAILWAY TICKET": "Transport",
        "UPI-DECATHLON-SPORTS STORE": "Shopping",
        "UPI-Abdul-books": "Shopping",
        "UPI-DOMINOS-PIZZA ORDER": "Entertainment",
        "UPI-VI-MOBILE BILL PAYMENT": "Bills",
        "UPI-RELIANCE FRESH MARKET": "Groceries"
    }[desc]
    
    status = "✓" if category == expected else "✗"
    print(f"{status} {desc:35} → {category or 'Other':15} (expected: {expected})")
