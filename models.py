"""
Database models for Budget API
Uses SQLAlchemy ORM with Supabase PostgreSQL
"""
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Column, Integer, String, Numeric, DateTime, Text, Index
import uuid
import bcrypt

# Initialize SQLAlchemy instance
db = SQLAlchemy()


class User(db.Model):
    """
    User model for authentication

    Columns:
        id: Primary key (UUID string)
        email: User email (unique)
        password_hash: Hashed password
        name: User's full name
        created_at: Account creation timestamp
        last_login: Last login timestamp
        is_active: Account status (1=active, 0=inactive)
    """
    __tablename__ = 'users'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    name = Column(String(100), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    is_active = Column(Integer, default=1, nullable=False)

    def set_password(self, password):
        """Hash and set password"""
        self.password_hash = bcrypt.hashpw(
            password.encode('utf-8'),
            bcrypt.gensalt()
        ).decode('utf-8')

    def check_password(self, password):
        """Verify password against hash"""
        return bcrypt.checkpw(
            password.encode('utf-8'),
            self.password_hash.encode('utf-8')
        )

    def to_dict(self):
        """Convert user object to dictionary (excludes password)"""
        return {
            'id': self.id,
            'email': self.email,
            'name': self.name,
            'created_at': self.created_at.isoformat(),
            'last_login': self.last_login.isoformat() if self.last_login else None,
            'is_active': bool(self.is_active)
        }

    def __repr__(self):
        return f'<User {self.email}>'


class Expense(db.Model):
    """
    Expense model representing individual user expenses

    Columns:
        id: Primary key
        user_id: UUID from Supabase Auth (string format)
        amount: Expense amount (decimal precision for currency)
        category: Expense category (Groceries, Entertainment, etc.)
        date: Date of the expense
        description: Optional description of the expense
        payment_method: Payment method (UPI, NEFT, IMPS, RTGS, ATM, Card, Cheque, Cash)
        upi_id: UPI ID if transaction was via UPI (e.g., merchant@paytm)
        transaction_ref: Bank transaction reference ID
        merchant_id: Foreign key to Merchant table (for linked merchants)
        created_at: Timestamp when record was created
    """
    __tablename__ = 'expenses'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    amount = Column(Numeric(10, 2), nullable=False)  # e.g., 1234567.89
    category = Column(String(100), nullable=False, index=True)
    date = Column(DateTime, nullable=False, index=True)
    description = Column(Text, nullable=True)

    # Transaction parsing fields (NEW)
    payment_method = Column(String(50), nullable=True, index=True)  # UPI, NEFT, IMPS, etc.
    upi_id = Column(String(255), nullable=True)  # e.g., merchant@paytm
    transaction_ref = Column(String(255), nullable=True)  # Bank reference ID
    merchant_id = Column(Integer, nullable=True)  # Foreign key to Merchant table

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # Composite indexes for common query patterns
    __table_args__ = (
        Index('idx_user_date', 'user_id', 'date'),
        Index('idx_user_category', 'user_id', 'category'),
        Index('idx_payment_method', 'payment_method'),
        Index('idx_merchant_id', 'merchant_id'),
    )

    def to_dict(self):
        """Convert expense object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'amount': float(self.amount),
            'category': self.category,
            'date': self.date.isoformat(),
            'description': self.description,
            'payment_method': self.payment_method,
            'upi_id': self.upi_id,
            'transaction_ref': self.transaction_ref,
            'merchant_id': self.merchant_id,
            'created_at': self.created_at.isoformat()
        }

    def __repr__(self):
        return f'<Expense {self.id}: {self.category} - ${self.amount}>'


class Merchant(db.Model):
    """
    Merchant model for tracking unique merchants identified from transactions

    This model stores merchant information extracted from UPI IDs, transaction descriptions,
    and other payment details. Helps build a database of known merchants for better
    categorization and insights.

    Columns:
        id: Primary key
        user_id: User who first encountered this merchant
        name: Merchant display name (normalized)
        upi_handles: Comma-separated list of UPI handles (e.g., "swiggy@paytm,swiggy.food@paytm")
        default_category: Most common category for this merchant
        transaction_count: Number of transactions with this merchant
        created_at: When merchant was first added
        updated_at: When merchant was last updated
    """
    __tablename__ = 'merchants'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    upi_handles = Column(Text, nullable=True)  # Comma-separated UPI handles
    default_category = Column(String(100), nullable=True)
    transaction_count = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Index for fast merchant lookup
    __table_args__ = (
        Index('idx_merchant_name', 'user_id', 'name'),
        Index('idx_merchant_upi', 'user_id', 'upi_handles'),
    )

    def add_upi_handle(self, upi_id):
        """Add a new UPI handle to this merchant if not already present"""
        if not upi_id:
            return

        current_handles = self.upi_handles.split(',') if self.upi_handles else []
        if upi_id not in current_handles:
            current_handles.append(upi_id)
            self.upi_handles = ','.join(current_handles)

    def get_upi_handles(self):
        """Get list of UPI handles for this merchant"""
        return self.upi_handles.split(',') if self.upi_handles else []

    def to_dict(self):
        """Convert merchant object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'name': self.name,
            'upi_handles': self.get_upi_handles(),
            'default_category': self.default_category,
            'transaction_count': self.transaction_count,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Merchant {self.name} ({self.transaction_count} transactions)>'


class MerchantCategoryMapping(db.Model):
    """
    Merchant Category Mapping model for learning user preferences

    Stores learned associations between merchants/descriptions and categories.
    When a user categorizes a transaction, the mapping is saved here.
    Future transactions from the same merchant will automatically use this category.

    Columns:
        id: Primary key
        user_id: User identifier (same format as Expense.user_id)
        merchant_name: Normalized merchant/description name
        category: Learned category for this merchant
        confidence: Number of times this mapping was confirmed (higher = more reliable)
        created_at: When this mapping was first created
        updated_at: When this mapping was last updated/confirmed
    """
    __tablename__ = 'merchant_category_mapping'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    merchant_name = Column(String(255), nullable=False)
    category = Column(String(100), nullable=False)
    confidence = Column(Integer, default=1, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Composite unique constraint and index for fast lookups
    __table_args__ = (
        Index('idx_merchant_lookup', 'user_id', 'merchant_name', unique=True),
    )

    def to_dict(self):
        """Convert mapping object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'merchant_name': self.merchant_name,
            'category': self.category,
            'confidence': self.confidence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<MerchantMapping {self.merchant_name} -> {self.category} (confidence: {self.confidence})>'


class Budget(db.Model):
    """
    Budget model for tracking monthly category-wise budgets

    Allows users to set budgets for each category and month.
    System can provide AI-powered recommendations based on historical data and market trends.

    Columns:
        id: Primary key
        user_id: User identifier
        category: Budget category (same as Expense categories)
        month: Budget month (YYYY-MM format)
        amount: Budgeted amount for this category
        is_ai_suggested: Whether this was AI-generated or user-set
        created_at: When this budget was created
        updated_at: When this budget was last updated
    """
    __tablename__ = 'budgets'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(255), nullable=False, index=True)
    category = Column(String(100), nullable=False)
    month = Column(String(7), nullable=False)  # YYYY-MM format
    amount = Column(Numeric(10, 2), nullable=False)
    is_ai_suggested = Column(Integer, default=0, nullable=False)  # 0=user-set, 1=AI-suggested
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Composite unique constraint - one budget per category per month per user
    __table_args__ = (
        Index('idx_budget_lookup', 'user_id', 'month', 'category', unique=True),
    )

    def to_dict(self):
        """Convert budget object to dictionary for JSON serialization"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'category': self.category,
            'month': self.month,
            'amount': float(self.amount),
            'is_ai_suggested': bool(self.is_ai_suggested),
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }

    def __repr__(self):
        return f'<Budget {self.month} {self.category}: ₹{self.amount}>'


class PasswordResetToken(db.Model):
    """
    Password Reset Token model for handling forgot password functionality

    Stores temporary tokens sent to users' emails for password reset.
    Tokens expire after a set time period for security.

    Columns:
        id: Primary key
        user_id: Reference to User.id
        token: Unique reset token (UUID)
        created_at: When token was created
        expires_at: When token expires
        used: Whether token has been used (0=unused, 1=used)
    """
    __tablename__ = 'password_reset_tokens'

    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(String(36), nullable=False, index=True)
    token = Column(String(255), unique=True, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    expires_at = Column(DateTime, nullable=False)
    used = Column(Integer, default=0, nullable=False)  # 0=unused, 1=used

    def is_valid(self):
        """Check if token is still valid (not expired and not used)"""
        return not self.used and datetime.utcnow() < self.expires_at

    def mark_as_used(self):
        """Mark token as used"""
        self.used = 1

    def to_dict(self):
        """Convert token object to dictionary"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'token': self.token,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'used': bool(self.used)
        }

    def __repr__(self):
        return f'<PasswordResetToken {self.token[:8]}... for user {self.user_id}>'


class UserProfile(db.Model):
    """
    User Profile model for storing user preferences and location

    Stores user's location (state/city) and financial information for personalized
    budget recommendations based on local market conditions, weather, and seasonal trends.

    Columns:
        user_id: Primary key (same as User.id)
        state: User's state in India
        city: User's city
        monthly_income: User's monthly income (optional)
        family_size: Number of people in family (default: 1)
        occupation: User's occupation (optional)
        age_group: Age group ('18-25', '26-35', '36-50', '50+')
        savings_goal: Monthly savings target (optional)
        category_preferences: JSON field storing detailed preferences per category
        created_at: When profile was created
        updated_at: When profile was last updated
    """
    __tablename__ = 'user_profiles'

    user_id = Column(String(255), primary_key=True)
    state = Column(String(100), nullable=True)
    city = Column(String(100), nullable=True)

    # Financial profile fields
    monthly_income = Column(Numeric(10, 2), nullable=True)
    family_size = Column(Integer, default=1, nullable=False)
    occupation = Column(String(100), nullable=True)
    age_group = Column(String(20), nullable=True)  # '18-25', '26-35', '36-50', '50+'
    savings_goal = Column(Numeric(10, 2), nullable=True)

    # Category preferences (JSON)
    category_preferences = Column(Text, nullable=True)  # Stores JSON

    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    @property
    def profile_completeness(self):
        """
        Calculate profile completeness percentage (0-100)

        Scoring:
        - Location (state + city): 15%
        - Monthly income: 15%
        - Family size: 10%
        - Savings goal: 10%
        - Each category preference: 10% (max 50% for 5 categories)

        Returns:
            int: Completeness percentage (0-100)
        """
        score = 0

        # Location
        if self.state and self.city:
            score += 15

        # Financial info
        if self.monthly_income:
            score += 15
        if self.family_size and self.family_size > 0:
            score += 10
        if self.savings_goal:
            score += 10

        # Category preferences
        if self.category_preferences:
            import json
            try:
                prefs = json.loads(self.category_preferences)
                # 10 points per configured category, max 50 points (5 categories)
                num_categories = len(prefs)
                score += min(num_categories * 10, 50)
            except:
                pass

        return min(score, 100)

    def get_category_preference(self, category):
        """
        Get preferences for a specific category

        Args:
            category: Category name (e.g., 'Groceries', 'Transport')

        Returns:
            dict: Category preferences or empty dict if not set
        """
        if not self.category_preferences:
            return {}

        import json
        try:
            prefs = json.loads(self.category_preferences)
            return prefs.get(category, {})
        except:
            return {}

    def set_category_preference(self, category, preferences):
        """
        Set preferences for a specific category

        Args:
            category: Category name
            preferences: Dictionary of preferences
        """
        import json

        # Load existing preferences
        if self.category_preferences:
            try:
                prefs = json.loads(self.category_preferences)
            except:
                prefs = {}
        else:
            prefs = {}

        # Update category
        prefs[category] = preferences

        # Save back as JSON
        self.category_preferences = json.dumps(prefs)

    def to_dict(self):
        """Convert profile object to dictionary for JSON serialization"""
        import json

        result = {
            'user_id': self.user_id,
            'state': self.state,
            'city': self.city,
            'monthly_income': float(self.monthly_income) if self.monthly_income else None,
            'family_size': self.family_size,
            'occupation': self.occupation,
            'age_group': self.age_group,
            'savings_goal': float(self.savings_goal) if self.savings_goal else None,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'profile_completeness': self.profile_completeness
        }

        # Parse category preferences
        if self.category_preferences:
            try:
                result['category_preferences'] = json.loads(self.category_preferences)
            except:
                result['category_preferences'] = {}
        else:
            result['category_preferences'] = {}

        return result

    def __repr__(self):
        return f'<UserProfile {self.user_id}: {self.city}, {self.state} ({self.profile_completeness}% complete)>'


# Valid expense categories
EXPENSE_CATEGORIES = [
    'Groceries',
    'Entertainment',
    'Rent',
    'Transport',
    'Bills',
    'Shopping',
    'Healthcare',
    'Income',  # For credit transactions (deposits, refunds, etc.)
    'Other'
]


def init_db(app):
    """
    Initialize database with Flask app
    Creates all tables if they don't exist
    """
    db.init_app(app)

    with app.app_context():
        # Create all tables
        db.create_all()
        print("Database tables created successfully!")


def validate_category(category):
    """Validate if a category is in the allowed list"""
    return category in EXPENSE_CATEGORIES
