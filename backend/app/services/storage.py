"""
Storage service abstraction for file management
Supports local filesystem and future S3-compatible storage
"""
import os
import shutil
import tempfile
from pathlib import Path
from typing import BinaryIO, Optional
from uuid import uuid4
import logging

logger = logging.getLogger(__name__)


class UploadTooLargeError(Exception):
    pass


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
        if Path(storage_key).name != storage_key or storage_key in {".", ".."}:
            raise ValueError("Invalid storage key")
        return self.base_path / storage_key

    def generate_storage_key(self, filename: str, image_format: Optional[str] = None) -> str:
        """
        Generate unique storage key for a file
        Uses UUID to prevent conflicts and path traversal
        
        Args:
            filename: Original filename
            
        Returns:
            Unique storage key
        """
        # Extract extension safely
        extension = {
            "JPEG": ".jpg",
            "PNG": ".png",
            "WEBP": ".webp",
            "GIF": ".gif",
            "BMP": ".bmp",
            "TIFF": ".tif",
            "AVIF": ".avif",
        }.get(image_format, Path(filename).suffix.lower())
        # Generate UUID-based key
        unique_id = str(uuid4())
        return f"{unique_id}{extension}"

    def stage_upload(self, file: BinaryIO, max_size: int) -> tuple[Path, int]:
        """Stream a request to a temporary file, enforcing the limit while reading."""
        staging_dir = self.base_path / ".staging"
        staging_dir.mkdir(parents=True, exist_ok=True)
        descriptor, path_string = tempfile.mkstemp(prefix="upload-", dir=staging_dir)
        staged_path = Path(path_string)
        size = 0
        try:
            with os.fdopen(descriptor, "wb") as destination:
                while chunk := file.read(64 * 1024):
                    size += len(chunk)
                    if size > max_size:
                        raise UploadTooLargeError
                    destination.write(chunk)
                destination.flush()
                os.fsync(destination.fileno())
            if size == 0:
                raise ValueError("Empty upload")
            return staged_path, size
        except Exception:
            staged_path.unlink(missing_ok=True)
            raise

    def promote(self, staged_path: Path, storage_key: str) -> Path:
        """Atomically move a validated staged file into permanent storage."""
        destination = self._get_storage_path(storage_key)
        os.replace(staged_path, destination)
        return destination

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

    def exists(self, storage_key: str) -> bool:
        """
        Check if file exists in storage
        
        Args:
            storage_key: Unique storage identifier
            
        Returns:
            True if file exists
        """
        return self._get_storage_path(storage_key).exists()

    def quarantine(self, storage_key: str) -> Optional[Path]:
        """Move evidence out of active storage until its database delete commits."""
        source = self.get(storage_key)
        if source is None:
            return None
        quarantine_dir = self.base_path / ".deleted"
        quarantine_dir.mkdir(parents=True, exist_ok=True)
        destination = quarantine_dir / f"{uuid4()}-{source.name}"
        os.replace(source, destination)
        return destination

    def restore_quarantined(self, quarantined_path: Path, storage_key: str) -> None:
        """Restore a quarantined file if the database transaction did not commit."""
        if quarantined_path.exists():
            os.replace(quarantined_path, self._get_storage_path(storage_key))

    @staticmethod
    def purge_quarantined(quarantined_path: Path) -> None:
        """Permanently remove a quarantined evidence file after commit."""
        quarantined_path.unlink(missing_ok=True)

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
