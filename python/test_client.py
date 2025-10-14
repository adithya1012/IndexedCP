#!/usr/bin/env python3
"""
Test script to verify IndexedCP Python client installation and functionality.
"""

import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.client import IndexCPClient
from lib.filesystem_db import FileSystemDB


def test_filesystem_db():
    """Test filesystem database functionality."""
    print("="*60)
    print("TEST 1: FileSystemDB")
    print("="*60)
    
    db = FileSystemDB('test_indexcp', 1)
    
    # Test add
    print("\n✓ Testing add...")
    record = {'id': 'test-1', 'fileName': 'test.txt', 'data': b'Hello World'}
    db.add('chunks', record)
    print(f"  Added record: {record['id']}")
    
    # Test get
    print("\n✓ Testing get...")
    retrieved = db.get('chunks', 'test-1')
    assert retrieved is not None, "Failed to retrieve record"
    assert retrieved['data'] == b'Hello World', "Data mismatch"
    print(f"  Retrieved record: {retrieved['id']}")
    
    # Test get_all
    print("\n✓ Testing get_all...")
    all_records = db.get_all('chunks')
    assert len(all_records) >= 1, "No records found"
    print(f"  Found {len(all_records)} record(s)")
    
    # Test count
    print("\n✓ Testing count...")
    count = db.count('chunks')
    print(f"  Total records: {count}")
    
    # Test delete
    print("\n✓ Testing delete...")
    db.delete('chunks', 'test-1')
    retrieved = db.get('chunks', 'test-1')
    assert retrieved is None, "Record should be deleted"
    print(f"  Deleted record: test-1")
    
    # Clean up
    db.clear('chunks')
    print("\n✓ Database cleared")
    
    print("\n✅ FileSystemDB tests passed!")
    return True


def test_client():
    """Test IndexCPClient functionality."""
    print("\n" + "="*60)
    print("TEST 2: IndexCPClient")
    print("="*60)
    
    # Create test file
    test_file = 'test_client_file.txt'
    with open(test_file, 'w') as f:
        f.write('Test data for IndexCPClient\n' * 100)
    print(f"\n✓ Created test file: {test_file}")
    
    try:
        # Initialize client
        print("\n✓ Testing client initialization...")
        client = IndexCPClient()
        print(f"  Client initialized")
        print(f"  DB name: {client.db_name}")
        print(f"  Store name: {client.store_name}")
        print(f"  Chunk size: {client.chunk_size} bytes")
        
        # Test add_file
        print("\n✓ Testing add_file...")
        chunks_created = client.add_file(test_file)
        print(f"  Created {chunks_created} chunk(s)")
        
        # Test list_buffered_files
        print("\n✓ Testing list_buffered_files...")
        buffered = client.list_buffered_files()
        assert len(buffered) == 1, f"Expected 1 buffered file, got {len(buffered)}"
        print(f"  Buffered files: {buffered}")
        
        # Check storage
        print("\n✓ Testing storage...")
        db = client._init_db()
        print(f"  Storage path: {db.store_path}")
        print(f"  Storage exists: {db.store_path.exists()}")
        chunk_count = db.count()
        print(f"  Total chunks in storage: {chunk_count}")
        
        # Test clear_buffer
        print("\n✓ Testing clear_buffer...")
        client.clear_buffer()
        buffered = client.list_buffered_files()
        assert len(buffered) == 0, "Buffer should be empty"
        print(f"  Buffer cleared successfully")
        
        print("\n✅ IndexCPClient tests passed!")
        return True
        
    finally:
        # Clean up
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n✓ Cleaned up test file: {test_file}")


def test_chunk_size():
    """Test that chunks are properly sized."""
    print("\n" + "="*60)
    print("TEST 3: Chunk Size")
    print("="*60)
    
    # Create a file larger than chunk size
    test_file = 'test_large_file.txt'
    chunk_size = 1024 * 1024  # 1MB
    file_size = chunk_size * 2 + 500000  # 2.5MB
    
    print(f"\n✓ Creating {file_size / (1024*1024):.2f}MB test file...")
    with open(test_file, 'wb') as f:
        f.write(b'X' * file_size)
    
    try:
        client = IndexCPClient()
        
        print(f"\n✓ Adding file to buffer...")
        chunks_created = client.add_file(test_file)
        print(f"  Created {chunks_created} chunk(s)")
        
        expected_chunks = (file_size + chunk_size - 1) // chunk_size
        assert chunks_created == expected_chunks, \
            f"Expected {expected_chunks} chunks, got {chunks_created}"
        print(f"  ✓ Chunk count is correct (expected {expected_chunks})")
        
        # Verify chunk sizes
        db = client._init_db()
        all_chunks = db.get_all('chunks')
        
        print(f"\n✓ Verifying chunk sizes...")
        for i, chunk in enumerate(all_chunks):
            chunk_data_size = len(chunk['data'])
            if i < chunks_created - 1:
                # All chunks except last should be exactly chunk_size
                assert chunk_data_size == chunk_size, \
                    f"Chunk {i} size mismatch: {chunk_data_size} != {chunk_size}"
            else:
                # Last chunk can be smaller
                assert chunk_data_size <= chunk_size, \
                    f"Last chunk too large: {chunk_data_size} > {chunk_size}"
            print(f"  Chunk {i}: {chunk_data_size / 1024:.2f}KB ✓")
        
        # Clean up
        client.clear_buffer()
        
        print("\n✅ Chunk size tests passed!")
        return True
        
    finally:
        if os.path.exists(test_file):
            os.remove(test_file)
            print(f"\n✓ Cleaned up test file: {test_file}")


def main():
    """Run all tests."""
    print("\n" + "🧪 "*20)
    print("IndexedCP Python Client - Test Suite")
    print("🧪 "*20)
    
    tests_passed = 0
    tests_failed = 0
    
    tests = [
        ("FileSystemDB", test_filesystem_db),
        ("IndexCPClient", test_client),
        ("Chunk Size", test_chunk_size),
    ]
    
    for test_name, test_func in tests:
        try:
            if test_func():
                tests_passed += 1
        except Exception as e:
            tests_failed += 1
            print(f"\n❌ {test_name} test failed: {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    print(f"✅ Passed: {tests_passed}/{len(tests)}")
    print(f"❌ Failed: {tests_failed}/{len(tests)}")
    
    if tests_failed == 0:
        print("\n🎉 All tests passed! IndexedCP Python client is working correctly.")
        print("\nNext steps:")
        print("  1. Start the Node.js server: node ../bin/indexcp server 3000")
        print("  2. Set API key: export INDEXCP_API_KEY='<server-api-key>'")
        print("  3. Try uploading: python bin/indexcp add test.txt && python bin/indexcp upload http://localhost:3000/upload")
        return 0
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
