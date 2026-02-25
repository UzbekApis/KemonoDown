"""
URL Parser
Kemono URL larni tahlil qilish moduli
"""

import re
from typing import Dict, Optional


class URLParser:
    """Kemono URL larni tahlil qilish"""
    
    PATTERNS = {
        'post': r'https?://(?:www\.)?kemono\.(su|cr|party)/([^/]+)/user/([^/]+)/post/([^/?]+)',
        'user': r'https?://(?:www\.)?kemono\.(su|cr|party)/([^/]+)/user/([^/?]+)/?$'
    }
    
    def __init__(self):
        """Initialize URL parser with compiled regex patterns"""
        self.post_pattern = re.compile(self.PATTERNS['post'])
        self.user_pattern = re.compile(self.PATTERNS['user'])
    
    def parse(self, url: str) -> Optional[Dict]:
        """
        URL ni parse qilish va ma'lumotlarni qaytarish
        
        Args:
            url: Kemono URL manzili
            
        Returns:
            Dictionary with parsed data or None if invalid
            Format: {
                'type': 'post' | 'user',
                'domain': 'su' | 'cr' | 'party',
                'service': str,
                'user_id': str,
                'post_id': str (only for post type)
            }
        """
        # Try to match post URL
        post_match = self.post_pattern.match(url)
        if post_match:
            domain, service, user_id, post_id = post_match.groups()
            return {
                'type': 'post',
                'domain': domain,
                'service': service,
                'user_id': user_id,
                'post_id': post_id
            }
        
        # Try to match user URL
        user_match = self.user_pattern.match(url)
        if user_match:
            domain, service, user_id = user_match.groups()
            return {
                'type': 'user',
                'domain': domain,
                'service': service,
                'user_id': user_id
            }
        
        return None
    
    def is_valid_url(self, url: str) -> bool:
        """
        URL to'g'riligini tekshirish
        
        Args:
            url: Tekshiriladigan URL
            
        Returns:
            True agar URL to'g'ri bo'lsa
        """
        return self.parse(url) is not None
    
    def get_url_type(self, url: str) -> Optional[str]:
        """
        URL turini aniqlash
        
        Args:
            url: Kemono URL
            
        Returns:
            'post', 'user' yoki None
        """
        parsed = self.parse(url)
        return parsed['type'] if parsed else None
