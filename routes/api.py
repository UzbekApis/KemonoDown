"""
API routes for Kemono WebApp
JSON endpoints for AJAX requests
"""

from flask import Blueprint, request, jsonify
from core.download_manager import DownloadManager
from core.library_manager import LibraryManager
from models.database import Database
from config import config

api_bp = Blueprint('api', __name__)

# Global instances (will be initialized in app.py)
download_manager = None
library_manager = None


def init_api_routes(dm, lm):
    """Initialize API routes with managers"""
    global download_manager, library_manager
    download_manager = dm
    library_manager = lm


@api_bp.route('/api/progress/<task_id>')
def get_progress(task_id):
    """
    Get download progress
    Requirements: 4.2
    """
    try:
        progress = download_manager.get_progress(task_id)
        
        if 'error' in progress and progress['error'] == 'Task not found':
            # Try to get from database
            db = Database()
            download = db.get_download(task_id)
            db.close()
            
            if download:
                return jsonify({
                    'success': True,
                    'progress': {
                        'task_id': task_id,
                        'status': download.get('status'),
                        'total': download.get('total_files', 0),
                        'downloaded': download.get('downloaded_files', 0),
                        'percent': int((download.get('downloaded_files', 0) / max(download.get('total_files', 1), 1)) * 100),
                        'current_file': '',
                        'error': None
                    }
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Task topilmadi'
                }), 404
        
        return jsonify({
            'success': True,
            'progress': progress
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/downloads')
def get_all_downloads():
    """
    Get all downloads with their progress
    """
    try:
        # Get active downloads from manager
        active_downloads = download_manager.get_all_downloads()
        
        # Get all downloads from database
        db = Database()
        db_downloads = db.get_all_downloads()
        db.close()
        
        # Merge data
        downloads = []
        for db_download in db_downloads:
            task_id = db_download.get('task_id')
            
            # Get live progress if available
            if task_id in active_downloads:
                progress = download_manager.get_progress(task_id)
                db_download['progress'] = progress
            else:
                # Use database data
                total = db_download.get('total_files', 0)
                downloaded = db_download.get('downloaded_files', 0)
                db_download['progress'] = {
                    'task_id': task_id,
                    'status': db_download.get('status'),
                    'total': total,
                    'downloaded': downloaded,
                    'percent': int((downloaded / max(total, 1)) * 100) if total > 0 else 0,
                    'current_file': '',
                    'error': None
                }
            
            downloads.append(db_download)
        
        return jsonify({
            'success': True,
            'downloads': downloads,
            'count': len(downloads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/downloads/active')
def get_active_downloads():
    """
    Get active downloads (exclude only cancelled and deleted)
    Requirements: 12.1
    """
    try:
        # Get active downloads from manager (in-memory)
        memory_downloads = download_manager.get_all_downloads()
        
        # Get all downloads from database
        db = Database()
        db_downloads = db.get_all_downloads()
        db.close()
        
        # Merge: prioritize memory data, but include completed/failed from DB
        all_downloads = {}
        
        # First, add all from memory
        for task_id, download in memory_downloads.items():
            if download['status'] not in ['cancelled', 'deleted']:
                all_downloads[task_id] = download
        
        # Then, add completed/failed from database if not in memory
        for db_download in db_downloads:
            task_id = db_download.get('task_id')
            status = db_download.get('status')
            
            # Skip cancelled and deleted
            if status in ['cancelled', 'deleted']:
                continue
            
            # If not in memory, add from database
            if task_id not in all_downloads:
                # Convert database format to API format
                total = db_download.get('total_files', 0)
                downloaded = db_download.get('downloaded_files', 0)
                percent = int((downloaded / max(total, 1)) * 100) if total > 0 else 0
                
                all_downloads[task_id] = {
                    'task_id': task_id,
                    'url': db_download.get('url', ''),
                    'status': status,
                    'total_files': total,
                    'downloaded_files': downloaded,
                    'progress_percent': percent,
                    'current_file': '',
                    'error': db_download.get('error_message')
                }
        
        return jsonify({
            'success': True,
            'downloads': all_downloads,
            'count': len(all_downloads)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/library/scan')
def scan_library():
    """
    Scan library and return files
    Requirements: 10.5
    """
    try:
        files = library_manager.scan_library()
        
        return jsonify({
            'success': True,
            'files': files,
            'count': len(files)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/library/generate-thumbnails', methods=['POST'])
def generate_thumbnails():
    """
    Generate thumbnails for all images in library
    """
    try:
        library_manager.generate_thumbnails()
        
        return jsonify({
            'success': True,
            'message': 'Thumbnails yaratildi'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/settings', methods=['GET'])
def get_settings():
    """
    Get current settings
    Requirements: 10.5
    """
    try:
        settings = {
            'download_path': config.get('download_path'),
            'library_path': config.get('library_path'),
            'max_concurrent_downloads': config.get('max_concurrent_downloads'),
            'api_base_url': config.get('api_base_url'),
            'theme': config.get('theme'),
            'language': config.get('language'),
            'cache_ttl': config.get('cache_ttl'),
            'thumbnail_size': config.get('thumbnail_size')
        }
        
        return jsonify({
            'success': True,
            'settings': settings
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/settings', methods=['POST'])
def save_settings():
    """
    Save settings
    Requirements: 10.5
    """
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Validate and update settings
        updates = {}
        
        # String settings
        for key in ['download_path', 'library_path', 'api_base_url', 'theme', 'language']:
            if key in data:
                updates[key] = data[key]
        
        # Integer settings
        for key in ['max_concurrent_downloads', 'cache_ttl']:
            if key in data:
                try:
                    updates[key] = int(data[key])
                except (ValueError, TypeError):
                    return jsonify({
                        'success': False,
                        'error': f'Noto\'g\'ri qiymat: {key}'
                    }), 400
        
        # Array settings
        if 'thumbnail_size' in data:
            if isinstance(data['thumbnail_size'], list) and len(data['thumbnail_size']) == 2:
                updates['thumbnail_size'] = data['thumbnail_size']
        
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


@api_bp.route('/api/settings/reset', methods=['POST'])
def reset_settings():
    """
    Reset settings to default
    """
    try:
        success = config.reset_to_default()
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Sozlamalar standart holatga qaytarildi'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Sozlamalarni qaytarishda xatolik'
            }), 500
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@api_bp.route('/api/health')
def health_check():
    """
    Health check endpoint
    """
    return jsonify({
        'success': True,
        'status': 'healthy',
        'version': '1.0.0'
    })
