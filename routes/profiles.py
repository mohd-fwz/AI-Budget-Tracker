"""
User Profile routes
Manages user location and preferences for personalized recommendations
"""
from flask import Blueprint, request, jsonify, g
from models import db, UserProfile
from utils.indian_locations import get_all_states, get_cities_for_state, validate_location
from utils.auth_helpers import require_auth

# Create Blueprint for profile routes
profiles_bp = Blueprint('profiles', __name__)


@profiles_bp.route('/api/profile', methods=['GET'])
@require_auth
def get_profile():
    """
    Get user profile including location

    Returns:
        200: User profile data
        404: Profile not found (will create default)
    """
    try:
        user_id = g.user_id
        
        # Get or create profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            # Create default profile
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)
            db.session.commit()
        
        return jsonify({
            'profile': profile.to_dict(),
            'has_location': bool(profile.state and profile.city)
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch profile',
            'message': str(e)
        }), 500


@profiles_bp.route('/api/profile/location', methods=['PUT'])
@require_auth
def update_location():
    """
    Update user's location (state and city)

    Request JSON:
        {
            "state": "Karnataka",
            "city": "Bangalore"
        }

    Returns:
        200: Location updated successfully
        400: Invalid location data
    """
    try:
        user_id = g.user_id
        data = request.get_json()
        
        state = data.get('state')
        city = data.get('city')
        
        # Validate location
        if not state or not city:
            return jsonify({
                'error': 'Both state and city are required'
            }), 400
        
        if not validate_location(state, city):
            return jsonify({
                'error': 'Invalid location',
                'message': f'{city} is not a valid city in {state}'
            }), 400
        
        # Get or create profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()
        
        if not profile:
            profile = UserProfile(user_id=user_id, state=state, city=city)
            db.session.add(profile)
        else:
            profile.state = state
            profile.city = city
        
        db.session.commit()
        
        return jsonify({
            'message': 'Location updated successfully',
            'profile': profile.to_dict()
        }), 200
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update location',
            'message': str(e)
        }), 500


@profiles_bp.route('/api/locations/states', methods=['GET'])
def get_states():
    """
    Get list of all Indian states
    
    Returns:
        200: List of states
    """
    try:
        states = get_all_states()
        return jsonify({
            'states': states
        }), 200
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch states',
            'message': str(e)
        }), 500


@profiles_bp.route('/api/locations/cities/<state>', methods=['GET'])
def get_cities(state):
    """
    Get list of cities for a given state
    
    Args:
        state: State name
    
    Returns:
        200: List of cities
        404: State not found
    """
    try:
        cities = get_cities_for_state(state)
        
        if not cities:
            return jsonify({
                'error': 'State not found',
                'message': f'No data available for state: {state}'
            }), 404
        
        return jsonify({
            'state': state,
            'cities': cities
        }), 200
        
    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch cities',
            'message': str(e)
        }), 500


@profiles_bp.route('/api/profile/financial', methods=['PUT'])
@require_auth
def update_financial_profile():
    """
    Update user's financial profile information

    Request JSON:
        {
            "monthly_income": 50000,
            "family_size": 4,
            "occupation": "Software Engineer",
            "age_group": "26-35",
            "savings_goal": 10000
        }

    Returns:
        200: Profile updated successfully
        400: Invalid data
    """
    try:
        user_id = g.user_id
        data = request.get_json()

        # Get or create profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        # Update fields
        if 'monthly_income' in data:
            profile.monthly_income = data['monthly_income']

        if 'family_size' in data:
            family_size = data['family_size']
            if family_size and family_size > 0:
                profile.family_size = family_size
            else:
                return jsonify({'error': 'Family size must be greater than 0'}), 400

        if 'occupation' in data:
            profile.occupation = data['occupation']

        if 'age_group' in data:
            age_group = data['age_group']
            valid_groups = ['18-25', '26-35', '36-50', '50+']
            if age_group and age_group not in valid_groups:
                return jsonify({
                    'error': 'Invalid age group',
                    'message': f'Must be one of: {", ".join(valid_groups)}'
                }), 400
            profile.age_group = age_group

        if 'savings_goal' in data:
            profile.savings_goal = data['savings_goal']

        db.session.commit()

        return jsonify({
            'message': 'Financial profile updated successfully',
            'profile': profile.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update financial profile',
            'message': str(e)
        }), 500


@profiles_bp.route('/api/profile/category-preferences/<category>', methods=['GET'])
@require_auth
def get_category_preferences(category):
    """
    Get preferences for a specific category

    Args:
        category: Category name (Groceries, Transport, etc.)

    Returns:
        200: Category preferences
        404: Profile not found
    """
    try:
        user_id = g.user_id
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        if not profile:
            return jsonify({
                'error': 'Profile not found',
                'preferences': {}
            }), 404

        preferences = profile.get_category_preference(category)

        return jsonify({
            'category': category,
            'preferences': preferences
        }), 200

    except Exception as e:
        return jsonify({
            'error': 'Failed to fetch category preferences',
            'message': str(e)
        }), 500


@profiles_bp.route('/api/profile/category-preferences/<category>', methods=['PUT'])
@require_auth
def update_category_preferences(category):
    """
    Update preferences for a specific category

    Request JSON: Category-specific preferences
    Example for Groceries:
        {
            "diet_type": "vegetarian",
            "family_size": 4,
            "consumption_items": {
                "rice_kg_per_month": 10,
                "wheat_kg_per_month": 5,
                "vegetables_kg_per_week": 7,
                "dairy_liters_per_week": 14,
                "meat_kg_per_week": 0
            },
            "shopping_frequency": "weekly"
        }

    Example for Transport:
        {
            "mode": "own_vehicle",
            "vehicle_type": "car",
            "fuel_type": "petrol",
            "avg_km_per_month": 500,
            "public_transport": {
                "uses_metro": false,
                "uses_bus": false
            }
        }

    Returns:
        200: Preferences updated successfully
        400: Invalid data
    """
    try:
        user_id = g.user_id
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No preferences provided'}), 400

        # Get or create profile
        profile = UserProfile.query.filter_by(user_id=user_id).first()

        if not profile:
            profile = UserProfile(user_id=user_id)
            db.session.add(profile)

        # Update category preferences
        profile.set_category_preference(category, data)

        db.session.commit()

        return jsonify({
            'message': f'{category} preferences updated successfully',
            'profile': profile.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        return jsonify({
            'error': 'Failed to update category preferences',
            'message': str(e)
        }), 500
