import hashlib
from typing import Dict


class HashCalculator:
    """Calculate cryptographic hashes for files"""

    @staticmethod
    def calculate_hashes(file_path: str) -> Dict[str, str]:
        """Calculate MD5, SHA-1, SHA-256, and SHA-512 hashes"""
        hashes = {
            "md5": hashlib.md5(),
            "sha1": hashlib.sha1(),
            "sha256": hashlib.sha256(),
            "sha512": hashlib.sha512(),
        }
        
        # Read file in chunks to handle large files efficiently
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                for hash_obj in hashes.values():
                    hash_obj.update(chunk)
        
        # Return hex digests
        return {
            name: hash_obj.hexdigest()
            for name, hash_obj in hashes.items()
        }

    @staticmethod
    def calculate_hash(file_path: str, algorithm: str = "sha256") -> str:
        """Calculate a single hash using specified algorithm"""
        hash_obj = hashlib.new(algorithm)
        
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                hash_obj.update(chunk)
        
        return hash_obj.hexdigest()
