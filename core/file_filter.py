"""File type filtering module"""
from typing import List, Dict
import os


class FileFilter:
    """Fayl turlarini filtrlash"""
    
    FILE_TYPES = {
        'images': ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg'],
        'videos': ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.wmv'],
        'archives': ['.zip', '.rar', '.7z', '.tar', '.gz', '.bz2'],
        'audio': ['.mp3', '.wav', '.flac', '.ogg', '.m4a', '.aac']
    }
    
    def filter_files(self, files: List[Dict], filter_type: str) -> List[Dict]:
        """
        Fayllarni tanlangan tur bo'yicha filtrlash
        
        Args:
            files: Fayllar ro'yxati (har biri 'name' yoki 'path' key ga ega)
            filter_type: Filter turi ('all', 'images', 'videos', 'archives', 'audio')
        
        Returns:
            Filtrlangan fayllar ro'yxati
        """
        if filter_type == 'all' or not filter_type:
            return files
        
        if filter_type not in self.FILE_TYPES:
            return files
        
        filtered = []
        for file in files:
            filename = file.get('name') or file.get('path') or ''
            file_type = self.get_file_type(filename)
            if file_type == filter_type:
                filtered.append(file)
        
        return filtered
    
    def get_file_type(self, filename: str) -> str:
        """
        Fayl turini aniqlash
        
        Args:
            filename: Fayl nomi yoki yo'li
        
        Returns:
            Fayl turi ('images', 'videos', 'archives', 'audio', 'other')
        """
        if not filename:
            return 'other'
        
        # Fayl kengaytmasini olish
        _, ext = os.path.splitext(filename.lower())
        
        # Har bir tur bo'yicha tekshirish
        for file_type, extensions in self.FILE_TYPES.items():
            if ext in extensions:
                return file_type
        
        return 'other'
    
    def get_supported_extensions(self, filter_type: str = 'all') -> List[str]:
        """
        Qo'llab-quvvatlanadigan kengaytmalar ro'yxatini olish
        
        Args:
            filter_type: Filter turi
        
        Returns:
            Kengaytmalar ro'yxati
        """
        if filter_type == 'all' or not filter_type:
            all_extensions = []
            for extensions in self.FILE_TYPES.values():
                all_extensions.extend(extensions)
            return all_extensions
        
        return self.FILE_TYPES.get(filter_type, [])
    
    def count_by_type(self, files: List[Dict]) -> Dict[str, int]:
        """
        Fayllarni tur bo'yicha sanash
        
        Args:
            files: Fayllar ro'yxati
        
        Returns:
            Har bir tur uchun fayllar soni
        """
        counts = {
            'images': 0,
            'videos': 0,
            'archives': 0,
            'audio': 0,
            'other': 0
        }
        
        for file in files:
            filename = file.get('name') or file.get('path') or ''
            file_type = self.get_file_type(filename)
            counts[file_type] = counts.get(file_type, 0) + 1
        
        return counts
