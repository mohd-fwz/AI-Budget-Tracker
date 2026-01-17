"""
Authentication Helper Functions
JWT token utilities and route protection decorators
"""
from functools import wraps
from flask import g, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity


def require_auth(f):
    """
    Decorator to protect routes - extracts user_id from JWT

    Usage:
        @app.route('/protected')
        @require_auth
        def protected_route():
            user_id = g.user_id
            return {'message': f'Hello {user_id}'}
    """
    @wraps(f)
    @jwt_required()
    def decorated(*args, **kwargs):
        current_user_id = get_jwt_identity()
        g.user_id = current_user_id
        return f(*args, **kwargs)
    return decorated


def get_current_user_id():
    """
    Get current user ID from Flask global context
    Must be called within a route protected by @require_auth

    Returns:
        str: User ID from JWT token
    """
    return getattr(g, 'user_id', None)
