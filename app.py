"""
Main Flask application for Budget API
Budgeting feature API with expense tracking, analytics, and AI recommendations
"""
from flask import Flask, jsonify
from flask_cors import CORS
from flask_jwt_extended import JWTManager
import logging
import sys

from config import Config
from models import db, init_db

# Import route blueprints
from routes.expenses import expenses_bp
from routes.analytics import analytics_bp
from routes.recommendations import recommendations_bp
from routes.profiles import profiles_bp
from routes.budgets import budgets_bp
from routes.auth import auth_bp


def create_app():
    """
    Application factory pattern
    Creates and configures the Flask application
    """
    # Initialize Flask app
    app = Flask(__name__)

    # Load configuration
    app.config.from_object(Config)

    # Configure logging
    logging.basicConfig(
        level=getattr(logging, Config.LOG_LEVEL),
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    logger = logging.getLogger(__name__)

    # Validate configuration
    try:
        Config.validate_config()
        logger.info("Configuration validated successfully")
    except ValueError as e:
        logger.error(f"Configuration error: {str(e)}")
        logger.warning("Application starting with invalid configuration - some features may not work")

    # Enable CORS
    CORS(app, origins=Config.CORS_ORIGINS, supports_credentials=True)
    logger.info(f"CORS enabled for origins: {Config.CORS_ORIGINS}")

    # Initialize JWT
    jwt = JWTManager(app)
    logger.info("JWT authentication initialized")

    # Initialize database
    try:
        init_db(app)
        logger.info("Database initialized successfully")
    except Exception as e:
        logger.error(f"Database initialization error: {str(e)}")

    # Register blueprints
    app.register_blueprint(auth_bp)
    app.register_blueprint(expenses_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(recommendations_bp)
    app.register_blueprint(profiles_bp)
    app.register_blueprint(budgets_bp)
    logger.info("Route blueprints registered")

    # Health check endpoint
    @app.route('/health', methods=['GET'])
    def health_check():
        """
        Health check endpoint for monitoring
        Tests database connectivity
        """
        try:
            # Test database connection
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))
            db_status = 'healthy'
        except Exception as e:
            db_status = f'unhealthy: {str(e)}'

        return jsonify({
            'status': 'healthy' if db_status == 'healthy' else 'degraded',
            'service': 'budget-api',
            'database': db_status,
            'version': '1.0.0'
        }), 200 if db_status == 'healthy' else 503

    # Root endpoint
    @app.route('/', methods=['GET'])
    def root():
        """
        API information endpoint
        """
        return jsonify({
            'name': 'Budget API',
            'version': '1.0.0',
            'description': 'Personal finance tracking API with AI-powered insights',
            'endpoints': {
                'health': '/health',
                'expenses': {
                    'add': 'POST /api/expenses',
                    'list': 'GET /api/expenses/<user_id>',
                    'delete': 'DELETE /api/expenses/<id>',
                    'upload': 'POST /api/upload-statement'
                },
                'analytics': 'GET /api/analytics/<user_id>',
                'recommendations': 'GET /api/recommendations/<user_id>'
            },
            'documentation': 'See README.md for full API documentation'
        }), 200

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        """Handle 404 errors"""
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource does not exist'
        }), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors"""
        logger.error(f"Internal server error: {str(error)}")
        db.session.rollback()  # Rollback any pending transactions
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error occurred'
        }), 500

    @app.errorhandler(413)
    def request_entity_too_large(error):
        """Handle file too large errors"""
        return jsonify({
            'error': 'File Too Large',
            'message': f'Maximum file size is {Config.MAX_CONTENT_LENGTH / 1024 / 1024}MB'
        }), 413

    logger.info("Budget API application created successfully")
    return app


# Create the application instance
app = create_app()


if __name__ == '__main__':
    """
    Development server
    For production, use gunicorn: gunicorn app:app
    """
    import os

    # Development mode
    debug_mode = os.getenv('DEBUG', 'False').lower() == 'true'

    print("=" * 60)
    print("Budget API Server")
    print("=" * 60)
    print(f"Environment: {'Development' if debug_mode else 'Production'}")
    print(f"Debug mode: {debug_mode}")
    print("=" * 60)

    app.run(
        host='0.0.0.0',
        port=int(os.getenv('PORT', 5000)),
        debug=debug_mode
    )
