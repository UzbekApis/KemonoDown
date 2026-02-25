"""
Main routes for Kemono WebApp
Home page and settings routes
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for
from config import config
from models.database import Database

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """
    Home page route
    Requirements: 6.1
    """
    db = Database()
    
    # Get recent downloads
    recent_downloads = db.get_all_downloads()[:5]  # Last 5 downloads
    
    # Get library statistics
    all_files = db.get_all_files()
    total_files = len(all_files)
    
    # Calculate total size
    total_size = sum(f.get('file_size', 0) or 0 for f in all_files)
    
    # Format size for display
    def format_size(size_bytes):
        """Format bytes to human readable format"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} TB"
    
    stats = {
        'total_downloads': len(recent_downloads),
        'total_files': total_files,
        'library_size': format_size(total_size)
    }
    
    db.close()
    
    return render_template('index.html', 
                         stats=stats, 
                         recent_downloads=recent_downloads)


@main_bp.route('/settings', methods=['GET'])
def settings():
    """
    Settings page route (GET)
    Requirements: 10.1, 10.2, 10.3
    """
    # Get current configuration
    current_config = {
        'download_path': config.get('download_path'),
        'library_path': config.get('library_path'),
        'max_concurrent_downloads': config.get('max_concurrent_downloads'),
        'api_base_url': config.get('api_base_url'),
        'theme': config.get('theme'),
        'language': config.get('language'),
        'cache_ttl': config.get('cache_ttl'),
        'thumbnail_size': config.get('thumbnail_size')
    }
    
    return render_template('settings.html', config=current_config)


@main_bp.route('/settings', methods=['POST'])
def save_settings():
    """
    Save settings route (POST)
    Requirements: 10.1, 10.2, 10.3
    """
    try:
        # Get form data
        updates = {}
        
        # Download path
        if 'download_path' in request.form:
            updates['download_path'] = request.form['download_path']
        
        # Library path
        if 'library_path' in request.form:
            updates['library_path'] = request.form['library_path']
        
        # Max concurrent downloads
        if 'max_concurrent_downloads' in request.form:
            try:
                updates['max_concurrent_downloads'] = int(request.form['max_concurrent_downloads'])
            except ValueError:
                pass
        
        # API base URL
        if 'api_base_url' in request.form:
            updates['api_base_url'] = request.form['api_base_url']
        
        # Theme
        if 'theme' in request.form:
            updates['theme'] = request.form['theme']
        
        # Language
        if 'language' in request.form:
            updates['language'] = request.form['language']
        
        # Cache TTL
        if 'cache_ttl' in request.form:
            try:
                updates['cache_ttl'] = int(request.form['cache_ttl'])
            except ValueError:
                pass
        
        # Update configuration
        success = config.update(updates)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Sozlamalar saqlandi'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sozlamalarni saqlashda xatolik'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
