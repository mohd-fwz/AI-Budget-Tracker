#!/usr/bin/env python
"""Test keyword categorization with problematic descriptions"""

from utils.categorizer import categorize_by_keywords

test_cases = [
    "UPI-MYNTRA-CLOTHING SHOP",
    "UPI-Ramesh-auto fare", 
    "UPI-IRCTC-RAILWAY TICKET",
    "UPI-DECATHLON-SPORTS STORE",
    "UPI-Abdul-books",
    "UPI-DOMINOS-PIZZA ORDER"
]

print("Testing categorization with updated keywords:")
print("-" * 60)
for desc in test_cases:
    category = categorize_by_keywords(desc)
    print(f"{desc:35} → {category or 'Other'}")
