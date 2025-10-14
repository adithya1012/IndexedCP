"""
Filesystem-based storage that simulates IndexedDB using JSON files.
Stores chunks in ~/.indexcp/db/chunks.json
"""

import json
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
import base64


class FileSystemDB:
    """
    Simulates IndexedDB using filesystem storage.
    Compatible with the Node.js implementation.
    """
    
    def __init__(self, db_name: str, version: int = 1):
        self.db_name = db_name
        self.version = version
        self.db_path = Path.home() / '.indexcp' / 'db'
        self.store_path = self.db_path / 'chunks.json'
        self._ensure_db_dir()
    
    def _ensure_db_dir(self):
        """Create database directory if it doesn't exist."""
        if not self.db_path.exists():
            self.db_path.mkdir(parents=True, exist_ok=True)
    
    def _load_store(self) -> List[Dict[str, Any]]:
        """Load all records from the JSON file."""
        try:
            if self.store_path.exists():
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if isinstance(data, list) else []
        except (json.JSONDecodeError, IOError) as error:
            print(f'Warning: Failed to load store: {error}')
        return []
    
    def _save_store(self, records: List[Dict[str, Any]]):
        """Save all records to the JSON file."""
        try:
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump(records, f, indent=2)
        except IOError as error:
            print(f'Error: Failed to save store: {error}')
            raise
    
    def add(self, store_name: str, record: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add a record to the store.
        Converts binary data to base64 for JSON serialization.
        """
        records = self._load_store()
        
        # Convert bytes data to base64 for JSON serialization
        serialized_record = record.copy()
        if 'data' in serialized_record and isinstance(serialized_record['data'], bytes):
            serialized_record['data'] = base64.b64encode(serialized_record['data']).decode('utf-8')
        
        records.append(serialized_record)
        self._save_store(records)
        return record
    
    def get(self, store_name: str, key: str) -> Optional[Dict[str, Any]]:
        """
        Get a record by key.
        Converts base64 data back to bytes.
        """
        records = self._load_store()
        for record in records:
            if record.get('id') == key:
                # Convert base64 back to bytes
                if 'data' in record and isinstance(record['data'], str):
                    record['data'] = base64.b64decode(record['data'])
                return record
        return None
    
    def delete(self, store_name: str, key: str) -> bool:
        """Delete a record by key."""
        records = self._load_store()
        filtered_records = [r for r in records if r.get('id') != key]
        self._save_store(filtered_records)
        return True
    
    def get_all(self, store_name: str = None) -> List[Dict[str, Any]]:
        """
        Get all records from the store.
        Converts base64 data back to bytes.
        """
        records = self._load_store()
        
        # Convert base64 data back to bytes
        for record in records:
            if 'data' in record and isinstance(record['data'], str):
                record['data'] = base64.b64decode(record['data'])
        
        return records
    
    def clear(self, store_name: str = None):
        """Clear all records from the store."""
        self._save_store([])
    
    def count(self, store_name: str = None) -> int:
        """Get the count of records in the store."""
        records = self._load_store()
        return len(records)


def open_filesystem_db(db_name: str, version: int = 1, options: Dict = None) -> FileSystemDB:
    """
    Factory function to create a FileSystemDB instance.
    Compatible with the Node.js openFileSystemDB API.
    """
    db = FileSystemDB(db_name, version)
    
    # Run upgrade if provided (for API compatibility)
    if options and 'upgrade' in options:
        # Placeholder - filesystem DB doesn't need schema upgrades
        pass
    
    return db
