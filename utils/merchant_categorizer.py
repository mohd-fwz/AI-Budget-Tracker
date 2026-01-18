"""
Merchant Categorizer - Eliminates AI ambiguity using multiple strategies
Combines UPI merchant database, MCC codes, and learned patterns
"""
from typing import Optional, Dict, Tuple
from models import db, Merchant, MerchantCategoryMapping
from sqlalchemy import func

# Indian-specific merchant database
INDIAN_MERCHANT_DATABASE = {
    # Food Delivery
    'swiggy': {'category': 'Groceries', 'confidence': 0.95, 'type': 'Food Delivery'},
    'zomato': {'category': 'Groceries', 'confidence': 0.95, 'type': 'Food Delivery'},
    'dunzo': {'category': 'Groceries', 'confidence': 0.90, 'type': 'Quick Commerce'},
    'zepto': {'category': 'Groceries', 'confidence': 0.95, 'type': 'Quick Commerce'},
    'blinkit': {'category': 'Groceries', 'confidence': 0.95, 'type': 'Quick Commerce'},
    'instamart': {'category': 'Groceries', 'confidence': 0.95, 'type': 'Quick Commerce'},

    # E-commerce
    'amazon': {'category': 'Shopping', 'confidence': 0.85, 'type': 'E-commerce'},
    'flipkart': {'category': 'Shopping', 'confidence': 0.85, 'type': 'E-commerce'},
    'myntra': {'category': 'Shopping', 'confidence': 0.90, 'type': 'Fashion'},
    'ajio': {'category': 'Shopping', 'confidence': 0.90, 'type': 'Fashion'},
    'nykaa': {'category': 'Shopping', 'confidence': 0.90, 'type': 'Beauty'},

    # Transport
    'uber': {'category': 'Transport', 'confidence': 0.95, 'type': 'Ride Hailing'},
    'ola': {'category': 'Transport', 'confidence': 0.95, 'type': 'Ride Hailing'},
    'rapido': {'category': 'Transport', 'confidence': 0.95, 'type': 'Ride Hailing'},
    'irctc': {'category': 'Transport', 'confidence': 0.95, 'type': 'Rail Travel'},
    'makemytrip': {'category': 'Transport', 'confidence': 0.90, 'type': 'Travel Booking'},
    'goibibo': {'category': 'Transport', 'confidence': 0.90, 'type': 'Travel Booking'},
    # Petrol Pumps
    'petrolpump': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'petrol': {'category': 'Transport', 'confidence': 0.90, 'type': 'Fuel'},
    'iocl': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'bpcl': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'hpcl': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'indianoil': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'bharatpetroleum': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'hindustanpetroleum': {'category': 'Transport', 'confidence': 0.95, 'type': 'Fuel'},
    'reliance': {'category': 'Transport', 'confidence': 0.85, 'type': 'Fuel'},
    'fastag': {'category': 'Transport', 'confidence': 0.95, 'type': 'Toll'},
    'paytmfastag': {'category': 'Transport', 'confidence': 0.95, 'type': 'Toll'},

    # Entertainment
    'bookmyshow': {'category': 'Entertainment', 'confidence': 0.95, 'type': 'Movies/Events'},
    'netflix': {'category': 'Entertainment', 'confidence': 0.95, 'type': 'Streaming'},
    'spotify': {'category': 'Entertainment', 'confidence': 0.95, 'type': 'Music Streaming'},
    'hotstar': {'category': 'Entertainment', 'confidence': 0.95, 'type': 'Streaming'},
    'primevideo': {'category': 'Entertainment', 'confidence': 0.95, 'type': 'Streaming'},

    # Bills & Utilities
    'airtel': {'category': 'Bills', 'confidence': 0.95, 'type': 'Telecom'},
    'jio': {'category': 'Bills', 'confidence': 0.95, 'type': 'Telecom'},
    'vodafone': {'category': 'Bills', 'confidence': 0.95, 'type': 'Telecom'},
    'bescom': {'category': 'Bills', 'confidence': 0.95, 'type': 'Electricity'},
    'bwssb': {'category': 'Bills', 'confidence': 0.95, 'type': 'Water'},

    # Healthcare
    'apollo': {'category': 'Healthcare', 'confidence': 0.95, 'type': 'Pharmacy'},
    'medplus': {'category': 'Healthcare', 'confidence': 0.95, 'type': 'Pharmacy'},
    '1mg': {'category': 'Healthcare', 'confidence': 0.95, 'type': 'Pharmacy'},
    'pharmeasy': {'category': 'Healthcare', 'confidence': 0.95, 'type': 'Pharmacy'},

    # Payment Apps (when used for merchant payments)
    'paytm': {'category': 'Other', 'confidence': 0.50, 'type': 'Payment Gateway'},
    'phonepe': {'category': 'Other', 'confidence': 0.50, 'type': 'Payment Gateway'},
    'googlepay': {'category': 'Other', 'confidence': 0.50, 'type': 'Payment Gateway'},
}


def categorize_by_merchant(
    merchant_name: Optional[str],
    upi_id: Optional[str],
    user_id: str,
    description: str
) -> Tuple[str, float, str]:
    """
    High-confidence categorization using merchant database

    Returns:
        (category, confidence, reasoning)

    Confidence levels:
        0.95+ = Very High (from known merchant database)
        0.80-0.94 = High (from user's learned patterns)
        0.60-0.79 = Medium (from similar merchants)
        < 0.60 = Low (fallback to AI)
    """

    # Strategy 1: Check known merchant database (Indian merchants)
    if merchant_name:
        merchant_key = merchant_name.lower().replace(' ', '')

        # Exact match
        if merchant_key in INDIAN_MERCHANT_DATABASE:
            data = INDIAN_MERCHANT_DATABASE[merchant_key]
            return (
                data['category'],
                data['confidence'],
                f"Known merchant: {merchant_name} ({data['type']})"
            )

        # Partial match (e.g., "swiggy food" matches "swiggy")
        for key, data in INDIAN_MERCHANT_DATABASE.items():
            if key in merchant_key or merchant_key in key:
                return (
                    data['category'],
                    data['confidence'] - 0.05,  # Slightly lower confidence
                    f"Matched merchant pattern: {merchant_name} → {key} ({data['type']})"
                )

    # Strategy 2: Check UPI handle for merchant clues
    if upi_id:
        upi_name = upi_id.split('@')[0].lower()
        for key, data in INDIAN_MERCHANT_DATABASE.items():
            if key in upi_name:
                return (
                    data['category'],
                    data['confidence'] - 0.05,
                    f"UPI merchant match: {upi_id} → {key} ({data['type']})"
                )

    # Strategy 3: Check user's learned merchant mappings
    if merchant_name:
        learned = db.session.query(MerchantCategoryMapping).filter_by(
            user_id=user_id,
            merchant_name=merchant_name
        ).first()

        if learned and learned.confidence >= 3:
            # User has confirmed this merchant 3+ times
            return (
                learned.category,
                0.85,
                f"Learned from your history ({learned.confidence}x confirmed)"
            )

    # Strategy 4: Check global merchant database (other users)
    if merchant_name:
        # Find most common category for this merchant across all users
        result = db.session.query(
            Merchant.default_category,
            func.sum(Merchant.transaction_count).label('total')
        ).filter(
            Merchant.name == merchant_name,
            Merchant.default_category.isnot(None)
        ).group_by(
            Merchant.default_category
        ).order_by(
            func.sum(Merchant.transaction_count).desc()
        ).first()

        if result and result.total >= 5:
            return (
                result.default_category,
                0.75,
                f"Community consensus: {merchant_name} → {result.default_category} ({result.total} transactions)"
            )

    # Strategy 5: Keyword matching from description
    category, confidence, reasoning = categorize_by_keywords(description)
    if confidence >= 0.70:
        return (category, confidence, reasoning)

    # Fallback: Low confidence, needs AI or user clarification
    return (None, 0.0, "No confident match found")


def categorize_by_keywords(description: str) -> Tuple[Optional[str], float, str]:
    """
    Fallback keyword-based categorization
    """
    if not description:
        return (None, 0.0, "No description")

    desc_lower = description.lower()

    # High-confidence keywords
    keyword_map = {
        'Groceries': [
            ('grocery', 0.90), ('supermarket', 0.90), ('food', 0.75),
            ('restaurant', 0.80), ('cafe', 0.80), ('eatery', 0.80),
            ('bakery', 0.85), ('kirana', 0.90)
        ],
        'Transport': [
            ('fuel', 0.90), ('petrol', 0.90), ('diesel', 0.90),
            ('petrolpump', 0.95), ('petrol pump', 0.95), ('filling station', 0.95),
            ('hp petrol', 0.95), ('iocl', 0.95), ('bpcl', 0.95), ('indian oil', 0.95),
            ('hindustan petroleum', 0.95), ('bharat petroleum', 0.95),
            ('cab', 0.85), ('taxi', 0.85), ('bus', 0.85),
            ('metro', 0.90), ('train', 0.90), ('flight', 0.85),
            ('parking', 0.85), ('toll', 0.90), ('fastag', 0.95)
        ],
        'Bills': [
            ('electricity', 0.95), ('water', 0.95), ('gas', 0.95),
            ('internet', 0.90), ('broadband', 0.90), ('recharge', 0.85),
            ('postpaid', 0.85), ('prepaid', 0.85)
        ],
        'Rent': [
            ('rent', 0.95), ('lease', 0.90), ('apartment', 0.85),
            ('flat', 0.85), ('pg', 0.90), ('hostel', 0.90)
        ],
        'Healthcare': [
            ('hospital', 0.95), ('clinic', 0.95), ('doctor', 0.90),
            ('medical', 0.90), ('pharmacy', 0.95), ('medicine', 0.90)
        ],
        'Entertainment': [
            ('movie', 0.90), ('cinema', 0.90), ('concert', 0.85),
            ('game', 0.75), ('subscription', 0.70)
        ],
        'Shopping': [
            ('purchase', 0.60), ('shopping', 0.70), ('retail', 0.65),
            ('store', 0.60), ('mall', 0.70)
        ]
    }

    best_match = (None, 0.0, "")

    for category, keywords in keyword_map.items():
        for keyword, confidence in keywords:
            if keyword in desc_lower:
                if confidence > best_match[1]:
                    best_match = (
                        category,
                        confidence,
                        f"Keyword match: '{keyword}' in description"
                    )

    return best_match


def get_categorization_strategy(
    merchant_name: Optional[str],
    upi_id: Optional[str],
    user_id: str,
    description: str
) -> Dict:
    """
    Main entry point for intelligent categorization

    Returns:
        {
            'suggested_category': str or None,
            'confidence': float (0.0 to 1.0),
            'needs_clarification': bool,
            'reasoning': str,
            'alternative_categories': List[str]
        }
    """
    category, confidence, reasoning = categorize_by_merchant(
        merchant_name, upi_id, user_id, description
    )

    return {
        'suggested_category': category,
        'confidence': confidence,
        'needs_clarification': confidence < 0.80,  # Only ask user if < 80% confident
        'reasoning': reasoning,
        'alternative_categories': _get_alternatives(category) if category else []
    }


def _get_alternatives(primary_category: str) -> list:
    """Get alternative categories similar to the primary one"""
    alternatives = {
        'Groceries': ['Shopping', 'Other'],
        'Shopping': ['Groceries', 'Entertainment', 'Other'],
        'Transport': ['Bills', 'Other'],
        'Bills': ['Transport', 'Rent', 'Other'],
        'Entertainment': ['Shopping', 'Other'],
        'Healthcare': ['Bills', 'Other'],
        'Rent': ['Bills', 'Other'],
    }
    return alternatives.get(primary_category, ['Other'])
