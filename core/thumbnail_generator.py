"""Thumbnail generation module"""
import os
import hashlib
from typing import Optional, List, Tuple
from PIL import Image


class ThumbnailGenerator:
    """ThumbnailGenerator class (Pillow)"""
    
    def __init__(self, thumbnail_size: Tuple[int, int] = (200, 200)):
        """
        Initialize thumbnail generator
        
        Args:
            thumbnail_size: Tuple of (width, height) for thumbnails
        """
        self.thumbnail_size = thumbnail_size
        self.supported_formats = {'.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp'}
    
    def generate_thumbnail(self, image_path: str, output_dir: str) -> Optional[str]:
        """
        Generate thumbnail metodi (200x200 px)
        
        Args:
            image_path: Path to source image
            output_dir: Directory to save thumbnail
        
        Returns:
            Path to generated thumbnail or None if failed
        """
        try:
            # Check if file exists
            if not os.path.exists(image_path):
                return None
            
            # Check if file format is supported
            _, ext = os.path.splitext(image_path.lower())
            if ext not in self.supported_formats:
                return None
            
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Generate unique thumbnail filename based on source path hash
            file_hash = hashlib.md5(image_path.encode()).hexdigest()
            thumbnail_filename = f"thumb_{file_hash}.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)
            
            # Skip if thumbnail already exists
            if os.path.exists(thumbnail_path):
                return thumbnail_path
            
            # Open and process image
            with Image.open(image_path) as img:
                # Convert to RGB if necessary (for PNG with transparency, etc.)
                if img.mode in ('RGBA', 'LA', 'P'):
                    # Create white background
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    if img.mode == 'P':
                        img = img.convert('RGBA')
                    background.paste(img, mask=img.split()[-1] if img.mode in ('RGBA', 'LA') else None)
                    img = background
                elif img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Create thumbnail maintaining aspect ratio
                img.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
                
                # Save thumbnail
                img.save(thumbnail_path, 'JPEG', quality=85, optimize=True)
            
            return thumbnail_path
        
        except Exception as e:
            print(f"Error generating thumbnail for {image_path}: {str(e)}")
            return None
    
    def generate_thumbnails_batch(self, image_paths: List[str], output_dir: str) -> List[Optional[str]]:
        """
        Batch thumbnail generation
        
        Args:
            image_paths: List of paths to source images
            output_dir: Directory to save thumbnails
        
        Returns:
            List of paths to generated thumbnails (None for failed ones)
        """
        thumbnails = []
        
        for image_path in image_paths:
            thumbnail_path = self.generate_thumbnail(image_path, output_dir)
            thumbnails.append(thumbnail_path)
        
        return thumbnails
    
    def regenerate_thumbnail(self, image_path: str, output_dir: str, force: bool = False) -> Optional[str]:
        """
        Regenerate thumbnail (useful if thumbnail is corrupted or size changed)
        
        Args:
            image_path: Path to source image
            output_dir: Directory to save thumbnail
            force: Force regeneration even if thumbnail exists
        
        Returns:
            Path to generated thumbnail or None if failed
        """
        if force:
            # Delete existing thumbnail
            file_hash = hashlib.md5(image_path.encode()).hexdigest()
            thumbnail_filename = f"thumb_{file_hash}.jpg"
            thumbnail_path = os.path.join(output_dir, thumbnail_filename)
            
            if os.path.exists(thumbnail_path):
                try:
                    os.remove(thumbnail_path)
                except Exception as e:
                    print(f"Error removing old thumbnail: {str(e)}")
        
        return self.generate_thumbnail(image_path, output_dir)
    
    def get_thumbnail_path(self, image_path: str, output_dir: str) -> str:
        """
        Get expected thumbnail path without generating it
        
        Args:
            image_path: Path to source image
            output_dir: Directory where thumbnail would be saved
        
        Returns:
            Expected path to thumbnail
        """
        file_hash = hashlib.md5(image_path.encode()).hexdigest()
        thumbnail_filename = f"thumb_{file_hash}.jpg"
        return os.path.join(output_dir, thumbnail_filename)
    
    def thumbnail_exists(self, image_path: str, output_dir: str) -> bool:
        """
        Check if thumbnail already exists
        
        Args:
            image_path: Path to source image
            output_dir: Directory where thumbnail would be saved
        
        Returns:
            True if thumbnail exists, False otherwise
        """
        thumbnail_path = self.get_thumbnail_path(image_path, output_dir)
        return os.path.exists(thumbnail_path)
    
    def cleanup_orphaned_thumbnails(self, output_dir: str, valid_image_paths: List[str]) -> int:
        """
        Remove thumbnails that don't have corresponding source images
        
        Args:
            output_dir: Directory containing thumbnails
            valid_image_paths: List of valid source image paths
        
        Returns:
            Number of thumbnails removed
        """
        if not os.path.exists(output_dir):
            return 0
        
        # Create set of valid thumbnail filenames
        valid_thumbnails = set()
        for image_path in valid_image_paths:
            file_hash = hashlib.md5(image_path.encode()).hexdigest()
            valid_thumbnails.add(f"thumb_{file_hash}.jpg")
        
        # Remove orphaned thumbnails
        removed_count = 0
        for filename in os.listdir(output_dir):
            if filename.startswith('thumb_') and filename.endswith('.jpg'):
                if filename not in valid_thumbnails:
                    try:
                        os.remove(os.path.join(output_dir, filename))
                        removed_count += 1
                    except Exception as e:
                        print(f"Error removing orphaned thumbnail {filename}: {str(e)}")
        
        return removed_count
