"""
Download routes for Kemono WebApp
Handle download operations
"""

from flask import Blueprint, render_template, request, jsonify
from api.url_parser import URLParser
from api.kemono_client import KemonoAPIClient
from core.download_manager import DownloadManager
from models.database import Database
from config import config

download_bp = Blueprint('download', __name__)

# Global instances (will be initialized in app.py)
download_manager = None
api_client = None


def init_download_routes(dm, api):
    """Initialize download routes with manager and API client"""
    global download_manager, api_client
    download_manager = dm
    api_client = api


@download_bp.route('/')
def download_page():
    """
    Download page route
    Requirements: 1.1, 1.5
    """
    return render_template('download.html')


@download_bp.route('/start', methods=['POST'])
def start_download():
    """
    Start download endpoint
    Requirements: 1.1, 1.2, 1.3
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form
        url = data.get('url', '').strip()
        
        # Validate URL
        if not url:
            return jsonify({
                'success': False,
                'error': 'URL kiritilmagan'
            }), 400
        
        parser = URLParser()
        if not parser.is_valid_url(url):
            return jsonify({
                'success': False,
                'error': 'Noto\'g\'ri Kemono URL'
            }), 400
        
        # Get file type filters (should be a list like ['all'] or ['images', 'videos'])
        filters = data.get('filters', ['all'])
        if not isinstance(filters, list):
            filters = ['all']
        
        # Add download to manager
        task_id = download_manager.add_download(url, filters)
        
        # Parse URL for database
        parsed = parser.parse(url)
        
        # Save to database
        db = Database()
        db.insert_download(
            task_id=task_id,
            url=url,
            service=parsed.get('service'),
            user_id=parsed.get('user_id'),
            post_id=parsed.get('post_id'),
            filters=filters
        )
        db.close()
        
        # Start download
        download_manager.start_download(task_id)
        
        return jsonify({
            'success': True,
            'task_id': task_id,
            'message': 'Yuklab olish boshlandi'
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@download_bp.route('/start-multi', methods=['POST'])
def start_multi_download():
    """
    Start multiple downloads at once
    Requirements: Multi-download feature
    """
    try:
        # Get request data
        data = request.get_json() if request.is_json else request.form
        urls = data.get('urls', [])
        
        if not urls or not isinstance(urls, list):
            return jsonify({
                'success': False,
                'error': 'URL ro\'yxati kiritilmagan'
            }), 400
        
        # Get file type filters
        filters = data.get('filters', ['all'])
        
        parser = URLParser()
        task_ids = []
        errors = []
        
        # Process each URL
        for url in urls:
            url = url.strip()
            
            # Validate URL
            if not parser.is_valid_url(url):
                errors.append(f'Noto\'g\'ri URL: {url}')
                continue
            
            try:
                # Add download to manager
                task_id = download_manager.add_download(url, filters)
                
                # Parse URL for database
                parsed = parser.parse(url)
                
                # Save to database
                db = Database()
                db.insert_download(
                    task_id=task_id,
                    url=url,
                    service=parsed.get('service'),
                    user_id=parsed.get('user_id'),
                    post_id=parsed.get('post_id'),
                    filters=filters
                )
                db.close()
                
                # Start download
                download_manager.start_download(task_id)
                
                task_ids.append(task_id)
                
            except Exception as e:
                errors.append(f'Xatolik ({url}): {str(e)}')
        
        # Return results
        response = {
            'success': len(task_ids) > 0,
            'task_ids': task_ids,
            'count': len(task_ids),
            'message': f'{len(task_ids)} ta yuklab olish boshlandi'
        }
        
        if errors:
            response['errors'] = errors
            response['message'] += f' ({len(errors)} ta xatolik)'
        
        return jsonify(response)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@download_bp.route('/pause/<task_id>', methods=['POST'])
def pause_download(task_id):
    """
    Pause download endpoint
    Requirements: 4.3
    """
    try:
        download_manager.pause_download(task_id)
        
        # Update database
        db = Database()
        db.update_download_status(task_id, 'paused')
        db.close()
        
        return jsonify({
            'success': True,
            'message': 'Yuklab olish to\'xtatildi'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@download_bp.route('/resume/<task_id>', methods=['POST'])
def resume_download(task_id):
    """
    Resume download endpoint
    Requirements: 4.4
    """
    try:
        download_manager.resume_download(task_id)
        
        # Update database
        db = Database()
        db.update_download_status(task_id, 'downloading')
        db.close()
        
        return jsonify({
            'success': True,
            'message': 'Yuklab olish davom ettirildi'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@download_bp.route('/cancel/<task_id>', methods=['POST'])
def cancel_download(task_id):
    """
    Cancel download endpoint
    Requirements: 4.4
    """
    try:
        download_manager.cancel_download(task_id)
        
        # Update database
        db = Database()
        db.update_download_status(task_id, 'cancelled')
        db.close()
        
        return jsonify({
            'success': True,
            'message': 'Yuklab olish bekor qilindi'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@download_bp.route('/list')
def list_downloads():
    """
    Get all downloads list
    """
    try:
        db = Database()
        downloads = db.get_all_downloads()
        db.close()
        
        return jsonify({
            'success': True,
            'downloads': downloads
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@download_bp.route('/delete/<task_id>', methods=['POST'])
def delete_download(task_id):
    """
    Delete download from active list
    Requirements: 12.2
    """
    try:
        download_manager.remove_download(task_id)
        
        # Update database
        db = Database()
        db.update_download_status(task_id, 'deleted')
        db.close()
        
        return jsonify({
            'success': True,
            'message': 'Download o\'chirildi'
        })
    
    except ValueError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 404
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
