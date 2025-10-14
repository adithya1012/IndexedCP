"""
Example: Client-only usage
Demonstrates adding files to buffer and uploading them.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.client import IndexCPClient


def client_example():
    """Example of using IndexCPClient to buffer and upload files."""
    
    # Create a test file if it doesn't exist
    test_file = 'test_upload.txt'
    if not os.path.exists(test_file):
        with open(test_file, 'w') as f:
            f.write('This is a test file for IndexedCP Python client.\n' * 100)
        print(f"Created test file: {test_file}")
    
    # Initialize client
    client = IndexCPClient()
    
    # Add file to buffer
    print(f"\n1. Adding file to buffer...")
    client.add_file(test_file)
    
    # List buffered files
    print(f"\n2. Listing buffered files...")
    buffered_files = client.list_buffered_files()
    print(f"Buffered files: {buffered_files}")
    
    # Upload to server (make sure server is running!)
    print(f"\n3. Uploading to server...")
    server_url = 'http://localhost:3000/upload'
    
    # Set API key (or use INDEXCP_API_KEY environment variable)
    # client.api_key = 'your-api-key-here'
    
    try:
        upload_results = client.upload_buffered_files(server_url)
        print(f"\nUpload results: {upload_results}")
    except Exception as e:
        print(f"\nUpload failed: {e}")
        print("Make sure the server is running!")
    
    # Clean up
    if os.path.exists(test_file):
        os.remove(test_file)
        print(f"\nCleaned up test file: {test_file}")


if __name__ == '__main__':
    client_example()
