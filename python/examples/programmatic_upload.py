"""
Example: Programmatic file upload
Demonstrates the buffer_and_upload convenience method.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.client import IndexCPClient


def programmatic_upload_example():
    """Example of programmatically uploading a file."""
    
    # Create a test file
    test_file = 'programmatic_test.txt'
    with open(test_file, 'w') as f:
        f.write('Programmatic upload test.\n' * 50)
    print(f"Created test file: {test_file}")
    
    # Initialize client
    client = IndexCPClient()
    
    # Set API key (or use INDEXCP_API_KEY environment variable)
    client.api_key = os.environ.get('INDEXCP_API_KEY', 'your-api-key-here')
    
    # Buffer and upload in one call
    server_url = 'http://localhost:3000/upload'
    
    try:
        print(f"Uploading {test_file} to {server_url}...")
        upload_results = client.buffer_and_upload(test_file, server_url)
        print(f"Upload successful!")
        print(f"Results: {upload_results}")
    except Exception as e:
        print(f"Upload failed: {e}")
        print("Make sure the server is running and API key is correct!")
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"Cleaned up test file: {test_file}")


if __name__ == '__main__':
    programmatic_upload_example()
