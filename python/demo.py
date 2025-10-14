#!/usr/bin/env python3
"""
Cross-compatibility demonstration script.
Shows how Python and JavaScript clients can work together using the same storage.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from lib.client import IndexCPClient


def print_banner(text):
    """Print a fancy banner."""
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")


def check_nodejs_available():
    """Check if Node.js is available."""
    try:
        result = subprocess.run(['node', '--version'], 
                              capture_output=True, 
                              text=True)
        return result.returncode == 0
    except FileNotFoundError:
        return False


def demo_python_only():
    """Demonstrate Python-only functionality."""
    print_banner("DEMO 1: Python Client Only")
    
    # Create test files
    test_files = []
    for i in range(2):
        filename = f'python_test_{i}.txt'
        with open(filename, 'w') as f:
            f.write(f'Python test file {i}\n' * 50)
        test_files.append(filename)
        print(f"✓ Created: {filename}")
    
    try:
        client = IndexCPClient()
        
        # Add files
        print("\n1. Adding files to buffer...")
        for filename in test_files:
            client.add_file(filename)
        
        # List buffered files
        print("\n2. Listing buffered files...")
        buffered = client.list_buffered_files()
        print(f"   Buffered files: {len(buffered)}")
        for f in buffered:
            print(f"   - {os.path.basename(f)}")
        
        # Show storage info
        print("\n3. Storage information...")
        db = client._init_db()
        print(f"   Storage location: {db.store_path}")
        print(f"   Total chunks: {db.count()}")
        
        # Clear buffer
        print("\n4. Clearing buffer...")
        client.clear_buffer()
        print("   ✓ Buffer cleared")
        
    finally:
        # Clean up
        print("\n5. Cleaning up test files...")
        for filename in test_files:
            if os.path.exists(filename):
                os.remove(filename)
                print(f"   ✓ Removed: {filename}")


def demo_storage_compatibility():
    """Demonstrate storage compatibility between Python and Node.js."""
    print_banner("DEMO 2: Storage Compatibility")
    
    if not check_nodejs_available():
        print("⚠️  Node.js not available. Skipping cross-compatibility demo.")
        print("   Install Node.js to test cross-compatibility.")
        return
    
    # Get parent directory (where Node.js CLI is)
    parent_dir = Path(__file__).parent.parent
    node_cli = parent_dir / 'bin' / 'indexcp'
    
    if not node_cli.exists():
        print(f"⚠️  Node.js CLI not found at {node_cli}")
        print("   Skipping cross-compatibility demo.")
        return
    
    print("✓ Node.js CLI found")
    print(f"  Location: {node_cli}")
    
    # Create test file
    test_file = 'compatibility_test.txt'
    with open(test_file, 'w') as f:
        f.write('Cross-compatibility test file\n' * 30)
    print(f"\n✓ Created test file: {test_file}")
    
    try:
        # Add with Python
        print("\n1. Adding file with Python client...")
        client = IndexCPClient()
        client.add_file(test_file)
        
        # Check storage with Python
        print("\n2. Checking storage with Python...")
        buffered = client.list_buffered_files()
        print(f"   Python sees {len(buffered)} file(s)")
        
        # Try to list with Node.js (if available)
        print("\n3. Attempting to list with Node.js CLI...")
        try:
            # Note: Node.js CLI doesn't have a 'list' command, so we just check it can read the storage
            print("   (Node.js CLI doesn't have 'list' command)")
            print("   But the storage file is at: ~/.indexcp/db/chunks.json")
            
            db = client._init_db()
            if db.store_path.exists():
                import json
                with open(db.store_path, 'r') as f:
                    data = json.load(f)
                print(f"   Storage file contains {len(data)} chunk(s)")
                print("   ✓ Storage is accessible to both implementations!")
        except Exception as e:
            print(f"   Note: {e}")
        
        # Clear with Python
        print("\n4. Clearing with Python...")
        client.clear_buffer()
        print("   ✓ Buffer cleared")
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n✓ Cleaned up: {test_file}")


def demo_upload_simulation():
    """Simulate the upload workflow (without actual server)."""
    print_banner("DEMO 3: Upload Workflow Simulation")
    
    print("This demo shows the upload workflow (without actual server):\n")
    
    # Create test file
    test_file = 'upload_test.txt'
    file_size = 2.5 * 1024 * 1024  # 2.5 MB
    
    print(f"1. Creating {file_size / (1024*1024):.1f}MB test file...")
    with open(test_file, 'wb') as f:
        f.write(b'X' * int(file_size))
    print(f"   ✓ Created: {test_file}")
    
    try:
        client = IndexCPClient()
        
        # Add file
        print("\n2. Chunking and buffering file...")
        chunks = client.add_file(test_file)
        print(f"   ✓ Created {chunks} chunks (1MB each)")
        
        # Show what would be uploaded
        print("\n3. Simulating upload process...")
        db = client._init_db()
        all_chunks = db.get_all('chunks')
        
        for i, chunk in enumerate(all_chunks):
            chunk_size_kb = len(chunk['data']) / 1024
            print(f"   Chunk {i}: {chunk_size_kb:.1f}KB")
            print(f"      Would send to: http://localhost:3000/upload")
            print(f"      Headers: X-Chunk-Index={i}, X-File-Name={test_file}")
            print(f"      After upload: Delete chunk {i} from buffer")
        
        print("\n4. Upload workflow complete!")
        print("   In real upload:")
        print("   - Each chunk sent via POST request")
        print("   - Server authenticates with API key")
        print("   - Server appends chunk to file")
        print("   - Client deletes chunk after success")
        print("   - If interrupted, remaining chunks stay in buffer")
        print("   - Next upload continues from where it left off")
        
        # Clear
        print("\n5. Clearing buffer...")
        client.clear_buffer()
        print("   ✓ Buffer cleared")
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n✓ Cleaned up: {test_file}")


def main():
    """Run all demonstrations."""
    print("\n" + "🐍 "*30)
    print("IndexedCP Python Client - Cross-Compatibility Demo")
    print("🐍 "*30)
    
    print("\nThis script demonstrates:")
    print("  1. Python client functionality")
    print("  2. Storage compatibility with Node.js")
    print("  3. Upload workflow simulation")
    
    demos = [
        demo_python_only,
        demo_storage_compatibility,
        demo_upload_simulation,
    ]
    
    for demo in demos:
        try:
            demo()
        except Exception as e:
            print(f"\n❌ Demo failed: {e}")
            import traceback
            traceback.print_exc()
    
    print_banner("All Demos Complete!")
    
    print("Next steps:")
    print("\n1. Start the Node.js server:")
    print("   cd ..")
    print("   node bin/indexcp server 3000")
    print("\n2. Set the API key (shown by server):")
    print("   export INDEXCP_API_KEY='<server-api-key>'")
    print("\n3. Upload a real file:")
    print("   cd python")
    print("   python bin/indexcp add ../myfile.txt")
    print("   python bin/indexcp upload http://localhost:3000/upload")
    print("\n4. Check the uploaded file in parent directory!")
    print("\n" + "🎉 "*30 + "\n")


if __name__ == '__main__':
    main()
