"""
View Gallery routes - Direct file system access
"""

import os
from flask import Blueprint, render_template, send_file, request, abort
from config import config

view_gallery_bp = Blueprint('view_gallery', __name__)


def get_file_type(filename):
    """Determine file type from extension"""
    ext = filename.lower().split('.')[-1]
    
    image_exts = ['jpg', 'jpeg', 'png', 'gif', 'webp', 'bmp']
    video_exts = ['mp4', 'webm', 'mov', 'avi', 'mkv']
    
    if ext in image_exts:
        return 'image'
    elif ext in video_exts:
        return 'video'
    elif ext == 'zip':
        return 'zip'
    else:
        return 'other'


def format_file_size(size_bytes):
    """Format file size in human readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} TB"


def find_post_folder(post_id):
    """
    Search for post folder in downloads directory
    Returns: (service, user_id, post_path) or (None, None, None)
    """
    download_path = config.get('download_path', 'downloads')
    
    if not os.path.exists(download_path):
        return None, None, None
    
    # Search through service folders
    for service in os.listdir(download_path):
        service_path = os.path.join(download_path, service)
        
        if not os.path.isdir(service_path):
            continue
        
        # Search through user folders
        for user_id in os.listdir(service_path):
            user_path = os.path.join(service_path, user_id)
            
            if not os.path.isdir(user_path):
                continue
            
            # Check if post folder exists
            post_path = os.path.join(user_path, post_id)
            
            if os.path.exists(post_path) and os.path.isdir(post_path):
                return service, user_id, post_path
    
    return None, None, None


@view_gallery_bp.route('/view_gallery/<post_id>')
def view_gallery(post_id):
    """
    View gallery for a post by scanning downloads folder
    """
    try:
        # Find post folder
        service, user_id, post_path = find_post_folder(post_id)
        
        if not post_path:
            return render_template('errors/404.html', 
                                 message=f'Post {post_id} not found in downloads'), 404
        
        # Get all files in post folder
        files = []
        
        for filename in os.listdir(post_path):
            file_path = os.path.join(post_path, filename)
            
            if not os.path.isfile(file_path):
                continue
            
            file_type = get_file_type(filename)
            file_size = os.path.getsize(file_path)
            
            file_info = {
                'name': filename,
                'type': file_type,
                'size': format_file_size(file_size),
                'kemono_url': None
            }
            
            # For ZIP files, generate Kemono URL
            if file_type == 'zip':
                file_info['kemono_url'] = f"https://kemono.cr/data/{service}/user/{user_id}/post/{post_id}/{filename}"
            
            files.append(file_info)
        
        # Sort files by name (natural sort for numbers)
        def natural_sort_key(filename):
            import re
            return [int(text) if text.isdigit() else text.lower()
                    for text in re.split('([0-9]+)', filename)]
        
        files.sort(key=lambda x: natural_sort_key(x['name']))
        
        # Get post title (use folder name or first file)
        post_title = f"Post {post_id}"
        
        return render_template('view_gallery.html',
                             files=files,
                             post_id=post_id,
                             post_title=post_title,
                             service=service,
                             user_id=user_id)
    
    except Exception as e:
        print(f"View gallery error: {e}")
        import traceback
        traceback.print_exc()
        return render_template('errors/500.html', 
                             error=str(e)), 500


@view_gallery_bp.route('/view_gallery/file/<post_id>/<filename>')
def serve_file(post_id, filename):
    """
    Serve a file from post folder
    """
    try:
        # Find post folder
        service, user_id, post_path = find_post_folder(post_id)
        
        if not post_path:
            abort(404)
        
        file_path = os.path.join(post_path, filename)
        
        if not os.path.exists(file_path):
            abort(404)
        
        # Check if download is requested
        as_attachment = request.args.get('download') == '1'
        
        return send_file(file_path, as_attachment=as_attachment)
    
    except Exception as e:
        print(f"Serve file error: {e}")
        abort(500)
