"""
Download data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
import json


@dataclass
class Download:
    """Download model representing a download task"""
    
    task_id: str
    url: str
    service: Optional[str] = None
    user_id: Optional[str] = None
    post_id: Optional[str] = None
    status: str = 'pending'  # pending, downloading, paused, completed, failed
    total_files: int = 0
    downloaded_files: int = 0
    filters: Optional[Dict] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Post initialization processing"""
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()
    
    @property
    def progress_percent(self) -> float:
        """Calculate download progress percentage"""
        if self.total_files == 0:
            return 0.0
        return (self.downloaded_files / self.total_files) * 100
    
    @property
    def is_active(self) -> bool:
        """Check if download is active"""
        return self.status in ['pending', 'downloading']
    
    @property
    def is_completed(self) -> bool:
        """Check if download is completed"""
        return self.status == 'completed'
    
    @property
    def is_paused(self) -> bool:
        """Check if download is paused"""
        return self.status == 'paused'
    
    @property
    def is_failed(self) -> bool:
        """Check if download failed"""
        return self.status == 'failed'
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'task_id': self.task_id,
            'url': self.url,
            'service': self.service,
            'user_id': self.user_id,
            'post_id': self.post_id,
            'status': self.status,
            'total_files': self.total_files,
            'downloaded_files': self.downloaded_files,
            'progress_percent': self.progress_percent,
            'filters': self.filters,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Download':
        """Create Download from dictionary"""
        # Parse filters if it's a JSON string
        filters = data.get('filters')
        if isinstance(filters, str):
            try:
                filters = json.loads(filters)
            except (json.JSONDecodeError, TypeError):
                filters = {}
        
        # Parse datetime strings
        created_at = data.get('created_at')
        if isinstance(created_at, str):
            try:
                created_at = datetime.fromisoformat(created_at)
            except (ValueError, TypeError):
                created_at = None
        
        updated_at = data.get('updated_at')
        if isinstance(updated_at, str):
            try:
                updated_at = datetime.fromisoformat(updated_at)
            except (ValueError, TypeError):
                updated_at = None
        
        return cls(
            id=data.get('id'),
            task_id=data['task_id'],
            url=data['url'],
            service=data.get('service'),
            user_id=data.get('user_id'),
            post_id=data.get('post_id'),
            status=data.get('status', 'pending'),
            total_files=data.get('total_files', 0),
            downloaded_files=data.get('downloaded_files', 0),
            filters=filters or {},
            created_at=created_at,
            updated_at=updated_at
        )
    
    def update_progress(self, downloaded_files: int, total_files: int = None):
        """Update download progress"""
        self.downloaded_files = downloaded_files
        if total_files is not None:
            self.total_files = total_files
        self.updated_at = datetime.now()
    
    def set_status(self, status: str):
        """Update download status"""
        self.status = status
        self.updated_at = datetime.now()
    
    def __repr__(self) -> str:
        """String representation"""
        return (f"Download(task_id='{self.task_id}', status='{self.status}', "
                f"progress={self.progress_percent:.1f}%)")
