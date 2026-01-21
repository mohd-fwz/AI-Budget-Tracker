#!/usr/bin/env python
"""Test the better solution - AI only for ambiguous items"""

from utils.categorizer import categorize_by_keywords, is_ambiguous_description

test_cases = [
    # Clear transactions (should NOT need AI)
    ("UPI-MYNTRA-CLOTHING SHOP", "Clear"),
    ("UPI-DOMINOS-PIZZA ORDER", "Clear"),
    ("UPI-IRCTC-RAILWAY TICKET", "Clear"),
    ("UPI-VI-MOBILE BILL PAYMENT", "Clear"),
    ("REFUND-AMAZON-RETURN CREDIT", "Clear"),
    
    # Ambiguous transactions (should need AI)
    ("UPI-Ramesh-auto fare", "Ambiguous"),
    ("UPI-Abdul-books", "Ambiguous"),
    ("John - parking", "Ambiguous"),
    ("Payment to friend", "Ambiguous"),
]

print("Testing Better Solution (AI only for ambiguous items):")
print("=" * 80)

keyword_saves = 0
ai_needed = 0

for description, expected_type in test_cases:
    keyword_match = categorize_by_keywords(description)
    is_ambig = is_ambiguous_description(description)
    
    # Logic from updated code:
    if keyword_match:
        ai_call = "NO ✓ (keyword match)"
        category_type = "Keyword"
    elif is_ambig:
        ai_call = "YES (ambiguous)"
        category_type = "AI-only"
        ai_needed += 1
    else:
        ai_call = "NO ✓ (non-ambiguous fallback)"
        category_type = "Fallback"
    
    if not ai_call.startswith("YES"):
        keyword_saves += 1
    
    match_type = "✓" if ("ambiguous" in description.lower() and "YES" in ai_call) or ("ambiguous" not in description.lower() and "NO" in ai_call) else "?"
    
    print(f"{match_type} {description:35} → AI: {ai_call:25} ({category_type})")

print("=" * 80)
print(f"Summary:")
print(f"  AI calls skipped: {keyword_saves} transactions (save ~{keyword_saves * 200} tokens)")
print(f"  AI calls needed: {ai_needed} transactions (use ~{ai_needed * 200} tokens)")
print(f"  Total tokens saved: ~{keyword_saves * 200} out of ~{len(test_cases) * 300} tokens")
print(f"  Reduction: ~{int((keyword_saves / len(test_cases)) * 100)}%")
