"""
Centralized error handling and logging module
"""
import logging
import traceback
from functools import wraps
from flask import jsonify, request
from requests.exceptions import RequestException, Timeout, ConnectionError


# Configure logging
def setup_logging(log_file='data/webapp.log', log_level=logging.INFO):
    """
    Setup application logging
    
    Args:
        log_file: Path to log file
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        
    Requirements: 9.4, 9.5
    """
    # Create logger
    logger = logging.getLogger('kemono_webapp')
    logger.setLevel(log_level)
    
    # Prevent duplicate handlers
    if logger.handlers:
        return logger
    
    # File handler
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(log_level)
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    
    # Formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    file_handler.setFormatter(formatter)
    console_handler.setFormatter(formatter)
    
    logger.addHandler(file_handler)
    logger.addHandler(console_handler)
    
    return logger


# Get logger instance
logger = setup_logging()


class APIError(Exception):
    """
    Custom exception for API errors
    
    Requirements: 9.3, 9.5
    """
    def __init__(self, message, code='API_ERROR', status_code=500, details=None):
        self.message = message
        self.code = code
        self.status_code = status_code
        self.details = details
        super().__init__(self.message)


class ValidationError(Exception):
    """
    Custom exception for validation errors
    
    Requirements: 9.1, 9.5
    """
    def __init__(self, message, field=None):
        self.message = message
        self.field = field
        super().__init__(self.message)


def handle_api_error(error):
    """
    Handle API errors and return JSON response
    
    Args:
        error: Exception object
        
    Returns:
        tuple: (JSON response, status code)
        
    Requirements: 9.3, 9.5
    """
    if isinstance(error, APIError):
        logger.error(f"API Error: {error.code} - {error.message}")
        return jsonify({
            'success': False,
            'error': {
                'code': error.code,
                'message': error.message,
                'details': error.details
            }
        }), error.status_code
    
    elif isinstance(error, ValidationError):
        logger.warning(f"Validation Error: {error.message}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': error.message,
                'field': error.field
            }
        }), 400
    
    elif isinstance(error, Timeout):
        logger.error(f"Timeout Error: {str(error)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'TIMEOUT_ERROR',
                'message': "So'rov vaqti tugadi",
                'details': str(error)
            }
        }), 504
    
    elif isinstance(error, ConnectionError):
        logger.error(f"Connection Error: {str(error)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'CONNECTION_ERROR',
                'message': "Tarmoqqa ulanishda xatolik",
                'details': str(error)
            }
        }), 503
    
    elif isinstance(error, RequestException):
        logger.error(f"Request Error: {str(error)}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'REQUEST_ERROR',
                'message': "So'rov yuborishda xatolik",
                'details': str(error)
            }
        }), 500
    
    else:
        logger.error(f"Unexpected Error: {str(error)}\n{traceback.format_exc()}")
        return jsonify({
            'success': False,
            'error': {
                'code': 'INTERNAL_ERROR',
                'message': "Ichki server xatoligi",
                'details': str(error)
            }
        }), 500


def api_error_handler(f):
    """
    Decorator for handling errors in API endpoints
    
    Usage:
        @api_error_handler
        def my_api_endpoint():
            ...
            
    Requirements: 9.3, 9.5
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except Exception as e:
            return handle_api_error(e)
    return decorated_function


def log_request():
    """
    Log incoming request details
    
    Requirements: 9.4
    """
    logger.info(f"{request.method} {request.path} - IP: {request.remote_addr}")


def log_error(error, context=None):
    """
    Log error with context
    
    Args:
        error: Exception object
        context: Additional context information (dict)
        
    Requirements: 9.4, 9.5
    """
    error_msg = f"Error: {str(error)}"
    
    if context:
        error_msg += f" | Context: {context}"
    
    logger.error(error_msg)
    logger.debug(traceback.format_exc())


def create_success_response(data=None, message=None):
    """
    Create standardized success response
    
    Args:
        data: Response data
        message: Success message
        
    Returns:
        dict: JSON response
        
    Requirements: 9.5
    """
    response = {'success': True}
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return jsonify(response)


def create_error_response(message, code='ERROR', status_code=400, details=None):
    """
    Create standardized error response
    
    Args:
        message: Error message
        code: Error code
        status_code: HTTP status code
        details: Additional error details
        
    Returns:
        tuple: (JSON response, status code)
        
    Requirements: 9.5
    """
    return jsonify({
        'success': False,
        'error': {
            'code': code,
            'message': message,
            'details': details
        }
    }), status_code


def retry_on_failure(max_retries=3, backoff_factor=2, exceptions=(RequestException,)):
    """
    Decorator for retrying failed operations
    
    Args:
        max_retries: Maximum number of retry attempts
        backoff_factor: Exponential backoff multiplier
        exceptions: Tuple of exceptions to catch and retry
        
    Usage:
        @retry_on_failure(max_retries=3)
        def download_file():
            ...
            
    Requirements: 9.3
    """
    def decorator(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            import time
            
            last_exception = None
            
            for attempt in range(max_retries):
                try:
                    return f(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_retries - 1:
                        wait_time = backoff_factor ** attempt
                        logger.warning(
                            f"Attempt {attempt + 1}/{max_retries} failed: {str(e)}. "
                            f"Retrying in {wait_time}s..."
                        )
                        time.sleep(wait_time)
                    else:
                        logger.error(
                            f"All {max_retries} attempts failed for {f.__name__}: {str(e)}"
                        )
            
            # If all retries failed, raise the last exception
            raise last_exception
        
        return wrapper
    return decorator


def safe_int(value, default=0, min_val=None, max_val=None):
    """
    Safely convert value to integer with bounds checking
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        
    Returns:
        int: Converted integer value
        
    Requirements: 9.1
    """
    try:
        result = int(value)
        
        if min_val is not None and result < min_val:
            return min_val
        
        if max_val is not None and result > max_val:
            return max_val
        
        return result
    except (ValueError, TypeError):
        return default


def safe_str(value, default='', max_length=None):
    """
    Safely convert value to string with length checking
    
    Args:
        value: Value to convert
        default: Default value if conversion fails
        max_length: Maximum allowed length
        
    Returns:
        str: Converted string value
        
    Requirements: 9.1
    """
    try:
        result = str(value)
        
        if max_length and len(result) > max_length:
            return result[:max_length]
        
        return result
    except (ValueError, TypeError):
        return default
