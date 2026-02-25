"""
Artist data model
"""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict
import json


@dataclass
class Artist:
    """Artist model representing a content creator"""
    
    service: str
    user_id: str
    name: str
    metadata: Optional[Dict] = field(default_factory=dict)
    last_updated: Optional[datetime] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        """Post initialization processing"""
        if self.last_updated is None:
            self.last_updated = datetime.now()
    
    @property
    def full_id(self) -> str:
        """Get full artist identifier (service:user_id)"""
        return f"{self.service}:{self.user_id}"
    
    @property
    def profile_url(self) -> str:
        """Get Kemono profile URL"""
        return f"https://kemono.cr/{self.service}/user/{self.user_id}"
    
    def to_dict(self) -> Dict:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'service': self.service,
            'user_id': self.user_id,
            'name': self.name,
            'full_id': self.full_id,
            'profile_url': self.profile_url,
            'metadata': self.metadata,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
    
    @classmethod
    def from_dict(cls, data: Dict) -> 'Artist':
        """Create Artist from dictionary"""
        # Parse metadata if it's a JSON string
        metadata = data.get('metadata')
        if isinstance(metadata, str):
            try:
                metadata = json.loads(metadata)
            except (json.JSONDecodeError, TypeError):
                metadata = {}
        
        # Parse datetime string
        last_updated = data.get('last_updated')
        if isinstance(last_updated, str):
            try:
                last_updated = datetime.fromisoformat(last_updated)
            except (ValueError, TypeError):
                last_updated = None
        
        return cls(
            id=data.get('id'),
            service=data['service'],
            user_id=data['user_id'],
            name=data['name'],
            metadata=metadata or {},
            last_updated=last_updated
        )
    
    @classmethod
    def from_api_response(cls, api_data: Dict) -> 'Artist':
        """Create Artist from Kemono API response"""
        return cls(
            service=api_data.get('service', ''),
            user_id=api_data.get('id', ''),
            name=api_data.get('name', 'Unknown'),
            metadata={
                'indexed': api_data.get('indexed'),
                'updated': api_data.get('updated'),
                'favorited': api_data.get('favorited', 0),
                'public_id': api_data.get('public_id')
            }
        )
    
    def update_metadata(self, metadata: Dict):
        """Update artist metadata"""
        self.metadata.update(metadata)
        self.last_updated = datetime.now()
    
    def __repr__(self) -> str:
        """String representation"""
        return f"Artist(service='{self.service}', user_id='{self.user_id}', name='{self.name}')"
