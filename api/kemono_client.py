"""
Kemono API Client
Kemono.cr API bilan ishlash uchun asosiy modul
"""

import time
import cloudscraper
from typing import List, Dict, Optional, Callable
from functools import lru_cache


class KemonoAPIClient:
    """Kemono API bilan ishlash uchun client"""
    
    def __init__(self, base_url: str = "https://kemono.cr/api/v1"):
        """
        Initialize Kemono API client
        
        Args:
            base_url: Kemono API base URL
        """
        self.base_url = base_url.rstrip('/')
        self.session = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'mobile': False
            }
        )
        # Add custom headers (minimal, like PHP code)
        self.session.headers.update({
            'Accept': 'text/css',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        })
        self.cache = {}
        self.cache_ttl = 300  # 5 minutes
        
    def _make_request(self, endpoint: str, params: Optional[Dict] = None, retries: int = 3) -> Dict:
        """
        API ga so'rov yuborish (retry mexanizmi bilan)
        
        Args:
            endpoint: API endpoint
            params: Query parameters
            retries: Qayta urinishlar soni
            
        Returns:
            API response as dictionary
        """
        url = f"{self.base_url}/{endpoint.lstrip('/')}"
        
        # Check cache
        cache_key = f"{url}:{str(params)}"
        if cache_key in self.cache:
            cached_data, timestamp = self.cache[cache_key]
            if time.time() - timestamp < self.cache_ttl:
                return cached_data
        
        # Make request with retries
        last_error = None
        for attempt in range(retries):
            try:
                # Add delay between retries (exponential backoff)
                if attempt > 0:
                    delay = 2 ** attempt  # 2, 4, 8 seconds
                    print(f"Retry {attempt + 1}/{retries} after {delay}s delay...")
                    time.sleep(delay)
                
                response = self.session.get(url, params=params, timeout=30)
                response.raise_for_status()
                data = response.json()
                
                # Cache response
                self.cache[cache_key] = (data, time.time())
                
                return data
                
            except Exception as e:
                last_error = e
                print(f"Request error (attempt {attempt + 1}/{retries}): {e}")
                
                # If 403, try alternative domains immediately
                if hasattr(e, 'response') and e.response and e.response.status_code == 403:
                    if 'kemono.cr' in url:
                        # Try alternative domains
                        alt_domains = ['kemono.su', 'kemono.party']
                        for domain in alt_domains:
                            try:
                                alt_url = url.replace('kemono.cr', domain)
                                print(f"Trying alternative domain: {domain}")
                                response = self.session.get(alt_url, params=params, timeout=30)
                                response.raise_for_status()
                                data = response.json()
                                
                                # Update base_url if successful
                                self.base_url = self.base_url.replace('kemono.cr', domain)
                                print(f"Switched to {domain} successfully")
                                
                                # Cache response
                                self.cache[cache_key] = (data, time.time())
                                
                                return data
                            except Exception as alt_error:
                                print(f"Alternative domain {domain} failed: {alt_error}")
                                continue
                
                # Continue to next retry
                continue
        
        # All retries failed
        raise last_error if last_error else Exception("Request failed")
    
    def search_posts(self, query: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Post qidirish - Kemono API /posts endpoint'i bilan
        
        Args:
            query: Qidiruv so'zi
            limit: Maksimal natijalar soni (minimum 50)
            offset: Pagination offset (50 qadam bilan)
            
        Returns:
            Postlar ro'yxati
        """
        try:
            # Kemono API: GET /v1/posts?q=query&o=offset
            # Returns dict with 'count', 'true_count', and 'posts' array
            # Note: offset stepping is enforced at 50, and API returns 50 posts by default
            
            # Ensure minimum 50 posts
            if limit and limit < 50:
                limit = 50
            
            params = {'q': query}
            
            # Add offset if specified (API enforces stepping of 50)
            if offset > 0:
                params['o'] = offset
            
            print(f"Searching posts with query: {query}, offset: {offset}, limit: {limit}")
            result = self._make_request('posts', params=params)
            
            # API returns dict with posts array
            if result and isinstance(result, dict):
                posts = result.get('posts', [])
                count = result.get('count', 0)
                true_count = result.get('true_count', 0)
                print(f"Found {len(posts)} posts (count: {count}, true_count: {true_count})")
                return posts[:limit] if limit else posts
            elif result and isinstance(result, list):
                # Fallback if API returns list directly
                print(f"Found {len(result)} posts")
                return result[:limit] if limit else result
            else:
                print(f"No posts found or invalid response format: {type(result)}")
                return []
            
        except Exception as e:
            print(f"Search posts error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def get_random_posts(self, count: int = 25) -> List[Dict]:
        """
        Random postlar olish
        
        Args:
            count: Postlar soni
            
        Returns:
            Random postlar ro'yxati
        """
        try:
            result = self._make_request('posts/random', params={'count': count})
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Get random posts error: {e}")
            return []
    
    def get_popular_posts(self) -> List[Dict]:
        """
        Mashhur postlar olish
        
        Returns:
            Mashhur postlar ro'yxati
        """
        try:
            result = self._make_request('posts/popular')
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Get popular posts error: {e}")
            return []
    
    def get_all_creators(self) -> List[Dict]:
        """
        Barcha creatorlar ro'yxati
        
        Returns:
            Creatorlar ro'yxati
        """
        try:
            result = self._make_request('creators')
            return result if isinstance(result, list) else []
        except Exception as e:
            print(f"Get all creators error: {e}")
            return []
    
    def get_post_details(self, service: str, user_id: str, post_id: str) -> Optional[Dict]:
        """
        Post tafsilotlari
        
        Args:
            service: Service nomi (patreon, fanbox, etc.)
            user_id: User ID
            post_id: Post ID
            
        Returns:
            Post tafsilotlari yoki None
        """
        try:
            endpoint = f"{service}/user/{user_id}/post/{post_id}"
            print(f"Get post details: {endpoint}")
            result = self._make_request(endpoint)
            
            # API returns data wrapped in 'post' key sometimes
            if result and isinstance(result, dict) and 'post' in result:
                return result['post']
            
            return result if result else {}
        except Exception as e:
            print(f"Get post details error: {e}")
            return None
    
    def get_user_posts(self, service: str, user_id: str, limit: int = 50, offset: int = 0) -> List[Dict]:
        """
        Get all posts from a user/creator
        
        Args:
            service: Service name (patreon, fanbox, etc.)
            user_id: Creator/user ID
            limit: Maximum number of posts
            offset: Pagination offset
            
        Returns:
            List of posts
        """
        try:
            # Kemono API endpoint for user posts with pagination
            # Try different possible endpoints
            endpoints_to_try = [
                f"{service}/user/{user_id}/posts",  # With /posts suffix
                f"posts/{service}/{user_id}",        # Alternative format
                f"{service}/user/{user_id}"          # Original format
            ]
            
            result = None
            for endpoint in endpoints_to_try:
                try:
                    params = {}
                    if offset > 0:
                        params['o'] = offset
                    
                    print(f"Trying endpoint: {endpoint} (offset={offset})")
                    result = self._make_request(endpoint, params=params)
                    
                    # If we got a valid response, break
                    if result:
                        print(f"Success with endpoint: {endpoint}")
                        break
                except Exception as e:
                    print(f"Failed with {endpoint}: {e}")
                    continue
            
            if not result:
                print("All endpoints failed")
                return []
            
            # API returns posts as a list directly
            if isinstance(result, list):
                return result[:limit]
            elif isinstance(result, dict):
                # Check various possible response formats
                if 'posts' in result:
                    return result['posts'][:limit]
                elif 'results' in result:
                    return result['results'][:limit]
                elif 'data' in result:
                    return result['data'][:limit]
            
            # If no posts found, return empty list
            print(f"No posts found in response format: {type(result)}")
            return []
            
        except Exception as e:
            print(f"Get user posts error: {e}")
            import traceback
            traceback.print_exc()
            return []
    
    def download_file(self, url: str, save_path: str, 
                     progress_callback: Optional[Callable[[int, int], None]] = None,
                     chunk_size: int = 8192) -> bool:
        """
        Faylni yuklab olish
        
        Args:
            url: Fayl URL
            save_path: Saqlash yo'li
            progress_callback: Progress callback funksiyasi (downloaded, total)
            chunk_size: Chunk hajmi (bytes)
            
        Returns:
            True agar muvaffaqiyatli bo'lsa
        """
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                response = self.session.get(url, stream=True, timeout=30)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            if progress_callback:
                                progress_callback(downloaded, total_size)
                
                return True
                
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    time.sleep(wait_time)
                else:
                    return False
        
        return False
    
    def clear_cache(self):
        """Cache ni tozalash"""
        self.cache.clear()
    
    def download_file(self, file_url: str, save_path: str, progress_callback: Callable = None):
        """
        Download a file from URL with retry mechanism
        
        Args:
            file_url: Full URL or path to file
            save_path: Local path to save file
            progress_callback: Optional callback for progress updates (progress_percent)
        
        Returns:
            True if successful, False otherwise
        """
        max_retries = 3
        backoff_factor = 2
        
        for attempt in range(max_retries):
            try:
                # If file_url is a path, prepend base domain
                if file_url.startswith('/'):
                    # Extract domain from base_url
                    from urllib.parse import urlparse
                    parsed = urlparse(self.base_url)
                    base_domain = f"{parsed.scheme}://{parsed.netloc}"
                    file_url = base_domain.replace('/api/v1', '') + file_url
                
                print(f"Downloading (attempt {attempt + 1}/{max_retries}): {file_url}")
                
                # Download with streaming and larger timeout
                response = self.session.get(file_url, stream=True, timeout=120)
                response.raise_for_status()
                
                total_size = int(response.headers.get('content-length', 0))
                downloaded = 0
                chunk_size = 8192  # 8KB chunks
                
                # Write to file
                with open(save_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:  # filter out keep-alive new chunks
                            f.write(chunk)
                            downloaded += len(chunk)
                            
                            # Call progress callback
                            if progress_callback and total_size > 0:
                                progress = (downloaded / total_size) * 100
                                progress_callback(progress)
                
                # Verify file was written
                import os
                if os.path.exists(save_path) and os.path.getsize(save_path) > 0:
                    print(f"Downloaded successfully: {save_path} ({downloaded} bytes)")
                    return True
                else:
                    print(f"File not written properly: {save_path}")
                    if attempt < max_retries - 1:
                        continue
                    return False
                
            except Exception as e:
                print(f"Download attempt {attempt + 1} failed: {e}")
                
                # Retry with exponential backoff
                if attempt < max_retries - 1:
                    wait_time = backoff_factor ** attempt
                    print(f"Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                else:
                    print(f"All download attempts failed for: {file_url}")
                    return False
        
        return False
