"""
Configuration management for Kemono WebApp
"""
import json
import os
from pathlib import Path
from typing import Dict, Any


class Config:
    """Application configuration manager"""
    
    # Default configuration
    DEFAULT_CONFIG = {
        "api_base_url": "https://kemono.cr/api/v1",
        "download_path": "downloads",
        "library_path": "./library",
        "max_concurrent_downloads": 3,
        "theme": "dark",
        "language": "en",
        "cache_ttl": 300,
        "thumbnail_size": [200, 200],
        "flask_host": "0.0.0.0",
        "flask_port": 5000,
        "flask_debug": True
    }
    
    def __init__(self, config_path: str = "data/config.json"):
        self.config_path = config_path
        self.config = self.load_config()
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                    # Merge with defaults to ensure all keys exist
                    config = self.DEFAULT_CONFIG.copy()
                    config.update(loaded_config)
                    return config
            except (json.JSONDecodeError, IOError) as e:
                print(f"Error loading config: {e}. Using default configuration.")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self.save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def save_config(self, config: Dict[str, Any] = None) -> bool:
        """Save configuration to JSON file"""
        if config is None:
            config = self.config
        
        try:
            # Ensure directory exists
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Error saving config: {e}")
            return False
    
    def get(self, key: str, default=None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any) -> bool:
        """Set configuration value and save"""
        self.config[key] = value
        return self.save_config()
    
    def update(self, updates: Dict[str, Any]) -> bool:
        """Update multiple configuration values"""
        self.config.update(updates)
        return self.save_config()
    
    def reset_to_default(self) -> bool:
        """Reset configuration to default values"""
        self.config = self.DEFAULT_CONFIG.copy()
        return self.save_config()


def create_default_config(config_path: str = "data/config.json"):
    """Create default configuration file"""
    config = Config(config_path)
    print(f"Default configuration created at: {config_path}")
    return config


# Global config instance
config = Config()
