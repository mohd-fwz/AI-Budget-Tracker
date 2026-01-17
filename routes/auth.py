"""
Authentication Routes
Handles user registration, login, token refresh, and profile retrieval
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import (
    create_access_token,
    create_refresh_token,
    jwt_required,
    get_jwt_identity
)
from datetime import datetime, timedelta
from models import db, User, UserProfile, PasswordResetToken
from utils.auth_helpers import require_auth
import re
import uuid

auth_bp = Blueprint('auth', __name__)


def validate_email(email):
    """Validate email format"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None


def validate_password_strength(password):
    """
    Validate password strength
    Requirements: At least 8 characters, 1 uppercase, 1 lowercase, 1 number
    """
    if len(password) < 8:
        return False, "Password must be at least 8 characters long"

    if not re.search(r'[A-Z]', password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r'[a-z]', password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r'[0-9]', password):
        return False, "Password must contain at least one number"

    return True, "Password is strong"


@auth_bp.route('/api/auth/register', methods=['POST'])
def register():
    """
    Register a new user

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123",
            "name": "John Doe" (optional)
        }

    Returns:
        {
            "message": "Registration successful",
            "user": {...},
            "tokens": {
                "access": "...",
                "refresh": "..."
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')
        name = data.get('name', '').strip()

        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Validate password strength
        is_strong, message = validate_password_strength(password)
        if not is_strong:
            return jsonify({'error': message}), 400

        # Check if user already exists
        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            return jsonify({'error': 'Email already registered'}), 409

        # Create new user
        new_user = User()
        new_user.email = email
        new_user.set_password(password)
        new_user.name = name if name else None

        db.session.add(new_user)
        db.session.flush()  # Get user.id before commit

        # Create user profile
        new_profile = UserProfile(user_id=new_user.id)
        db.session.add(new_profile)

        db.session.commit()

        # Generate JWT tokens
        access_token = create_access_token(identity=new_user.id)
        refresh_token = create_refresh_token(identity=new_user.id)

        return jsonify({
            'message': 'Registration successful',
            'user': new_user.to_dict(),
            'tokens': {
                'access': access_token,
                'refresh': refresh_token
            }
        }), 201

    except Exception as e:
        db.session.rollback()
        print(f"Registration error: {e}")
        return jsonify({'error': 'Registration failed. Please try again.'}), 500


@auth_bp.route('/api/auth/login', methods=['POST'])
def login():
    """
    Login user and return JWT tokens

    Request Body:
        {
            "email": "user@example.com",
            "password": "SecurePass123"
        }

    Returns:
        {
            "message": "Login successful",
            "user": {...},
            "profile": {...},
            "tokens": {
                "access": "...",
                "refresh": "..."
            }
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()
        password = data.get('password', '')

        # Validate required fields
        if not email or not password:
            return jsonify({'error': 'Email and password are required'}), 400

        # Find user by email
        user = User.query.filter_by(email=email).first()

        if not user or not user.check_password(password):
            return jsonify({'error': 'Invalid email or password'}), 401

        # Check if account is active
        if not user.is_active:
            return jsonify({'error': 'Account is disabled'}), 403

        # Update last login
        user.last_login = datetime.utcnow()
        db.session.commit()

        # Get user profile
        profile = UserProfile.query.filter_by(user_id=user.id).first()

        # Generate JWT tokens
        access_token = create_access_token(identity=user.id)
        refresh_token = create_refresh_token(identity=user.id)

        return jsonify({
            'message': 'Login successful',
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None,
            'tokens': {
                'access': access_token,
                'refresh': refresh_token
            }
        }), 200

    except Exception as e:
        print(f"Login error: {e}")
        return jsonify({'error': 'Login failed. Please try again.'}), 500


@auth_bp.route('/api/auth/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """
    Refresh access token using refresh token

    Headers:
        Authorization: Bearer <refresh_token>

    Returns:
        {
            "access_token": "..."
        }
    """
    try:
        current_user_id = get_jwt_identity()

        # Verify user still exists and is active
        user = User.query.filter_by(id=current_user_id).first()

        if not user or not user.is_active:
            return jsonify({'error': 'Invalid user'}), 401

        # Generate new access token
        access_token = create_access_token(identity=current_user_id)

        return jsonify({
            'access_token': access_token
        }), 200

    except Exception as e:
        print(f"Token refresh error: {e}")
        return jsonify({'error': 'Token refresh failed'}), 500


@auth_bp.route('/api/auth/user', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current user information

    Headers:
        Authorization: Bearer <access_token>

    Returns:
        {
            "user": {...},
            "profile": {...}
        }
    """
    try:
        from flask import g
        user_id = g.user_id

        # Get user and profile
        user = User.query.filter_by(id=user_id).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        profile = UserProfile.query.filter_by(user_id=user_id).first()

        return jsonify({
            'user': user.to_dict(),
            'profile': profile.to_dict() if profile else None
        }), 200

    except Exception as e:
        print(f"Get user error: {e}")
        return jsonify({'error': 'Failed to get user information'}), 500


@auth_bp.route('/api/auth/change-password', methods=['PUT'])
@require_auth
def change_password():
    """
    Change user password

    Request Body:
        {
            "current_password": "OldPass123",
            "new_password": "NewPass123"
        }

    Returns:
        {
            "message": "Password changed successfully"
        }
    """
    try:
        from flask import g
        user_id = g.user_id
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        current_password = data.get('current_password', '')
        new_password = data.get('new_password', '')

        # Validate required fields
        if not current_password or not new_password:
            return jsonify({'error': 'Current password and new password are required'}), 400

        # Get user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify current password
        if not user.check_password(current_password):
            return jsonify({'error': 'Current password is incorrect'}), 401

        # Validate new password strength
        is_strong, message = validate_password_strength(new_password)
        if not is_strong:
            return jsonify({'error': message}), 400

        # Check if new password is same as current
        if current_password == new_password:
            return jsonify({'error': 'New password must be different from current password'}), 400

        # Update password
        user.set_password(new_password)
        db.session.commit()

        return jsonify({
            'message': 'Password changed successfully'
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Change password error: {e}")
        return jsonify({'error': 'Failed to change password'}), 500


@auth_bp.route('/api/auth/change-email', methods=['PUT'])
@require_auth
def change_email():
    """
    Change user email

    Request Body:
        {
            "new_email": "newemail@example.com",
            "password": "UserPass123"
        }

    Returns:
        {
            "message": "Email changed successfully",
            "user": {...}
        }
    """
    try:
        from flask import g
        user_id = g.user_id
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        new_email = data.get('new_email', '').strip().lower()
        password = data.get('password', '')

        # Validate required fields
        if not new_email or not password:
            return jsonify({'error': 'New email and password are required'}), 400

        # Validate email format
        if not validate_email(new_email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Get user
        user = User.query.filter_by(id=user_id).first()
        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Verify password
        if not user.check_password(password):
            return jsonify({'error': 'Password is incorrect'}), 401

        # Check if email is same as current
        if new_email == user.email:
            return jsonify({'error': 'New email must be different from current email'}), 400

        # Check if email already exists
        existing_user = User.query.filter_by(email=new_email).first()
        if existing_user:
            return jsonify({'error': 'Email already in use'}), 409

        # Update email
        user.email = new_email
        db.session.commit()

        return jsonify({
            'message': 'Email changed successfully',
            'user': user.to_dict()
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Change email error: {e}")
        return jsonify({'error': 'Failed to change email'}), 500


@auth_bp.route('/api/auth/forgot-password', methods=['POST'])
def forgot_password():
    """
    Request password reset - generates token and provides reset link

    Note: For development/testing, this returns the reset token directly.
    In production, this would send an email with a reset link.

    Request Body:
        {
            "email": "user@example.com"
        }

    Returns:
        {
            "message": "Password reset instructions sent",
            "reset_token": "..." (dev only)
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        email = data.get('email', '').strip().lower()

        if not email:
            return jsonify({'error': 'Email is required'}), 400

        # Validate email format
        if not validate_email(email):
            return jsonify({'error': 'Invalid email format'}), 400

        # Find user by email
        user = User.query.filter_by(email=email).first()

        # Always return success message (don't reveal if email exists)
        # This prevents email enumeration attacks
        response_message = "If an account with this email exists, password reset instructions have been sent."

        if user:
            # Generate unique reset token
            reset_token = str(uuid.uuid4())

            # Token expires in 1 hour
            expires_at = datetime.utcnow() + timedelta(hours=1)

            # Invalidate any existing unused tokens for this user
            existing_tokens = PasswordResetToken.query.filter_by(
                user_id=user.id,
                used=0
            ).all()

            for token in existing_tokens:
                token.mark_as_used()

            # Create new reset token
            new_token = PasswordResetToken(
                user_id=user.id,
                token=reset_token,
                expires_at=expires_at
            )

            db.session.add(new_token)
            db.session.commit()

            # In production, send email with reset link here
            # For development, return the token directly
            print(f"Password reset token for {email}: {reset_token}")

            return jsonify({
                'message': response_message,
                'reset_token': reset_token,  # Remove this in production
                'dev_note': 'In production, this token would be sent via email'
            }), 200

        # Even if user doesn't exist, return success to prevent enumeration
        return jsonify({
            'message': response_message
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Forgot password error: {e}")
        return jsonify({'error': 'Failed to process request'}), 500


@auth_bp.route('/api/auth/reset-password', methods=['POST'])
def reset_password():
    """
    Reset password using valid reset token

    Request Body:
        {
            "token": "reset-token-uuid",
            "new_password": "NewPass123"
        }

    Returns:
        {
            "message": "Password reset successfully"
        }
    """
    try:
        data = request.get_json()

        if not data:
            return jsonify({'error': 'No data provided'}), 400

        token = data.get('token', '').strip()
        new_password = data.get('new_password', '')

        # Validate required fields
        if not token or not new_password:
            return jsonify({'error': 'Token and new password are required'}), 400

        # Validate new password strength
        is_strong, message = validate_password_strength(new_password)
        if not is_strong:
            return jsonify({'error': message}), 400

        # Find reset token
        reset_token = PasswordResetToken.query.filter_by(token=token).first()

        if not reset_token:
            return jsonify({'error': 'Invalid or expired reset token'}), 400

        # Check if token is valid (not expired and not used)
        if not reset_token.is_valid():
            return jsonify({'error': 'Invalid or expired reset token'}), 400

        # Get user
        user = User.query.filter_by(id=reset_token.user_id).first()

        if not user:
            return jsonify({'error': 'User not found'}), 404

        # Update password
        user.set_password(new_password)

        # Mark token as used
        reset_token.mark_as_used()

        db.session.commit()

        return jsonify({
            'message': 'Password reset successfully. You can now login with your new password.'
        }), 200

    except Exception as e:
        db.session.rollback()
        print(f"Reset password error: {e}")
        return jsonify({'error': 'Failed to reset password'}), 500
