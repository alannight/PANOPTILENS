"""
Storage service abstraction for file management
Supports local filesystem and future S3-compatible storage
"""
import os
import shutil
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class StorageService:
    """
    Abstraction layer for file storage operations
    Currently implements local filesystem storage
    Can be extended for S3/MinIO in production
    """

    def __init__(self, base_path: str = None):
        """
        Initialize storage service
        
        Args:
            base_path: Base directory for file storage (default: ./uploads)
        """
        self.base_path = Path(base_path or os.getenv("UPLOAD_DIR", "./uploads"))
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"Storage service initialized with base path: {self.base_path}")

    def _get_storage_path(self, storage_key: str) -> Path:
        """
        Get full filesystem path for a storage key
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            Full path to file
        """
        return self.base_path / storage_key

    def generate_storage_key(self, filename: str) -> str:
        """
        Generate unique storage key for a file
        Uses UUID to prevent conflicts and path traversal
        
        Args:
            filename: Original filename
            
        Returns:
            Unique storage key
        """
        # Extract extension safely
        extension = Path(filename).suffix.lower()
        # Generate UUID-based key
        unique_id = str(uuid4())
        return f"{unique_id}{extension}"

    def save(self, file: BinaryIO, storage_key: str) -> str:
        """
        Save file to storage
        
        Args:
            file: File-like object to save
            storage_key: Unique storage identifier
            
        Returns:
            Storage key (path/identifier)
            
        Raises:
            IOError: If file save fails
        """
        try:
            file_path = self._get_storage_path(storage_key)
            
            # Ensure parent directory exists
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Save file
            with open(file_path, 'wb') as destination:
                shutil.copyfileobj(file, destination)
            
            logger.info(f"File saved to storage: {storage_key}")
            return storage_key
            
        except Exception as e:
            logger.error(f"Failed to save file {storage_key}: {str(e)}")
            raise IOError(f"Failed to save file: {str(e)}")

    def save_from_path(self, source_path: str, storage_key: str) -> str:
        """
        Save file from filesystem path
        
        Args:
            source_path: Path to source file
            storage_key: Unique storage identifier
            
        Returns:
            Storage key
            
        Raises:
            IOError: If file save fails
        """
        try:
            file_path = self._get_storage_path(storage_key)
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            shutil.copy2(source_path, file_path)
            
            logger.info(f"File copied to storage: {storage_key}")
            return storage_key
            
        except Exception as e:
            logger.error(f"Failed to copy file {storage_key}: {str(e)}")
            raise IOError(f"Failed to copy file: {str(e)}")

    def get(self, storage_key: str) -> Optional[Path]:
        """
        Get path to stored file
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            Path to file if exists, None otherwise
        """
        file_path = self._get_storage_path(storage_key)
        return file_path if file_path.exists() else None

    def get_url(self, storage_key: str) -> str:
        """
        Get URL for accessing file (for local storage, returns relative path)
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            URL/path to access file
        """
        # For local storage, return relative path
        # In production with S3, this would return signed URL
        return f"/uploads/{storage_key}"

    def exists(self, storage_key: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            True if file exists
        """
        return self._get_storage_path(storage_key).exists()

    def delete(self, storage_key: str) -> bool:
        """
        Delete file from storage
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            True if file was deleted, False if file didn't exist
            
        Raises:
            IOError: If deletion fails
        """
        try:
            file_path = self._get_storage_path(storage_key)
            
            if not file_path.exists():
                logger.warning(f"Attempted to delete non-existent file: {storage_key}")
                return False
            
            file_path.unlink()
            logger.info(f"File deleted from storage: {storage_key}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to delete file {storage_key}: {str(e)}")
            raise IOError(f"Failed to delete file: {str(e)}")

    def get_size(self, storage_key: str) -> Optional[int]:
        """
        Get file size in bytes
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            File size in bytes, None if file doesn't exist
        """
        file_path = self._get_storage_path(storage_key)
        return file_path.stat().st_size if file_path.exists() else None


# Global storage service instance
storage_service = StorageService()
