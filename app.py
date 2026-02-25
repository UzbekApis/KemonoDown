"""
Kemono WebApp - Flask Application Entry Point
"""
import os
import sys
from flask import Flask, render_template, jsonify, request
from pathlib import Path

# Import configuration
from config import config

# Import database initialization
from models.database import init_db

# Import error handling and logging
from core.error_handler import (
    setup_logging, logger, handle_api_error, 
    APIError, ValidationError, log_request
)


def create_app():
    """Create and configure Flask application"""
    app = Flask(__name__)
    
    # Flask configuration
    app.config['SECRET_KEY'] = os.urandom(24)
    app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max upload
    app.config['JSON_AS_ASCII'] = False  # Support for UTF-8 in JSON
    
    # Setup logging
    log_level = config.get('log_level', 'INFO')
    setup_logging(log_level=getattr(__import__('logging'), log_level))
    logger.info("Kemono WebApp ishga tushirilmoqda...")
    
    # Initialize database
    with app.app_context():
        init_db()
        logger.info("Database initialized")
    
    # Initialize download manager and API client
    from core.download_manager import DownloadManager
    from core.library_manager import LibraryManager
    from api.kemono_client import KemonoAPIClient
    from models.database import Database
    
    api_client = KemonoAPIClient()
    db_manager = Database()
    download_path = config.get('download_path', './downloads')
    library_path = config.get('library_path', './library')
    
    download_manager = DownloadManager(api_client, db_manager, download_path)
    library_manager = LibraryManager(library_path, db_manager)
    
    # Store in app config for access in routes
    app.config['DOWNLOAD_MANAGER'] = download_manager
    app.config['API_CLIENT'] = api_client
    app.config['LIBRARY_MANAGER'] = library_manager
    logger.info("Download manager, library manager and API client initialized")
    
    # Register request logger
    @app.before_request
    def before_request():
        log_request()
    
    # Register blueprints
    register_blueprints(app, download_manager, api_client, library_manager)
    logger.info("Blueprints registered")
    
    # Register error handlers
    register_error_handlers(app)
    logger.info("Error handlers registered")
    
    # Create necessary directories
    create_directories()
    logger.info("Directories created")
    
    return app


def register_blueprints(app, download_manager, api_client, library_manager):
    """Register all Flask blueprints"""
    from routes.main import main_bp
    from routes.download import download_bp, init_download_routes
    from routes.search import search_bp, init_search_routes
    from routes.library import library_bp, init_library_routes
    from routes.api import api_bp, init_api_routes
    from routes.view_gallery import view_gallery_bp
    
    # Initialize download routes with manager and client
    init_download_routes(download_manager, api_client)
    
    # Initialize search routes with API client
    init_search_routes(api_client)
    
    # Initialize library routes with manager
    init_library_routes(library_manager)
    
    # Initialize API routes with managers
    init_api_routes(download_manager, library_manager)
    
    app.register_blueprint(main_bp)
    app.register_blueprint(download_bp, url_prefix='/download')
    app.register_blueprint(search_bp, url_prefix='/search')
    app.register_blueprint(library_bp, url_prefix='/library')
    app.register_blueprint(api_bp)
    app.register_blueprint(view_gallery_bp)


def register_error_handlers(app):
    """Register error handlers for common HTTP errors"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 Not Found errors"""
        logger.warning(f"404 Error: {request.path}")
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'NOT_FOUND',
                    'message': 'Sahifa topilmadi',
                    'details': str(error)
                }
            }), 404
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 Internal Server errors"""
        logger.error(f"500 Error: {str(error)}", exc_info=True)
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'INTERNAL_ERROR',
                    'message': 'Ichki server xatoligi',
                    'details': str(error)
                }
            }), 500
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        """Handle 403 Forbidden errors"""
        logger.warning(f"403 Error: {request.path}")
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'FORBIDDEN',
                    'message': 'Ruxsat berilmagan',
                    'details': str(error)
                }
            }), 403
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(400)
    def bad_request_error(error):
        """Handle 400 Bad Request errors"""
        logger.warning(f"400 Error: {str(error)}")
        if request_wants_json():
            return jsonify({
                'success': False,
                'error': {
                    'code': 'BAD_REQUEST',
                    'message': "Noto'g'ri so'rov",
                    'details': str(error)
                }
            }), 400
        return render_template('errors/400.html'), 400
    
    # Handle custom API errors
    @app.errorhandler(APIError)
    def handle_api_error_route(error):
        """Handle custom API errors"""
        return handle_api_error(error)
    
    @app.errorhandler(ValidationError)
    def handle_validation_error_route(error):
        """Handle validation errors"""
        return handle_api_error(error)


def request_wants_json():
    """Check if request expects JSON response"""
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def create_directories():
    """Create necessary directories for the application"""
    directories = [
        config.get('download_path', './downloads'),
        config.get('library_path', './library'),
        os.path.join(config.get('library_path', './library'), 'thumbs'),
        'data',
        'data/cache',
        'templates/errors'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)


def print_startup_info():
    """Print startup information"""
    host = config.get('flask_host', '0.0.0.0')
    port = config.get('flask_port', 5000)
    
    print("=" * 60)
    print("Kemono WebApp - Ishga tushirildi")
    print("=" * 60)
    print(f"Server manzili: http://{host}:{port}")
    if host == '0.0.0.0':
        print(f"Lokal kirish: http://localhost:{port}")
        print(f"Tarmoq kirish: http://<your-ip>:{port}")
    print("=" * 60)
    print("To'xtatish uchun: Ctrl+C")
    print("=" * 60)


# Create Flask app
app = create_app()


if __name__ == '__main__':
    # Print startup information
    print_startup_info()
    
    # Get configuration
    host = config.get('flask_host', '0.0.0.0')
    port = config.get('flask_port', 5000)
    debug = config.get('flask_debug', True)
    
    # Run Flask application
    try:
        logger.info(f"Starting Flask server on {host}:{port}")
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
        print("\n\nServer to'xtatildi.")
        sys.exit(0)
    except Exception as e:
        logger.critical(f"Failed to start server: {e}", exc_info=True)
        print(f"\n\nXatolik: {e}")
        sys.exit(1)
