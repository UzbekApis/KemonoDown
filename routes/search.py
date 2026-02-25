"""
Search routes for Kemono WebApp
Handle artist and post search
"""

from flask import Blueprint, render_template, request, jsonify
from api.kemono_client import KemonoAPIClient
from api.search import find_closest_matches
from models.database import Database
from config import config

search_bp = Blueprint('search', __name__)

# Global API client instance (will be initialized in app.py)
api_client = None


def init_search_routes(api):
    """Initialize search routes with API client"""
    global api_client
    api_client = api


@search_bp.route('/')
def search_page():
    """
    Search page route
    Requirements: 2.1
    """
    return render_template('search.html')


@search_bp.route('/artist', methods=['POST'])
def search_artist():
    """
    Artist search endpoint
    Requirements: 2.2, 2.3, 2.4
    """
    try:
        # Get search query
        data = request.get_json() if request.is_json else request.form
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Qidiruv so\'zi kiritilmagan'
            }), 400
        
        # Get all creators from API
        all_creators = api_client.get_all_creators()
        
        if not all_creators:
            return jsonify({
                'success': True,
                'results': [],
                'message': 'Hech qanday natija topilmadi'
            })
        
        # Use Levenshtein distance to find closest matches
        matches = find_closest_matches(
            search_term=query,
            items=all_creators,
            key='name',
            limit=20
        )
        
        # Format results
        results = []
        for creator in matches:
            results.append({
                'id': creator.get('id'),
                'name': creator.get('name'),
                'service': creator.get('service'),
                'indexed': creator.get('indexed'),
                'updated': creator.get('updated')
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/post', methods=['POST'])
def search_post():
    """
    Post search endpoint
    Requirements: 2.1, 2.2, 2.3, 2.4
    """
    try:
        # Get search query
        data = request.get_json() if request.is_json else request.form
        query = data.get('query', '').strip()
        limit = int(data.get('limit', 50))
        offset = int(data.get('offset', 0))
        
        if not query:
            return jsonify({
                'success': False,
                'error': 'Qidiruv so\'zi kiritilmagan'
            }), 400
        
        # Search posts via API with offset
        posts = api_client.search_posts(query, limit=limit, offset=offset)
        
        if not posts:
            return jsonify({
                'success': True,
                'results': [],
                'message': 'Hech qanday natija topilmadi'
            })
        
        # Format results
        results = []
        for post in posts:
            results.append({
                'id': post.get('id'),
                'user': post.get('user'),
                'service': post.get('service'),
                'title': post.get('title'),
                'content': post.get('content', '')[:200],  # First 200 chars
                'published': post.get('published'),
                'edited': post.get('edited'),
                'file': post.get('file'),
                'attachments': post.get('attachments', [])
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/artist/<service>/<user_id>')
def get_artist_posts(service, user_id):
    """
    Get all posts for a specific artist
    Requirements: 2.4
    """
    try:
        offset = int(request.args.get('offset', 0))
        
        # Check if api_client is initialized
        if api_client is None:
            return jsonify({
                'success': False,
                'error': 'API client not initialized'
            }), 500
        
        # Get user posts from API
        posts = api_client.get_user_posts(service, user_id, offset=offset)
        
        if not posts:
            return jsonify({
                'success': True,
                'results': [],
                'message': 'Postlar topilmadi'
            })
        
        # Format results
        results = []
        for post in posts:
            results.append({
                'id': post.get('id'),
                'user': post.get('user'),
                'service': post.get('service'),
                'title': post.get('title'),
                'content': post.get('content', '')[:200],
                'published': post.get('published'),
                'edited': post.get('edited'),
                'file': post.get('file'),
                'attachments': post.get('attachments', [])
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'offset': offset
        })
    
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"Error in get_artist_posts: {error_details}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results),
            'offset': offset
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@search_bp.route('/random')
def get_random_posts():
    """
    Get random posts
    """
    try:
        count = int(request.args.get('count', 25))
        
        # Get random posts from API
        posts = api_client.get_random_posts(count=count)
        
        if not posts:
            return jsonify({
                'success': True,
                'results': [],
                'message': 'Postlar topilmadi'
            })
        
        # Format results
        results = []
        for post in posts:
            results.append({
                'id': post.get('id'),
                'user': post.get('user'),
                'service': post.get('service'),
                'title': post.get('title'),
                'content': post.get('content', '')[:200],
                'published': post.get('published'),
                'file': post.get('file'),
                'attachments': post.get('attachments', [])
            })
        
        return jsonify({
            'success': True,
            'results': results,
            'count': len(results)
        })
    
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
