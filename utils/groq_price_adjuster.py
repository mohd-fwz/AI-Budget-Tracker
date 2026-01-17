"""
GROQ AI Price Adjuster
Uses GROQ API to estimate current prices based on baseline data and inflation trends
"""
import os
import requests
from datetime import datetime
from config import Config


def adjust_price_for_inflation(item_name: str, base_price: float, city: str, base_date: str) -> float:
    """
    Use GROQ AI to estimate current price based on base price and inflation

    Args:
        item_name: e.g., "rice per kg", "petrol per liter"
        base_price: Price at base_date (in rupees)
        city: City name in India
        base_date: When base_price was recorded (YYYY-MM-DD)

    Returns:
        Adjusted price estimate (in rupees)
    """
    # If no API key, return base price
    if not Config.GROQ_API_KEY:
        return base_price

    try:
        current_date = datetime.now().strftime('%Y-%m')

        # Build prompt for AI
        prompt = f"""You are a price estimation expert for India.

Base information:
- Item: {item_name}
- Location: {city}, India
- Base price: Rs.{base_price} (as of {base_date})
- Current date: {current_date}

Based on:
1. Historical inflation trends in India (typically 4-6% annual)
2. Seasonal factors if applicable (vegetables, fuel, etc.)
3. Recent market conditions
4. City-specific cost variations

Estimate the current realistic market price of {item_name} in {city}.

IMPORTANT: Respond with ONLY a single numeric value (no currency symbol, no text, no explanation).
Example: If estimated price is Rs.105.50, respond with: 105.5"""

        # Call GROQ API
        response = requests.post(
            Config.GROQ_API_URL,
            headers={
                'Authorization': f'Bearer {Config.GROQ_API_KEY}',
                'Content-Type': 'application/json'
            },
            json={
                'model': Config.GROQ_MODEL,
                'messages': [
                    {
                        'role': 'system',
                        'content': 'You are a price estimation expert. Always respond with only numeric values.'
                    },
                    {
                        'role': 'user',
                        'content': prompt
                    }
                ],
                'temperature': 0.3,
                'max_tokens': 20
            },
            timeout=10
        )

        if response.status_code == 200:
            result = response.json()
            ai_response = result['choices'][0]['message']['content'].strip()

            # Extract numeric value (handle potential text)
            # Remove common text like "Rs.", "rupees", etc.
            ai_response = ai_response.replace('Rs.', '').replace('Rs', '').replace('rupees', '').strip()

            try:
                adjusted_price = float(ai_response)

                # Sanity check: Don't allow more than 50% deviation from base
                # This prevents AI hallucinations
                max_price = base_price * 1.5
                min_price = base_price * 0.5

                if adjusted_price > max_price or adjusted_price < min_price:
                    print(f"AI adjustment too extreme for {item_name} ({adjusted_price}), using base price")
                    return base_price

                return adjusted_price

            except ValueError:
                print(f"Could not parse AI response for {item_name}: {ai_response}")
                return base_price

        else:
            print(f"GROQ API error for {item_name}: {response.status_code}")
            return base_price

    except Exception as e:
        print(f"Price adjustment error for {item_name}: {str(e)}")
        return base_price  # Fallback to base price on any error


def get_inflation_factor(base_date: str) -> float:
    """
    Calculate simple inflation multiplier based on time elapsed
    Assumes 5% annual inflation in India

    Args:
        base_date: Base date string (YYYY-MM-DD)

    Returns:
        Inflation multiplier (e.g., 1.05 for 5% increase)
    """
    try:
        base = datetime.strptime(base_date, '%Y-%m-%d')
        current = datetime.now()

        # Calculate years elapsed
        years_elapsed = (current - base).days / 365.25

        # 5% annual inflation
        inflation_rate = 0.05
        multiplier = (1 + inflation_rate) ** years_elapsed

        return multiplier

    except Exception:
        return 1.0  # No adjustment if date parsing fails


def adjust_price_simple(base_price: float, base_date: str) -> float:
    """
    Simple inflation adjustment without AI (fallback method)

    Args:
        base_price: Original price
        base_date: Date of original price (YYYY-MM-DD)

    Returns:
        Inflation-adjusted price
    """
    multiplier = get_inflation_factor(base_date)
    return base_price * multiplier
