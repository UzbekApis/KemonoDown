"""
Library routes for Kemono WebApp
Handle library viewing and management
"""

from flask import Blueprint, render_template, request, jsonify, send_file
from core.library_manager import LibraryManager
from models.database import Database
from config import config
import os

library_bp = Blueprint('library', __name__)

# Global library manager instance (will be initialized in app.py)
library_manager = None


def init_library_routes(lm):
    """Initialize library routes with library manager"""
    global library_manager
    library_manager = lm


@library_bp.route('/')
def library_page():
    """
    Library page route
    Requirements: 3.2
    """
    # Get filter parameters
    filter_type = request.args.get('type', 'all')
    artist_id = request.args.get('artist')
    post_id = request.args.get('post')
    
    return render_template('library.html', 
                         filter_type=filter_type,
                         artist_id=artist_id,
                         post_id=post_id)


@library_bp.route('/gallery/<post_id>')
def gallery_view(post_id):
    """
    Simple gallery view for a specific post
    """
    try:
        # Get all files for this post
        files = library_manager.get_by_post(post_id)
        
        if not files or len(files) == 0:
            return render_template('errors/404.html', 
                                 message='Post topilmadi yoki fayllar mavjud emas'), 404
        
        # Get post title from first file
        post_title = files[0].get('post_title', 'Unknown Post') if files else 'Gallery'
        
        return render_template('gallery.html',
                             files=files,
                             post_id=post_id,
                             post_title=post_title)
    
    except Exception as e:
        print(f"Gallery view error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('errors/500.html', 
                             error=str(e)), 500


@library_bp.route('/view/<post_id>')
def simple_gallery_view(post_id):
    """
    Alternative simple gallery view
    """
    return gallery_view(post_id)


@library_bp.route('/files')
def get_library_files():
    """
    Get library files with optional filters
    Requirements: 3.2, 3.4
    """
    try:
        # Get filter parameters
        filter_type = request.args.get('type', 'all')
        artist_id = request.args.get('artist')
        service = request.args.get('service')
        post_id = request.args.get('post')
        
        # Get files based on filters
        if post_id:
            # Filter by post
            files = library_manager.get_by_post(post_id)
        elif artist_id:
            # Filter by artist
            files = library_manager.get_by_artist(artist_id, service)
        else:
            # Get all files
            files = library_manager.scan_library()
        
        # Apply file type filter
        if filter_type != 'all':
            files = [f for f in files if f.get('file_type') == filter_type]
        
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


@library_bp.route('/filter/artist')
def filter_by_artist():
    """
    Filter library by artist
    Requirements: 3.4
    """
    try:
        artist_id = request.args.get('artist_id')
        service = request.args.get('service')
        
        if not artist_id:
            return jsonify({
                'success': False,
                'error': 'Artist ID kiritilmagan'
            }), 400
        
        files = library_manager.get_by_artist(artist_id, service)
        
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


@library_bp.route('/filter/post')
def filter_by_post():
    """
    Filter library by post
    Requirements: 3.4
    """
    try:
        post_id = request.args.get('post_id')
        
        if not post_id:
            return jsonify({
                'success': False,
                'error': 'Post ID kiritilmagan'
            }), 400
        
        files = library_manager.get_by_post(post_id)
        
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


@library_bp.route('/file/<int:file_id>', methods=['DELETE'])
def delete_file(file_id):
    """
    Delete file from library
    Requirements: 3.5
    """
    try:
        success = library_manager.delete_file(file_id)
        
        if success:
            return jsonify({
                'success': True,
                'message': 'Fayl o\'chirildi'
            })
        else:
            return jsonify({
                'success': False,
                'error': 'Fayl topilmadi yoki o\'chirishda xatolik'
            }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/file/<int:file_id>')
def serve_file(file_id):
    """
    Serve file for viewing in gallery
    Requirements: 3.4
    """
    try:
        db = Database()
        file_info = db.get_file(file_id)
        db.close()
        
        if not file_info:
            return jsonify({
                'success': False,
                'error': 'Fayl topilmadi'
            }), 404
        
        filepath = file_info.get('filepath')
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Fayl mavjud emas'
            }), 404
        
        return send_file(filepath, as_attachment=False)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/file/<int:file_id>/view')
def view_file(file_id):
    """
    View/download file
    Requirements: 3.4
    """
    try:
        db = Database()
        file_info = db.get_file(file_id)
        db.close()
        
        if not file_info:
            return jsonify({
                'success': False,
                'error': 'Fayl topilmadi'
            }), 404
        
        filepath = file_info.get('filepath')
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Fayl mavjud emas'
            }), 404
        
        return send_file(filepath, as_attachment=False)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/file/<int:file_id>/download')
def download_file(file_id):
    """
    Download file
    Requirements: 3.4
    """
    try:
        db = Database()
        file_info = db.get_file(file_id)
        db.close()
        
        if not file_info:
            return jsonify({
                'success': False,
                'error': 'Fayl topilmadi'
            }), 404
        
        filepath = file_info.get('filepath')
        filename = file_info.get('filename')
        
        if not filepath or not os.path.exists(filepath):
            return jsonify({
                'success': False,
                'error': 'Fayl mavjud emas'
            }), 404
        
        return send_file(filepath, as_attachment=True, download_name=filename)
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/stats')
def get_statistics():
    """
    Get library statistics
    Requirements: 3.2
    """
    try:
        db = Database()
        
        # Get all files
        all_files = db.get_all_files()
        
        # Calculate statistics
        total_files = len(all_files)
        total_size = sum(f.get('file_size', 0) or 0 for f in all_files)
        
        # Count by type
        files_by_type = {}
        for f in all_files:
            file_type = f.get('file_type', 'unknown')
            files_by_type[file_type] = files_by_type.get(file_type, 0) + 1
        
        # Count unique artists
        unique_artists = len(set(f.get('user_id') for f in all_files if f.get('user_id')))
        
        # Count unique posts
        unique_posts = len(set(f.get('post_id') for f in all_files if f.get('post_id')))
        
        db.close()
        
        # Format size
        def format_size(size_bytes):
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024.0:
                    return f"{size_bytes:.2f} {unit}"
                size_bytes /= 1024.0
            return f"{size_bytes:.2f} TB"
        
        return jsonify({
            'success': True,
            'stats': {
                'total_files': total_files,
                'total_size': total_size,
                'total_size_formatted': format_size(total_size),
                'files_by_type': files_by_type,
                'unique_artists': unique_artists,
                'unique_posts': unique_posts
            }
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/thumbnail/<int:file_id>')
def get_thumbnail(file_id):
    """
    Get file thumbnail
    Requirements: 3.3
    """
    try:
        db = Database()
        file_info = db.get_file(file_id)
        db.close()
        
        if not file_info:
            return jsonify({
                'success': False,
                'error': 'Fayl topilmadi'
            }), 404
        
        thumbnail_path = file_info.get('thumbnail_path')
        
        if thumbnail_path and os.path.exists(thumbnail_path):
            return send_file(thumbnail_path)
        else:
            # Return placeholder or original file
            filepath = file_info.get('filepath')
            if filepath and os.path.exists(filepath):
                return send_file(filepath)
            else:
                return jsonify({
                    'success': False,
                    'error': 'Thumbnail mavjud emas'
                }), 404
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@library_bp.route('/post/<service>/<user_id>/<post_id>/zip-files')
def get_post_zip_files(service, user_id, post_id):
    """
    Get ZIP files for a post from Kemono API
    """
    try:
        from api.kemono_client import KemonoAPIClient
        
        api_client = KemonoAPIClient()
        post_data = api_client.get_post_details(service, user_id, post_id)
        
        if not post_data:
            return jsonify({
                'success': False,
                'error': 'Post not found'
            }), 404
        
        # Get post thumbnail
        thumbnail_url = None
        if 'file' in post_data and post_data['file'] and post_data['file'].get('path'):
            thumbnail_url = f"https://kemono.cr/data{post_data['file']['path']}"
        elif 'attachments' in post_data and isinstance(post_data['attachments'], list) and len(post_data['attachments']) > 0:
            first_attachment = post_data['attachments'][0]
            if first_attachment.get('path'):
                thumbnail_url = f"https://kemono.cr/data{first_attachment['path']}"
        
        # Get all files
        all_files = []
        
        # Add attachments
        if 'attachments' in post_data and isinstance(post_data['attachments'], list):
            all_files.extend(post_data['attachments'])
        
        # Add main file
        if 'file' in post_data and post_data['file']:
            all_files.append(post_data['file'])
        
        # Filter ZIP files
        zip_files = []
        for file_info in all_files:
            name = file_info.get('name', '')
            path = file_info.get('path', '')
            
            if '.zip' in name.lower() or '.zip' in path.lower():
                zip_files.append({
                    'name': name,
                    'path': path,
                    'url': f"https://kemono.cr/data{path}"
                })
        
        return jsonify({
            'success': True,
            'zip_files': zip_files,
            'count': len(zip_files),
            'thumbnail': thumbnail_url,
            'post_title': post_data.get('title', 'Unknown Post')
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
