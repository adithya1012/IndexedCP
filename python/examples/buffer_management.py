"""
Example: Buffer management
Demonstrates managing the buffer - adding, listing, and clearing files.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.client import IndexCPClient


def buffer_management_example():
    """Example of managing buffered files."""
    
    client = IndexCPClient()
    
    # Create some test files
    test_files = []
    for i in range(3):
        filename = f'test_file_{i}.txt'
        with open(filename, 'w') as f:
            f.write(f'This is test file {i}\n' * 20)
        test_files.append(filename)
        print(f"Created: {filename}")
    
    print("\n" + "="*50)
    print("1. Adding files to buffer...")
    print("="*50)
    for filename in test_files:
        client.add_file(filename)
    
    print("\n" + "="*50)
    print("2. Listing buffered files...")
    print("="*50)
    buffered_files = client.list_buffered_files()
    print(f"Total buffered files: {len(buffered_files)}")
    for filename in buffered_files:
        print(f"  - {filename}")
    
    print("\n" + "="*50)
    print("3. Checking buffer storage location...")
    print("="*50)
    db = client._init_db()
    print(f"Storage path: {db.store_path}")
    print(f"Total chunks: {db.count()}")
    
    print("\n" + "="*50)
    print("4. Clearing buffer...")
    print("="*50)
    client.clear_buffer()
    
    print("\n" + "="*50)
    print("5. Verifying buffer is empty...")
    print("="*50)
    buffered_files = client.list_buffered_files()
    print(f"Buffered files after clear: {len(buffered_files)}")
    
    # Clean up test files
    print("\n" + "="*50)
    print("6. Cleaning up test files...")
    print("="*50)
    for filename in test_files:
        if os.path.exists(filename):
            os.remove(filename)
            print(f"Removed: {filename}")


if __name__ == '__main__':
    buffer_management_example()
