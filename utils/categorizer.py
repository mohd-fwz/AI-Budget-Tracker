"""
Expense categorization utilities
Uses learned mappings -> keyword matching -> AI for categorizations
Priority: Learned preferences > Keywords > AI
"""
import re
import requests
from config import Config
from utils.merchant_learning import get_learned_category


# Keyword patterns for automatic categorization
# Each category has a list of keywords that indicate that category
CATEGORY_KEYWORDS = {
    'Groceries': [
        'supermarket', 'grocery', 'walmart', 'target', 'costco', 'whole foods',
        'trader joe', 'safeway', 'kroger', 'publix', 'food', 'market',
        'aldi', 'lidl', 'tesco', 'carrefour', 'fresh', 'produce'
    ],
    'Entertainment': [
        'netflix', 'spotify', 'hulu', 'disney', 'hbo', 'amazon prime',
        'movie', 'cinema', 'theater', 'theatre', 'concert', 'game',
        'xbox', 'playstation', 'nintendo', 'steam', 'ticket', 'show',
        'entertainment', 'music', 'streaming', 'youtube premium'
    ],
    'Rent': [
        'rent', 'lease', 'landlord', 'property', 'housing', 'apartment',
        'mortgage', 'housing payment', 'monthly rent'
    ],
    'Transport': [
        'uber', 'lyft', 'taxi', 'cab', 'gas', 'fuel', 'petrol', 'shell',
        'chevron', 'bp', 'exxon', 'transit', 'metro', 'bus', 'train',
        'subway', 'parking', 'toll', 'car', 'vehicle', 'auto',
        'transportation', 'citymapper', 'parking meter'
    ],
    'Bills': [
        'electric', 'electricity', 'water', 'utility', 'utilities', 'gas bill',
        'internet', 'wifi', 'phone', 'mobile', 'verizon', 'att', 't-mobile',
        'comcast', 'spectrum', 'insurance', 'bill payment', 'utilities payment'
    ],
    'Shopping': [
        'amazon', 'ebay', 'shop', 'store', 'mall', 'clothing', 'clothes',
        'fashion', 'shoes', 'electronics', 'best buy', 'apple store',
        'h&m', 'zara', 'uniqlo', 'nike', 'adidas', 'online shopping',
        'department store', 'retail'
    ],
    'Healthcare': [
        'doctor', 'hospital', 'clinic', 'pharmacy', 'cvs', 'walgreens',
        'medicine', 'medical', 'health', 'dental', 'dentist', 'prescription',
        'urgent care', 'healthcare', 'copay', 'medication', 'drug store'
    ]
}


def categorize_by_keywords(description):
    """
    Categorize expense based on keyword matching

    Args:
        description (str): Expense description

    Returns:
        str: Category name or None if no match found

    Algorithm:
        1. Convert description to lowercase
        2. Check each category's keywords
        3. Return first matching category
        4. Return None if no matches
    """
    if not description:
        return None

    description_lower = description.lower()

    # Check each category's keywords
    for category, keywords in CATEGORY_KEYWORDS.items():
        for keyword in keywords:
            # Use word boundaries to avoid partial matches
            # e.g., "car" shouldn't match "card"
            pattern = r'\b' + re.escape(keyword) + r'\b'
            if re.search(pattern, description_lower):
                return category

    return None


def is_ambiguous_description(description):
    """
    Detect if a description is ambiguous (like person names, unclear vendors)

    Args:
        description (str): Expense description

    Returns:
        bool: True if description seems ambiguous

    Detection criteria:
    - Very short descriptions (1-2 words)
    - Contains only names (capitalized words without clear keywords)
    - No recognizable business/merchant keywords
    """
    if not description or len(description.strip()) < 3:
        return True

    words = description.strip().split()

    # If it's just 1-2 capitalized words (likely a name)
    if len(words) <= 2 and all(word[0].isupper() for word in words if word):
        # Check if it matches any of our keywords
        if categorize_by_keywords(description):
            return False  # Has clear keywords, not ambiguous
        return True  # Looks like a person name or unclear

    return False


def categorize_with_ai(description, amount=None, return_suggestions=False):
    """
    Categorize expense using Groq AI API as fallback

    Args:
        description (str): Expense description
        amount (float, optional): Expense amount for additional context
        return_suggestions (bool): If True, returns multiple suggestions with reasoning

    Returns:
        If return_suggestions=False:
            str: Category name (one of the valid categories) or 'Other'
        If return_suggestions=True:
            dict: {
                'suggested_category': str,
                'confidence': str ('high', 'medium', 'low'),
                'alternatives': [str],
                'reasoning': str,
                'needs_clarification': bool
            }

    The AI is prompted to classify the expense into one of the predefined categories.
    """
    if not Config.GROQ_API_KEY:
        print("Warning: GROQ_API_KEY not configured, defaulting to 'Other'")
        if return_suggestions:
            return {
                'suggested_category': 'Other',
                'confidence': 'low',
                'alternatives': [],
                'reasoning': 'AI not configured',
                'needs_clarification': True
            }
        return 'Other'

    try:
        categories_list = ', '.join(CATEGORY_KEYWORDS.keys()) + ', Income'

        if return_suggestions:
            # Enhanced prompt for suggestions
            prompt = f"""You are an expense categorization assistant. Analyze this expense and provide categorization suggestions.

Expense description: "{description}"
{"Amount: ₹" + str(amount) if amount else ""}

Available categories: {categories_list}, Other

Provide your response in this exact format:
CATEGORY: [your best guess category]
CONFIDENCE: [high/medium/low]
ALTERNATIVES: [comma-separated list of 1-2 alternative categories if uncertain]
REASONING: [brief explanation in one sentence]

Example for "Ramesh - parking":
CATEGORY: Transport
CONFIDENCE: medium
ALTERNATIVES: Bills, Other
REASONING: Payment to a person named Ramesh for parking suggests transportation costs."""

            max_tokens = 150
        else:
            # Simple prompt for direct categorization
            prompt = f"""You are an expense categorization assistant. Categorize the following expense into exactly ONE of these categories: {categories_list}, or Other.

Expense description: "{description}"
{"Amount: ₹" + str(amount) if amount else ""}

Respond with ONLY the category name, nothing else. If you're not sure, respond with "Other"."""
            max_tokens = 10

        # Call Groq API
        headers = {
            'Authorization': f'Bearer {Config.GROQ_API_KEY}',
            'Content-Type': 'application/json'
        }

        payload = {
            'model': Config.GROQ_MODEL,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ],
            'temperature': 0.3,
            'max_tokens': max_tokens
        }

        response = requests.post(
            Config.GROQ_API_URL,
            headers=headers,
            json=payload,
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            content = result['choices'][0]['message']['content'].strip()

            if return_suggestions:
                # Parse the structured response
                lines = content.split('\n')
                suggestion = {
                    'suggested_category': 'Other',
                    'confidence': 'low',
                    'alternatives': [],
                    'reasoning': 'Unable to categorize',
                    'needs_clarification': True
                }

                for line in lines:
                    if line.startswith('CATEGORY:'):
                        cat = line.replace('CATEGORY:', '').strip()
                        valid_cats = list(CATEGORY_KEYWORDS.keys()) + ['Other']
                        if cat in valid_cats:
                            suggestion['suggested_category'] = cat
                    elif line.startswith('CONFIDENCE:'):
                        conf = line.replace('CONFIDENCE:', '').strip().lower()
                        if conf in ['high', 'medium', 'low']:
                            suggestion['confidence'] = conf
                    elif line.startswith('ALTERNATIVES:'):
                        alts = line.replace('ALTERNATIVES:', '').strip()
                        suggestion['alternatives'] = [a.strip() for a in alts.split(',') if a.strip()]
                    elif line.startswith('REASONING:'):
                        suggestion['reasoning'] = line.replace('REASONING:', '').strip()

                # Mark as needing clarification if confidence is not high
                suggestion['needs_clarification'] = (
                    suggestion['confidence'] in ['medium', 'low'] or
                    is_ambiguous_description(description)
                )

                return suggestion
            else:
                # Simple category response
                category = content.strip()
                valid_categories = list(CATEGORY_KEYWORDS.keys()) + ['Other']
                if category in valid_categories:
                    return category

        # If API call failed or returned invalid category
        if return_suggestions:
            return {
                'suggested_category': 'Other',
                'confidence': 'low',
                'alternatives': [],
                'reasoning': 'Could not categorize automatically',
                'needs_clarification': True
            }
        return 'Other'

    except Exception as e:
        print(f"AI categorization error: {str(e)}")
        if return_suggestions:
            return {
                'suggested_category': 'Other',
                'confidence': 'low',
                'alternatives': [],
                'reasoning': f'Error: {str(e)}',
                'needs_clarification': True
            }
        return 'Other'


def categorize_expense(description, amount=None, use_ai=True, user_id=None, transaction_type='expense'):
    """
    Main categorization function with learning support

    Args:
        description (str): Expense description
        amount (float, optional): Expense amount
        use_ai (bool): Whether to use AI as fallback (default: True)
        user_id (str, optional): User ID for learned mappings
        transaction_type (str): 'expense' | 'income' (default: 'expense')

    Returns:
        str: Category name

    Flow:
        1. Auto-categorize income transactions as 'Income'
        2. Check learned mappings first (highest confidence >= 2)
        3. Try keyword matching (fast and free)
        4. If no match and use_ai=True, use AI categorization
        5. Default to 'Other' if all else fails
    """
    if not description:
        return 'Other'

    # PRIORITY 0: Auto-categorize income transactions
    if transaction_type == 'income':
        return 'Income'

    # PRIORITY 1: Check learned mappings (if user_id provided)
    if user_id:
        learned = get_learned_category(user_id, description)
        # Only use learned category if confidence >= 2 (confirmed at least twice)
        if learned['found'] and learned['confidence'] >= 2:
            return learned['category']

    # PRIORITY 2: Try keyword matching
    category = categorize_by_keywords(description)
    if category:
        return category

    # PRIORITY 3: Check learned mappings with lower confidence
    # (if we didn't have high-confidence match earlier)
    if user_id:
        learned = get_learned_category(user_id, description)
        if learned['found']:
            return learned['category']

    # PRIORITY 4: If no keyword match and AI is enabled, use AI
    if use_ai:
        return categorize_with_ai(description, amount)

    # Default to 'Other' if no matches
    return 'Other'
