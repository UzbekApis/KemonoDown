"""
Security module for input validation and sanitization
"""
import re
import os
from pathlib import Path
from urllib.parse import urlparse


def validate_kemono_url(url: str) -> bool:
    """
    Validate Kemono URL format
    
    Args:
        url: URL string to validate
        
    Returns:
        bool: True if valid Kemono URL, False otherwise
        
    Requirements: 9.1
    """
    if not url or not isinstance(url, str):
        return False
    
    # Check for valid Kemono domain patterns
    pattern = r'^https?://(?:www\.)?kemono\.(su|cr|party)/.+'
    return bool(re.match(pattern, url.strip()))


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to prevent security issues
    
    Removes or replaces dangerous characters that could cause:
    - Path traversal attacks
    - Command injection
    - File system issues
    
    Args:
        filename: Original filename
        
    Returns:
        str: Sanitized filename
        
    Requirements: 9.1, 9.2
    """
    if not filename or not isinstance(filename, str):
        return "unnamed_file"
    
    # Remove path separators and dangerous characters
    # Windows: < > : " / \ | ? *
    # Unix: /
    dangerous_chars = r'[<>:"/\\|?*\x00-\x1f]'
    sanitized = re.sub(dangerous_chars, '_', filename)
    
    # Remove leading/trailing dots and spaces
    sanitized = sanitized.strip('. ')
    
    # Prevent reserved Windows filenames
    reserved_names = {
        'CON', 'PRN', 'AUX', 'NUL',
        'COM1', 'COM2', 'COM3', 'COM4', 'COM5', 'COM6', 'COM7', 'COM8', 'COM9',
        'LPT1', 'LPT2', 'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9'
    }
    
    name_without_ext = os.path.splitext(sanitized)[0].upper()
    if name_without_ext in reserved_names:
        sanitized = f"_{sanitized}"
    
    # Ensure filename is not empty after sanitization
    if not sanitized:
        sanitized = "unnamed_file"
    
    # Limit filename length (255 bytes is common filesystem limit)
    if len(sanitized.encode('utf-8')) > 255:
        name, ext = os.path.splitext(sanitized)
        max_name_length = 255 - len(ext.encode('utf-8')) - 1
        name = name.encode('utf-8')[:max_name_length].decode('utf-8', errors='ignore')
        sanitized = f"{name}{ext}"
    
    return sanitized


def prevent_path_traversal(base_path: str, user_path: str) -> str:
    """
    Prevent path traversal attacks by ensuring the resolved path
    stays within the base directory
    
    Args:
        base_path: Base directory that should contain the file
        user_path: User-provided path (potentially malicious)
        
    Returns:
        str: Safe absolute path
        
    Raises:
        ValueError: If path traversal is detected
        
    Requirements: 9.1, 9.2
    """
    # Resolve to absolute paths
    base = Path(base_path).resolve()
    
    # Combine and resolve the user path
    try:
        target = (base / user_path).resolve()
    except (ValueError, OSError) as e:
        raise ValueError(f"Invalid path: {e}")
    
    # Check if target is within base directory
    try:
        target.relative_to(base)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: '{user_path}' attempts to access outside '{base_path}'"
        )
    
    return str(target)


def validate_file_path(filepath: str, allowed_extensions: list = None) -> bool:
    """
    Validate file path for security issues
    
    Args:
        filepath: File path to validate
        allowed_extensions: List of allowed file extensions (e.g., ['.jpg', '.png'])
        
    Returns:
        bool: True if valid, False otherwise
        
    Requirements: 9.1
    """
    if not filepath or not isinstance(filepath, str):
        return False
    
    # Check for null bytes
    if '\x00' in filepath:
        return False
    
    # Check for path traversal patterns
    if '..' in filepath or filepath.startswith('/') or filepath.startswith('\\'):
        return False
    
    # Check file extension if provided
    if allowed_extensions:
        ext = os.path.splitext(filepath)[1].lower()
        if ext not in [e.lower() for e in allowed_extensions]:
            return False
    
    return True


def sanitize_service_name(service: str) -> str:
    """
    Sanitize service name to prevent injection attacks
    
    Args:
        service: Service name (e.g., 'patreon', 'fanbox')
        
    Returns:
        str: Sanitized service name
        
    Requirements: 9.1
    """
    if not service or not isinstance(service, str):
        return ""
    
    # Only allow alphanumeric characters and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_]', '', service)
    return sanitized.lower()


def sanitize_user_id(user_id: str) -> str:
    """
    Sanitize user ID to prevent injection attacks
    
    Args:
        user_id: User ID from URL
        
    Returns:
        str: Sanitized user ID
        
    Requirements: 9.1
    """
    if not user_id or not isinstance(user_id, str):
        return ""
    
    # Only allow alphanumeric characters, hyphens, and underscores
    sanitized = re.sub(r'[^a-zA-Z0-9_-]', '', user_id)
    return sanitized


def validate_post_id(post_id: str) -> bool:
    """
    Validate post ID format
    
    Args:
        post_id: Post ID to validate
        
    Returns:
        bool: True if valid format
        
    Requirements: 9.1
    """
    if not post_id or not isinstance(post_id, str):
        return False
    
    # Post IDs should be alphanumeric
    return bool(re.match(r'^[a-zA-Z0-9_-]+$', post_id))


def validate_integer_param(value: any, min_val: int = None, max_val: int = None) -> bool:
    """
    Validate integer parameter with optional range checking
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value (optional)
        max_val: Maximum allowed value (optional)
        
    Returns:
        bool: True if valid integer within range
        
    Requirements: 9.1
    """
    try:
        int_val = int(value)
        
        if min_val is not None and int_val < min_val:
            return False
        
        if max_val is not None and int_val > max_val:
            return False
        
        return True
    except (ValueError, TypeError):
        return False
