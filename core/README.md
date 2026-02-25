# Core Modules

## Security Module (`security.py`)

Input validation and sanitization functions.

### Usage Examples

```python
from core.security import (
    validate_kemono_url,
    sanitize_filename,
    prevent_path_traversal,
    validate_file_path,
    sanitize_service_name,
    sanitize_user_id,
    validate_post_id
)

# Validate Kemono URL
url = "https://kemono.cr/patreon/user/12345"
if validate_kemono_url(url):
    print("Valid URL")

# Sanitize filename
unsafe_filename = "../../../etc/passwd"
safe_filename = sanitize_filename(unsafe_filename)  # Returns: ".._.._.._.._etc_passwd"

# Prevent path traversal
base_path = "/app/downloads"
user_path = "../../../etc/passwd"
try:
    safe_path = prevent_path_traversal(base_path, user_path)
except ValueError as e:
    print(f"Path traversal detected: {e}")

# Validate file path
if validate_file_path("images/photo.jpg", allowed_extensions=['.jpg', '.png']):
    print("Valid file path")

# Sanitize service name
service = sanitize_service_name("patreon'; DROP TABLE users;--")  # Returns: "patreon"

# Sanitize user ID
user_id = sanitize_user_id("user<script>alert('xss')</script>")  # Returns: "userscriptalertxssscript"

# Validate post ID
if validate_post_id("post-12345"):
    print("Valid post ID")
```

## Error Handler Module (`error_handler.py`)

Centralized error handling and logging.

### Usage Examples

```python
from core.error_handler import (
    logger,
    APIError,
    ValidationError,
    api_error_handler,
    retry_on_failure,
    create_success_response,
    create_error_response
)

# Logging
logger.info("Application started")
logger.warning("Low disk space")
logger.error("Failed to connect to API")

# Raise custom errors
raise APIError("Failed to fetch data", code="API_FETCH_ERROR", status_code=503)
raise ValidationError("Invalid URL format", field="url")

# Use decorator for API endpoints
@api_error_handler
def my_api_endpoint():
    if not valid:
        raise ValidationError("Invalid input")
    return create_success_response(data={"result": "success"})

# Use retry decorator
@retry_on_failure(max_retries=3, backoff_factor=2)
def download_file(url):
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    return response.content

# Create responses
success_response = create_success_response(
    data={"posts": posts},
    message="Posts fetched successfully"
)

error_response = create_error_response(
    message="Invalid URL",
    code="INVALID_URL",
    status_code=400,
    details="URL must start with https://kemono.cr/"
)
```

### Flask Route Example

```python
from flask import Blueprint, request
from core.error_handler import api_error_handler, ValidationError, create_success_response
from core.security import validate_kemono_url, sanitize_filename

api_bp = Blueprint('api', __name__)

@api_bp.route('/download', methods=['POST'])
@api_error_handler
def start_download():
    # Get and validate input
    url = request.json.get('url')
    
    if not validate_kemono_url(url):
        raise ValidationError("Invalid Kemono URL", field="url")
    
    # Sanitize filename
    filename = sanitize_filename(request.json.get('filename', 'download'))
    
    # Process download
    task_id = download_manager.add_download(url, filename)
    
    return create_success_response(
        data={"task_id": task_id},
        message="Download started"
    )
```

## Requirements Coverage

- **9.1**: Input validation (URL, filename, path, service name, user ID, post ID)
- **9.2**: SQL injection and XSS prevention through sanitization
- **9.3**: Retry mechanism with exponential backoff
- **9.4**: Comprehensive logging setup (file and console)
- **9.5**: Standardized error responses and error handling
