"""
IndexedCP Client for Python
Handles file chunking, buffering, and upload with filesystem-based storage.
"""

import os
import sys
import getpass
from pathlib import Path
from typing import Optional, Dict, List
import requests
from .filesystem_db import open_filesystem_db


class IndexCPClient:
    """
    Client for chunked file transfer with filesystem buffering.
    Compatible with the Node.js IndexedCP client.
    """
    
    def __init__(self):
        self.db = None
        self.db_name = 'indexcp'
        self.store_name = 'chunks'
        self.api_key = None
        self.chunk_size = 1024 * 1024  # 1MB chunks
    
    def _prompt_for_api_key(self) -> str:
        """Prompt user for API key securely."""
        api_key = getpass.getpass('Enter API key: ')
        return api_key.strip()
    
    def _get_api_key(self) -> str:
        """Get API key from instance, environment, or prompt user."""
        if self.api_key:
            return self.api_key
        
        # Check environment variable first
        if 'INDEXCP_API_KEY' in os.environ:
            self.api_key = os.environ['INDEXCP_API_KEY']
            return self.api_key
        
        # Prompt user for API key
        self.api_key = self._prompt_for_api_key()
        return self.api_key
    
    def _init_db(self):
        """Initialize the filesystem database."""
        if not self.db:
            self.db = open_filesystem_db(self.db_name, 1)
        return self.db
    
    def add_file(self, file_path: str) -> int:
        """
        Add a file to the buffer by reading it in chunks.
        
        Args:
            file_path: Path to the file to buffer
            
        Returns:
            Number of chunks created
        """
        db = self._init_db()
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")
        
        file_path = os.path.abspath(file_path)
        chunk_index = 0
        chunks = []
        
        try:
            with open(file_path, 'rb') as f:
                while True:
                    chunk_data = f.read(self.chunk_size)
                    if not chunk_data:
                        break
                    
                    chunks.append({
                        'id': f"{file_path}-{chunk_index}",
                        'fileName': file_path,
                        'chunkIndex': chunk_index,
                        'data': chunk_data
                    })
                    chunk_index += 1
            
            # Add all chunks to the database
            for chunk in chunks:
                db.add(self.store_name, chunk)
            
            print(f"File {file_path} added to buffer with {chunk_index} chunks")
            return chunk_index
            
        except IOError as error:
            raise IOError(f"Error reading file: {error}")
    
    def upload_buffered_files(self, server_url: str) -> Dict[str, str]:
        """
        Upload all buffered files to the server.
        
        Args:
            server_url: URL of the upload endpoint
            
        Returns:
            Dictionary mapping client filenames to server filenames
        """
        api_key = self._get_api_key()
        
        db = self._init_db()
        all_records = db.get_all(self.store_name)
        
        print(f"Found {len(all_records)} buffered chunks")
        
        if len(all_records) == 0:
            print("No buffered files to upload")
            return {}
        
        # Group records by fileName
        file_groups = {}
        for record in all_records:
            file_name = record['fileName']
            if file_name not in file_groups:
                file_groups[file_name] = []
            file_groups[file_name].append(record)
        
        print(f"Grouped into {len(file_groups)} files: {list(file_groups.keys())}")
        
        upload_results = {}  # Track server-determined filenames
        
        # Upload each file's chunks in order
        for file_name, chunks in file_groups.items():
            print(f"Uploading {file_name} with {len(chunks)} chunks...")
            
            # Sort chunks by index
            chunks.sort(key=lambda x: x['chunkIndex'])
            
            server_filename = None
            
            for chunk in chunks:
                print(f"Uploading chunk {chunk['chunkIndex']} for {file_name}")
                response = self._upload_chunk(
                    server_url, 
                    chunk['data'], 
                    chunk['chunkIndex'], 
                    file_name, 
                    api_key
                )
                
                # Capture server-determined filename from first chunk response
                if response and 'actualFilename' in response and not server_filename:
                    server_filename = response['actualFilename']
                
                # Delete chunk after successful upload
                db.delete(self.store_name, chunk['id'])
            
            # Store the mapping of client filename to server filename
            upload_results[file_name] = server_filename or os.path.basename(file_name)
            
            if server_filename and server_filename != os.path.basename(file_name):
                print(f"Upload complete for {file_name} -> Server saved as: {server_filename}")
            else:
                print(f"Upload complete for {file_name}")
        
        return upload_results
    
    def _upload_chunk(
        self, 
        server_url: str, 
        chunk_data: bytes, 
        index: int, 
        file_name: str, 
        api_key: Optional[str] = None
    ) -> Optional[Dict]:
        """
        Upload a single chunk to the server.
        
        Args:
            server_url: URL of the upload endpoint
            chunk_data: Binary data of the chunk
            index: Index of the chunk
            file_name: Name of the file
            api_key: API key for authentication
            
        Returns:
            Response data from server
        """
        if not api_key:
            api_key = self._get_api_key()
        
        headers = {
            'Content-Type': 'application/octet-stream',
            'X-Chunk-Index': str(index),
            'X-File-Name': file_name,
            'Authorization': f'Bearer {api_key}'
        }
        
        try:
            response = requests.post(server_url, headers=headers, data=chunk_data)
            
            if response.status_code == 401:
                raise Exception('Authentication failed: Invalid API key')
            
            if not response.ok:
                raise Exception(f'Upload failed: {response.status_code} {response.reason}')
            
            # Try to parse response as JSON
            try:
                response_data = response.json()
                
                # Log server-determined filename if it differs
                if ('actualFilename' in response_data and 
                    response_data['actualFilename'] != file_name and 
                    response_data['actualFilename'] != os.path.basename(file_name)):
                    print(f"Server used filename: {response_data['actualFilename']} (client sent: {file_name})")
                
                return response_data
            except ValueError:
                # Backward compatibility: plain text response
                return {'message': response.text}
                
        except requests.RequestException as error:
            raise Exception(f'Upload error: {error}')
    
    def buffer_and_upload(self, file_path: str, server_url: str):
        """
        Convenience method to buffer and immediately upload a file.
        
        Args:
            file_path: Path to the file to upload
            server_url: URL of the upload endpoint
        """
        self.add_file(file_path)
        return self.upload_buffered_files(server_url)
    
    def clear_buffer(self):
        """Clear all buffered chunks."""
        db = self._init_db()
        db.clear(self.store_name)
        print("Buffer cleared")
    
    def list_buffered_files(self) -> List[str]:
        """
        List all files currently in the buffer.
        
        Returns:
            List of unique filenames
        """
        db = self._init_db()
        all_records = db.get_all(self.store_name)
        
        # Get unique filenames
        file_names = set()
        for record in all_records:
            file_names.add(record['fileName'])
        
        return sorted(list(file_names))
