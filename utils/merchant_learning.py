"""
Merchant Learning System
Learns and applies user's category preferences for merchants/descriptions
"""
import re
from models import db, MerchantCategoryMapping
from datetime import datetime


def normalize_merchant_name(description: str) -> str:
    """
    Normalize merchant/description for consistent matching

    Examples:
        "UPI-AMAZON PAY-12345" -> "amazon pay"
        "Swiggy Order #12345" -> "swiggy order"
        "ATM WDL 123456" -> "atm wdl"

    Args:
        description: Raw transaction description

    Returns:
        Normalized merchant name (lowercase, alphanumeric only)
    """
    # Convert to lowercase
    normalized = description.lower()

    # Remove common prefixes
    prefixes = [
        r'upi-',
        r'pos-',
        r'neft-',
        r'imps-',
        r'atm-',
        r'online-',
        r'card-',
    ]
    for prefix in prefixes:
        normalized = re.sub(f'^{prefix}', '', normalized)

    # Remove transaction IDs, reference numbers, order numbers
    # Pattern: consecutive digits (6 or more)
    normalized = re.sub(r'\d{6,}', '', normalized)

    # Remove special characters, keep only letters, numbers, and spaces
    normalized = re.sub(r'[^a-z0-9\s]', ' ', normalized)

    # Normalize whitespace
    normalized = ' '.join(normalized.split())

    # Trim to first 100 characters
    normalized = normalized[:100].strip()

    return normalized


def get_learned_category(user_id: str, description: str) -> dict:
    """
    Check if we've learned a category for this merchant

    Args:
        user_id: User identifier
        description: Transaction description

    Returns:
        {
            'found': bool,
            'category': str or None,
            'confidence': int or None,
            'merchant_name': str (normalized)
        }
    """
    merchant_name = normalize_merchant_name(description)

    if not merchant_name:
        return {
            'found': False,
            'category': None,
            'confidence': None,
            'merchant_name': merchant_name
        }

    # Look up in database
    mapping = MerchantCategoryMapping.query.filter_by(
        user_id=user_id,
        merchant_name=merchant_name
    ).first()

    if mapping:
        return {
            'found': True,
            'category': mapping.category,
            'confidence': mapping.confidence,
            'merchant_name': merchant_name
        }
    else:
        return {
            'found': False,
            'category': None,
            'confidence': None,
            'merchant_name': merchant_name
        }


def save_merchant_category(user_id: str, description: str, category: str) -> dict:
    """
    Save or update a merchant-category mapping

    If mapping exists, increment confidence counter.
    If new, create with confidence=1.

    Args:
        user_id: User identifier
        description: Transaction description
        category: Category to associate with this merchant

    Returns:
        {
            'action': 'created' or 'updated',
            'mapping': dict (mapping object as dict)
        }
    """
    merchant_name = normalize_merchant_name(description)

    if not merchant_name:
        raise ValueError("Could not normalize merchant name from description")

    # Check if mapping exists
    mapping = MerchantCategoryMapping.query.filter_by(
        user_id=user_id,
        merchant_name=merchant_name
    ).first()

    if mapping:
        # Update existing mapping
        if mapping.category != category:
            # Category changed - reset confidence to 1
            mapping.category = category
            mapping.confidence = 1
            action = 'updated'
        else:
            # Same category - increment confidence
            mapping.confidence += 1
            action = 'updated'

        mapping.updated_at = datetime.utcnow()
    else:
        # Create new mapping
        mapping = MerchantCategoryMapping(
            user_id=user_id,
            merchant_name=merchant_name,
            category=category,
            confidence=1
        )
        db.session.add(mapping)
        action = 'created'

    db.session.commit()

    return {
        'action': action,
        'mapping': mapping.to_dict()
    }


def get_all_learned_mappings(user_id: str) -> list:
    """
    Get all learned merchant mappings for a user

    Args:
        user_id: User identifier

    Returns:
        List of mapping dictionaries, sorted by confidence (highest first)
    """
    mappings = MerchantCategoryMapping.query.filter_by(
        user_id=user_id
    ).order_by(
        MerchantCategoryMapping.confidence.desc(),
        MerchantCategoryMapping.updated_at.desc()
    ).all()

    return [mapping.to_dict() for mapping in mappings]


def delete_merchant_mapping(user_id: str, merchant_name: str) -> bool:
    """
    Delete a learned merchant mapping

    Args:
        user_id: User identifier
        merchant_name: Normalized merchant name

    Returns:
        True if deleted, False if not found
    """
    mapping = MerchantCategoryMapping.query.filter_by(
        user_id=user_id,
        merchant_name=merchant_name
    ).first()

    if mapping:
        db.session.delete(mapping)
        db.session.commit()
        return True
    else:
        return False
