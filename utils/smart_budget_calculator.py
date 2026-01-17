"""
Smart Budget Calculator
Calculates personalized budgets using:
1. User preferences (consumption quantities, transport mode, etc.)
2. Market prices from database
3. AI-adjusted prices for inflation
4. Historical spending comparison
"""
import json
import os
from typing import Dict, Optional
from datetime import datetime
from utils.groq_price_adjuster import adjust_price_for_inflation, adjust_price_simple


def load_market_prices() -> Dict:
    """Load static market price database"""
    prices_file = os.path.join(os.path.dirname(__file__), 'market_prices.json')
    try:
        with open(prices_file, 'r') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error loading market prices: {e}")
        return {}


def get_current_price(city: str, item_key: str, use_ai: bool = True) -> float:
    """
    Get current price with optional AI adjustment

    Args:
        city: City name
        item_key: Price key like 'groceries.rice_per_kg' or 'transport.petrol_per_liter'
        use_ai: Whether to use AI for price adjustment (default: True)

    Returns:
        Current estimated price in rupees
    """
    prices = load_market_prices()

    # Find city data (case-insensitive, handle variations)
    city_data = None
    for city_name, data in prices.items():
        if city_name.lower() == city.lower():
            city_data = data
            break

    # Fallback to Bangalore if city not found
    if not city_data:
        print(f"City '{city}' not found in price database, using Bangalore prices")
        city_data = prices.get('Bangalore', {})

    # Navigate nested structure (e.g., 'groceries.rice_per_kg')
    parts = item_key.split('.')
    if len(parts) == 2:
        category, item = parts
        base_price = city_data.get(category, {}).get(item, 0)
    else:
        base_price = city_data.get(item_key, 0)

    if base_price == 0:
        return 0

    base_date = city_data.get('last_updated', '2024-12-01')

    # Use AI adjustment if enabled
    if use_ai:
        adjusted_price = adjust_price_for_inflation(
            item_name=item_key.replace('_', ' '),
            base_price=base_price,
            city=city,
            base_date=base_date
        )
    else:
        # Simple inflation adjustment
        adjusted_price = adjust_price_simple(base_price, base_date)

    return adjusted_price


def calculate_groceries_budget(
    preferences: Dict,
    city: str,
    historical_avg: float,
    use_ai: bool = True
) -> Dict:
    """
    Calculate Groceries budget based on user preferences

    Args:
        preferences: User's groceries preferences from category_preferences JSON
        city: User's city
        historical_avg: 6-month average spending on groceries
        use_ai: Whether to use AI for price adjustment

    Returns:
        {
            'suggested_amount': float,
            'breakdown': {...},
            'reasoning': str,
            'comparison_with_actual': str,
            'confidence': str
        }
    """
    consumption = preferences.get('consumption_items', {})
    diet_type = preferences.get('diet_type', 'vegetarian')  # Get diet preference

    if not consumption:
        # No consumption data - fallback to historical average
        return {
            'suggested_amount': round(historical_avg, 2) if historical_avg > 0 else 5000,
            'breakdown': {},
            'reasoning': 'Based on your historical spending average (consumption preferences not provided)',
            'comparison_with_actual': '',
            'confidence': 'low'
        }

    # Get current prices for common items
    rice_price = get_current_price(city, 'groceries.rice_per_kg', use_ai)
    wheat_price = get_current_price(city, 'groceries.wheat_per_kg', use_ai)
    veg_price = get_current_price(city, 'groceries.vegetables_per_kg_avg', use_ai)
    dairy_price = get_current_price(city, 'groceries.dairy_per_liter', use_ai)

    # Calculate costs
    rice_kg = consumption.get('rice_kg_per_month', 0)
    wheat_kg = consumption.get('wheat_kg_per_month', 0)
    veg_kg_week = consumption.get('vegetables_kg_per_week', 0)
    dairy_l_week = consumption.get('dairy_liters_per_week', 0)

    rice_cost = rice_kg * rice_price
    wheat_cost = wheat_kg * wheat_price
    veg_cost = veg_kg_week * 4.33 * veg_price  # 4.33 weeks/month
    dairy_cost = dairy_l_week * 4.33 * dairy_price

    # Only calculate meat costs for non-vegetarian users (individual meat types)
    chicken_cost = 0
    mutton_cost = 0
    fish_cost = 0
    eggs_cost = 0

    if diet_type == 'non_vegetarian':
        # Chicken
        chicken_kg_week = consumption.get('chicken_kg_per_week', 0)
        if chicken_kg_week > 0:
            chicken_price = get_current_price(city, 'groceries.chicken_per_kg', use_ai)
            chicken_cost = chicken_kg_week * 4.33 * chicken_price

        # Mutton
        mutton_kg_week = consumption.get('mutton_kg_per_week', 0)
        if mutton_kg_week > 0:
            mutton_price = get_current_price(city, 'groceries.mutton_per_kg', use_ai)
            mutton_cost = mutton_kg_week * 4.33 * mutton_price

        # Fish
        fish_kg_week = consumption.get('fish_kg_per_week', 0)
        if fish_kg_week > 0:
            fish_price = get_current_price(city, 'groceries.fish_per_kg', use_ai)
            fish_cost = fish_kg_week * 4.33 * fish_price

        # Eggs
        eggs_dozen_week = consumption.get('eggs_dozen_per_week', 0)
        if eggs_dozen_week > 0:
            eggs_price = get_current_price(city, 'groceries.eggs_per_dozen', use_ai)
            eggs_cost = eggs_dozen_week * 4.33 * eggs_price

    # Subtotal (sum of all individual items)
    subtotal = rice_cost + wheat_cost + veg_cost + dairy_cost + chicken_cost + mutton_cost + fish_cost + eggs_cost

    # Add buffer for other items (spices, oil, condiments, snacks) - 20%
    other_items = subtotal * 0.20

    total = subtotal + other_items

    # Build breakdown
    breakdown = {}
    if rice_cost > 0:
        breakdown['rice'] = round(rice_cost, 2)
    if wheat_cost > 0:
        breakdown['wheat'] = round(wheat_cost, 2)
    if veg_cost > 0:
        breakdown['vegetables'] = round(veg_cost, 2)
    if dairy_cost > 0:
        breakdown['dairy'] = round(dairy_cost, 2)

    # Individual meat types in breakdown
    if chicken_cost > 0:
        breakdown['chicken'] = round(chicken_cost, 2)
    if mutton_cost > 0:
        breakdown['mutton'] = round(mutton_cost, 2)
    if fish_cost > 0:
        breakdown['fish'] = round(fish_cost, 2)
    if eggs_cost > 0:
        breakdown['eggs'] = round(eggs_cost, 2)

    breakdown['other_items'] = round(other_items, 2)

    # Generate reasoning
    diet_label = "Non-Vegetarian" if diet_type == 'non_vegetarian' else "Vegetarian"
    reasoning_parts = [f"Based on your {diet_label} consumption in {city}:"]
    if rice_kg > 0:
        reasoning_parts.append(f"• Rice: {rice_kg}kg × ₹{rice_price:.0f}/kg = ₹{rice_cost:.0f}")
    if wheat_kg > 0:
        reasoning_parts.append(f"• Wheat: {wheat_kg}kg × ₹{wheat_price:.0f}/kg = ₹{wheat_cost:.0f}")
    if veg_kg_week > 0:
        reasoning_parts.append(f"• Vegetables: {veg_kg_week}kg/week × ₹{veg_price:.0f}/kg = ₹{veg_cost:.0f}/month")
    if dairy_l_week > 0:
        reasoning_parts.append(f"• Dairy: {dairy_l_week}L/week × ₹{dairy_price:.0f}/L = ₹{dairy_cost:.0f}/month")

    # Show individual meat costs for non-vegetarian users (only if they consume them)
    if diet_type == 'non_vegetarian':
        chicken_kg_week = consumption.get('chicken_kg_per_week', 0)
        mutton_kg_week = consumption.get('mutton_kg_per_week', 0)
        fish_kg_week = consumption.get('fish_kg_per_week', 0)
        eggs_dozen_week = consumption.get('eggs_dozen_per_week', 0)

        if chicken_kg_week > 0:
            chicken_price = get_current_price(city, 'groceries.chicken_per_kg', use_ai)
            reasoning_parts.append(f"• Chicken: {chicken_kg_week}kg/week × ₹{chicken_price:.0f}/kg = ₹{chicken_cost:.0f}/month")

        if mutton_kg_week > 0:
            mutton_price = get_current_price(city, 'groceries.mutton_per_kg', use_ai)
            reasoning_parts.append(f"• Mutton: {mutton_kg_week}kg/week × ₹{mutton_price:.0f}/kg = ₹{mutton_cost:.0f}/month")

        if fish_kg_week > 0:
            fish_price = get_current_price(city, 'groceries.fish_per_kg', use_ai)
            reasoning_parts.append(f"• Fish: {fish_kg_week}kg/week × ₹{fish_price:.0f}/kg = ₹{fish_cost:.0f}/month")

        if eggs_dozen_week > 0:
            eggs_price = get_current_price(city, 'groceries.eggs_per_dozen', use_ai)
            reasoning_parts.append(f"• Eggs: {eggs_dozen_week} dozen/week × ₹{eggs_price:.0f}/dozen = ₹{eggs_cost:.0f}/month")

    reasoning_parts.append(f"• Other items (spices, oil, snacks - 20% buffer): ₹{other_items:.0f}")
    reasoning_parts.append(f"\nMarket prices for {city} ({datetime.now().strftime('%B %Y')})")

    reasoning = '\n'.join(reasoning_parts)

    # Compare with historical
    comparison = ""
    if historical_avg > 0:
        variance = ((total - historical_avg) / historical_avg) * 100
        if abs(variance) < 10:
            comparison = f"✓ Calculated budget (₹{total:.0f}) aligns well with your historical spending (₹{historical_avg:.0f})."
        elif variance > 10:
            comparison = f"⚠ Calculated budget (₹{total:.0f}) is {variance:.0f}% higher than your average (₹{historical_avg:.0f}). You may be underestimating consumption or getting better deals currently."
        else:
            comparison = f"💡 Calculated budget (₹{total:.0f}) is {abs(variance):.0f}% lower than your average (₹{historical_avg:.0f}). Consider if you're buying premium products or eating out more often."
    else:
        comparison = "No historical data available for comparison. Start tracking expenses for better insights!"

    return {
        'suggested_amount': round(total, 2),
        'breakdown': breakdown,
        'reasoning': reasoning,
        'comparison_with_actual': comparison,
        'confidence': 'high' if historical_avg > 0 else 'medium'
    }


def calculate_transport_budget(
    preferences: Dict,
    city: str,
    historical_avg: float,
    use_ai: bool = True
) -> Dict:
    """
    Calculate Transport budget based on user preferences

    Args:
        preferences: User's transport preferences
        city: User's city
        historical_avg: 6-month average spending on transport
        use_ai: Whether to use AI for price adjustment

    Returns:
        Budget calculation dict
    """
    mode = preferences.get('mode', 'own_vehicle')

    if not mode:
        # Fallback to historical
        return {
            'suggested_amount': round(historical_avg, 2) if historical_avg > 0 else 3000,
            'breakdown': {},
            'reasoning': 'Based on your historical spending average (transport preferences not provided)',
            'comparison_with_actual': '',
            'confidence': 'low'
        }

    total = 0
    breakdown = {}
    reasoning_parts = [f"Based on your transport usage in {city}:"]

    # Own vehicle calculation
    if mode in ['own_vehicle', 'mixed']:
        fuel_type = preferences.get('fuel_type', 'petrol')
        km_per_month = preferences.get('avg_km_per_month', 0)
        vehicle_type = preferences.get('vehicle_type', 'car')

        if km_per_month > 0:
            # Get fuel price
            fuel_price = get_current_price(city, f'transport.{fuel_type}_per_liter', use_ai)

            # Mileage assumptions (km per liter)
            mileage_map = {
                'bike': 40,
                'scooter': 45,
                'car': 15 if fuel_type == 'petrol' else 18
            }
            mileage = mileage_map.get(vehicle_type, 20)

            # Calculate fuel cost
            fuel_liters = km_per_month / mileage
            fuel_cost = fuel_liters * fuel_price

            # Maintenance (5% of fuel cost as estimate)
            maintenance = fuel_cost * 0.05

            total += fuel_cost + maintenance
            breakdown['fuel'] = round(fuel_cost, 2)
            breakdown['maintenance'] = round(maintenance, 2)

            reasoning_parts.append(
                f"• {fuel_type.capitalize()}: {km_per_month}km ÷ {mileage}km/L × ₹{fuel_price:.0f}/L = ₹{fuel_cost:.0f}"
            )
            reasoning_parts.append(f"• Maintenance: ₹{maintenance:.0f}")

    # Public transport calculation
    if mode in ['public_transport', 'mixed']:
        pt = preferences.get('public_transport', {})

        if pt.get('uses_metro'):
            metro_cost = pt.get('metro_monthly_cost', 0)
            if metro_cost > 0:
                total += metro_cost
                breakdown['metro'] = metro_cost
                reasoning_parts.append(f"• Metro pass: ₹{metro_cost}")

        if pt.get('uses_bus'):
            bus_cost = pt.get('bus_monthly_cost', 0)
            if bus_cost > 0:
                total += bus_cost
                breakdown['bus'] = bus_cost
                reasoning_parts.append(f"• Bus pass: ₹{bus_cost}")

    reasoning = '\n'.join(reasoning_parts)

    # Compare with historical
    comparison = ""
    if historical_avg > 0:
        variance = ((total - historical_avg) / historical_avg) * 100
        if abs(variance) < 15:
            comparison = f"✓ Calculated budget (₹{total:.0f}) matches your historical spending (₹{historical_avg:.0f})."
        else:
            comparison = f"Calculated budget (₹{total:.0f}) differs by {variance:+.0f}% from your average (₹{historical_avg:.0f})."
    else:
        comparison = "No historical data available. This budget is based on your stated usage patterns."

    return {
        'suggested_amount': round(total, 2),
        'breakdown': breakdown,
        'reasoning': reasoning,
        'comparison_with_actual': comparison,
        'confidence': 'high'
    }


def calculate_generic_budget(
    category: str,
    historical_avg: float,
    trend: Optional[str] = None
) -> Dict:
    """
    Fallback calculator for categories without detailed preferences

    Args:
        category: Category name
        historical_avg: Historical average spending
        trend: 'increasing', 'decreasing', or None

    Returns:
        Budget calculation dict
    """
    if historical_avg == 0:
        # No data - provide reasonable defaults
        defaults = {
            'Entertainment': 2000,
            'Shopping': 3000,
            'Bills': 2500,
            'Healthcare': 1500,
            'Education': 2000,
            'Other': 1000
        }
        suggested = defaults.get(category, 1000)
        reasoning = f"No historical data available. Suggested default budget for {category}."
    else:
        # Use historical average with slight adjustment for trends
        if trend == 'increasing':
            suggested = historical_avg * 1.1  # 10% increase
            reasoning = f"Based on your 6-month average (₹{historical_avg:.0f}), adjusted upward by 10% due to increasing trend."
        elif trend == 'decreasing':
            suggested = historical_avg * 0.9  # 10% decrease
            reasoning = f"Based on your 6-month average (₹{historical_avg:.0f}), adjusted downward by 10% due to decreasing trend."
        else:
            suggested = historical_avg
            reasoning = f"Based on your 6-month average spending."

    return {
        'suggested_amount': round(suggested, 2),
        'breakdown': {},
        'reasoning': reasoning,
        'comparison_with_actual': f"Historical average: ₹{historical_avg:.0f}" if historical_avg > 0 else "",
        'confidence': 'medium' if historical_avg > 0 else 'low'
    }


def estimate_custom_activity_cost(activity_name: str, city: str = "Bangalore") -> float:
    """
    Use AI to estimate the typical cost per visit for custom entertainment activities

    Args:
        activity_name: Name of the activity (e.g., "Go-karting", "Arcade", "Bowling")
        city: City name for location-based pricing

    Returns:
        Estimated cost per visit in rupees
    """
    try:
        from groq import Groq
        import os

        client = Groq(api_key=os.getenv('GROQ_API_KEY'))

        prompt = f"""You are a pricing expert for entertainment activities in India.

Activity: {activity_name}
City: {city}

Provide the typical cost per person per visit for this activity in {city}, India.
Consider:
- Entry fees or per-game/per-hour charges
- Typical duration of visit
- Average pricing in Indian metros
- Any standard packages or deals

Respond with ONLY a number (the cost in rupees). No explanation, just the number.
Example responses: 500, 1200, 300

Your response:"""

        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3,  # Low temperature for consistent pricing
            max_tokens=10
        )

        cost_str = completion.choices[0].message.content.strip()
        # Extract number from response
        cost = float(''.join(filter(str.isdigit, cost_str)))

        # Sanity check (₹50 to ₹5000 per visit)
        if cost < 50:
            cost = 500  # Default minimum
        elif cost > 5000:
            cost = 2000  # Default maximum

        print(f"AI estimated cost for '{activity_name}' in {city}: ₹{cost}")
        return cost

    except Exception as e:
        print(f"Error estimating activity cost: {e}")
        # Fallback to reasonable default
        return 500.0


def calculate_entertainment_budget(
    preferences: Dict,
    city: str,
    historical_avg: float,
    use_ai: bool = True
) -> Dict:
    """
    Calculate Entertainment budget including subscriptions and custom activities

    Args:
        preferences: User's entertainment preferences
        city: User's city
        historical_avg: Historical average spending
        use_ai: Whether to use AI for cost estimation

    Returns:
        Budget calculation dict
    """
    total = 0
    breakdown = {}
    reasoning_parts = ["Based on your entertainment preferences:"]

    # Streaming subscriptions
    subscriptions = preferences.get('subscriptions', [])
    subscription_costs = {
        'netflix': 649,
        'prime_video': 299,
        'hotstar': 299,
        'spotify': 119,
        'youtube_premium': 129,
        'zee5': 99,
        'sony_liv': 299
    }

    subscription_total = sum(subscription_costs.get(sub, 0) for sub in subscriptions)
    if subscription_total > 0:
        total += subscription_total
        breakdown['subscriptions'] = subscription_total
        sub_names = ', '.join([sub.replace('_', ' ').title() for sub in subscriptions])
        reasoning_parts.append(f"• Subscriptions ({sub_names}): ₹{subscription_total}")

    # Standard activities (estimate 2 visits per month)
    activities = preferences.get('activities', {})
    activity_costs = {
        'movies': 300,  # Average movie ticket
        'dining': 800,  # Dining out per visit
        'sports': 1500,  # Gym/sports membership
        'hobbies': 1000  # Classes/hobbies
    }

    for activity_id, enabled in activities.items():
        if enabled:
            cost = activity_costs.get(activity_id, 500) * 2  # 2 visits per month
            total += cost
            breakdown[activity_id] = cost
            reasoning_parts.append(f"• {activity_id.capitalize()}: ₹{cost}/month")

    # Custom activities with AI estimation
    custom_activities = preferences.get('custom_activities', [])
    if custom_activities and use_ai:
        custom_total = 0
        custom_breakdown = []

        for activity in custom_activities:
            estimated_cost_per_visit = estimate_custom_activity_cost(activity, city)
            # Assume 2 visits per month for custom activities
            monthly_cost = estimated_cost_per_visit * 2
            custom_total += monthly_cost
            custom_breakdown.append(f"{activity}: ₹{estimated_cost_per_visit}/visit")

        if custom_total > 0:
            total += custom_total
            breakdown['custom_activities'] = custom_total
            reasoning_parts.append(f"• Custom activities (AI-estimated, 2 visits/month): ₹{custom_total}")
            reasoning_parts.append(f"  Details: {', '.join(custom_breakdown)}")

    # User-specified budget (if provided, use as cap)
    user_budget = preferences.get('monthly_entertainment_budget', 0)
    if user_budget > 0 and total > user_budget:
        reasoning_parts.append(f"\n⚠ Calculated total (₹{total}) exceeds your budget (₹{user_budget}). Consider prioritizing activities.")

    # If nothing configured, fallback to historical or default
    if total == 0:
        if historical_avg > 0:
            total = historical_avg
            reasoning_parts = [f"Based on your historical average spending: ₹{historical_avg:.0f}"]
        else:
            total = 2000
            reasoning_parts = ["No preferences configured. Suggested default entertainment budget."]

    reasoning = '\n'.join(reasoning_parts)

    # Compare with historical
    comparison = ""
    if historical_avg > 0:
        variance = ((total - historical_avg) / historical_avg) * 100
        if abs(variance) < 15:
            comparison = f"✓ Aligns with your historical spending (₹{historical_avg:.0f})."
        else:
            comparison = f"Differs by {variance:+.0f}% from your average (₹{historical_avg:.0f})."

    return {
        'suggested_amount': round(total, 2),
        'breakdown': breakdown,
        'reasoning': reasoning,
        'comparison_with_actual': comparison,
        'confidence': 'high' if (subscriptions or activities or custom_activities) else 'medium'
    }


def calculate_bills_budget(
    preferences: Dict,
    city: str,
    historical_avg: float
) -> Dict:
    """
    Calculate Bills budget based on user's fixed expenses

    Args:
        preferences: User's bills preferences
        city: User's city
        historical_avg: Historical average spending

    Returns:
        Budget calculation dict
    """
    total = 0
    breakdown = {}
    reasoning_parts = ["Based on your fixed monthly bills:"]

    # Rent
    has_rent = preferences.get('has_rent', False)
    if has_rent:
        rent = preferences.get('rent', 0)
        if rent > 0:
            total += rent
            breakdown['rent'] = rent
            reasoning_parts.append(f"• Rent: ₹{rent}")

    # Utilities
    utilities = ['electricity', 'water', 'internet', 'gas', 'phone', 'other_bills']
    for util in utilities:
        cost = preferences.get(util, 0)
        if cost > 0:
            total += cost
            breakdown[util] = cost
            reasoning_parts.append(f"• {util.replace('_', ' ').capitalize()}: ₹{cost}")

    # If nothing configured, fallback
    if total == 0:
        if historical_avg > 0:
            total = historical_avg
            reasoning_parts = [f"Based on your historical average: ₹{historical_avg:.0f}"]
        else:
            total = 2500
            reasoning_parts = ["No bills configured. Suggested default budget."]

    reasoning = '\n'.join(reasoning_parts)

    # Compare with historical
    comparison = ""
    if historical_avg > 0 and breakdown:
        variance = ((total - historical_avg) / historical_avg) * 100
        if abs(variance) < 10:
            comparison = f"✓ Fixed bills match historical spending (₹{historical_avg:.0f})."
        else:
            comparison = f"Fixed bills differ by {variance:+.0f}% from average (₹{historical_avg:.0f})."

    return {
        'suggested_amount': round(total, 2),
        'breakdown': breakdown,
        'reasoning': reasoning,
        'comparison_with_actual': comparison,
        'confidence': 'high' if breakdown else 'low'
    }
