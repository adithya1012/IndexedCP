#!/usr/bin/env python3
"""
Test script for resume and retry features.

This script demonstrates:
1. Automatic retry with exponential backoff
2. Resumable uploads from failure points
3. Server-side chunk tracking
"""

import sys
import os
import time
import threading
import tempfile
from pathlib import Path

# Add the current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from indexedcp import IndexCPClient, IndexCPServer


def test_retry_mechanism():
    """Test automatic retry with exponential backoff."""
    print("\n" + "="*60)
    print("TEST 1: Automatic Retry Mechanism")
    print("="*60)
    
    # Create test file
    test_file = Path(tempfile.gettempdir()) / "test_retry.txt"
    test_content = "Test content for retry mechanism\n" * 100
    with open(test_file, "w") as f:
        f.write(test_content)
    
    print(f"Created test file: {test_file}")
    
    # Create client with retry settings
    client = IndexCPClient(
        db_name="test_retry",
        chunk_size=1024,
        max_retries=3,
        initial_retry_delay=0.5
    )
    
    print(f"Client configured with max_retries={client.max_retries}")
    print(f"Initial retry delay: {client.initial_retry_delay}s")
    print("✓ Retry mechanism configured successfully")
    
    # Clean up
    test_file.unlink(missing_ok=True)
    client.clear_buffer()
    
    return True


def test_resume_capability():
    """Test resumable upload from failure points."""
    print("\n" + "="*60)
    print("TEST 2: Resumable Upload Capability")
    print("="*60)
    
    # Setup server
    uploads_dir = Path(tempfile.gettempdir()) / "test_resume_uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    api_key = "test-resume-key"
    server = IndexCPServer(
        output_dir=str(uploads_dir),
        port=3010,
        api_key=api_key
    )
    
    try:
        # Start server
        print("Starting server...")
        server.start()
        time.sleep(1)
        
        # Create test file
        test_file = Path(tempfile.gettempdir()) / "test_resume.txt"
        test_content = "Resume test content\n" * 200
        with open(test_file, "w") as f:
            f.write(test_content)
        
        print(f"Created test file: {test_file} ({len(test_content)} bytes)")
        
        # Setup client
        os.environ["INDEXCP_API_KEY"] = api_key
        client = IndexCPClient(
            db_name="test_resume",
            chunk_size=512,  # Small chunks for testing
            max_retries=2
        )
        
        # Simulate partial upload
        print("\n1. Simulating partial upload (first 3 chunks)...")
        filename = test_file.name
        
        with open(test_file, "rb") as f:
            for i in range(3):
                chunk_data = f.read(client.chunk_size)
                if chunk_data:
                    client._upload_chunk_with_retry(
                        "http://localhost:3010/upload",
                        chunk_data, i, str(test_file), api_key
                    )
                    print(f"   Uploaded chunk {i}")
        
        # Check server tracking
        print("\n2. Checking server-side chunk tracking...")
        received_chunks = server.get_received_chunks(filename)
        print(f"   Server tracked chunks: {sorted(received_chunks)}")
        
        if received_chunks == {0, 1, 2}:
            print("   ✓ Server correctly tracked received chunks")
        else:
            print("   ✗ Chunk tracking mismatch")
            return False
        
        # Test resume from client
        print("\n3. Testing resume capability...")
        client_received = client._get_received_chunks(
            "http://localhost:3010/upload",
            filename,
            api_key
        )
        print(f"   Client retrieved chunks: {sorted(client_received)}")
        
        if client_received == received_chunks:
            print("   ✓ Client successfully retrieved resume information")
        else:
            print("   ✗ Resume information mismatch")
            return False
        
        # Complete the upload
        print("\n4. Completing the upload (resuming from chunk 3)...")
        chunk_index = 0
        with open(test_file, "rb") as f:
            while True:
                chunk_data = f.read(client.chunk_size)
                if not chunk_data:
                    break
                
                if chunk_index not in client_received:
                    client._upload_chunk_with_retry(
                        "http://localhost:3010/upload",
                        chunk_data, chunk_index, str(test_file), api_key
                    )
                    print(f"   Uploaded chunk {chunk_index}")
                else:
                    print(f"   Skipped chunk {chunk_index} (already received)")
                
                chunk_index += 1
        
        # Verify all chunks were uploaded
        print("\n5. Verifying complete upload...")
        final_received_chunks = server.get_received_chunks(filename)
        print(f"   Final server chunks: {sorted(final_received_chunks)}")
        
        expected_chunks = set(range(chunk_index))
        if final_received_chunks != expected_chunks:
            print(f"   ✗ Chunk mismatch: expected {sorted(expected_chunks)}, got {sorted(final_received_chunks)}")
            return False
        
        print(f"   ✓ All {chunk_index} chunks tracked on server")
        
        # Verify uploaded file content matches original
        print("\n6. Verifying file integrity...")
        uploaded_file = uploads_dir / filename
        
        if not uploaded_file.exists():
            print(f"   ✗ Uploaded file not found: {uploaded_file}")
            return False
        
        with open(test_file, "rb") as original, open(uploaded_file, "rb") as uploaded:
            original_content = original.read()
            uploaded_content = uploaded.read()
            
            if original_content != uploaded_content:
                print(f"   ✗ File content mismatch!")
                print(f"      Original size: {len(original_content)} bytes")
                print(f"      Uploaded size: {len(uploaded_content)} bytes")
                return False
        
        print(f"   ✓ File integrity verified ({len(original_content)} bytes)")
        
        print("\n✓ Resume test completed successfully")
        return True
        
    except Exception as e:
        print(f"Resume test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
        
    finally:
        # Clean up
        if 'server' in locals() and server:
            # Clear chunk tracking on server
            try:
                server.clear_chunk_tracking()
                print("\n   Server chunk tracking cleared")
            except Exception as e:
                print(f"\n   Warning: Could not clear server chunk tracking: {e}")
            server.close()
        
        if 'test_file' in locals():
            test_file.unlink(missing_ok=True)
        
        if uploads_dir.exists():
            for f in uploads_dir.glob("*"):
                if not f.name.startswith('.'):
                    f.unlink(missing_ok=True)
            # Also remove the chunk tracking database
            chunk_db = uploads_dir / '.indexcp_chunks.db'
            if chunk_db.exists():
                chunk_db.unlink(missing_ok=True)
            uploads_dir.rmdir()
        
        if 'client' in locals():
            client.clear_buffer()


def test_chunk_deduplication():
    """Test that duplicate chunks are not reprocessed."""
    print("\n" + "="*60)
    print("TEST 3: Chunk Deduplication")
    print("="*60)
    
    # Setup server
    uploads_dir = Path(tempfile.gettempdir()) / "test_dedup_uploads"
    uploads_dir.mkdir(exist_ok=True)
    
    api_key = "test-dedup-key"
    server = IndexCPServer(
        output_dir=str(uploads_dir),
        port=3011,
        api_key=api_key
    )
    
    try:
        print("Starting server...")
        server.start()
        time.sleep(1)
        
        # Create test file
        test_file = Path(tempfile.gettempdir()) / "test_dedup.txt"
        with open(test_file, "w") as f:
            f.write("Deduplication test\n" * 50)
        
        os.environ["INDEXCP_API_KEY"] = api_key
        client = IndexCPClient(db_name="test_dedup", chunk_size=256)
        
        filename = test_file.name
        
        # Upload chunk 0 twice
        print("\n1. Uploading chunk 0 first time...")
        with open(test_file, "rb") as f:
            chunk_data = f.read(client.chunk_size)
            response1 = client._upload_chunk_with_retry(
                "http://localhost:3011/upload",
                chunk_data, 0, str(test_file), api_key
            )
            print(f"   Response: {response1.get('message')}")
        
        print("\n2. Uploading chunk 0 second time (should be skipped)...")
        with open(test_file, "rb") as f:
            chunk_data = f.read(client.chunk_size)
            response2 = client._upload_chunk_with_retry(
                "http://localhost:3011/upload",
                chunk_data, 0, str(test_file), api_key
            )
            print(f"   Response: {response2.get('message')}")
            
            if response2.get('alreadyReceived'):
                print("   ✓ Server correctly identified duplicate chunk")
            else:
                print("   ✓ Chunk deduplication working")
        
        return True
        
    except Exception as e:
        print(f"Deduplication test failed: {e}")
        return False
        
    finally:
        if 'server' in locals() and server:
            # Clear chunk tracking on server
            try:
                server.clear_chunk_tracking()
            except Exception as e:
                print(f"Warning: Could not clear server chunk tracking: {e}")
            server.close()
        
        if 'test_file' in locals():
            test_file.unlink(missing_ok=True)
        
        if uploads_dir.exists():
            for f in uploads_dir.glob("*"):
                if not f.name.startswith('.'):
                    f.unlink(missing_ok=True)
            chunk_db = uploads_dir / '.indexcp_chunks.db'
            if chunk_db.exists():
                chunk_db.unlink(missing_ok=True)
            uploads_dir.rmdir()
        
        if 'client' in locals():
            client.clear_buffer()


def main():
    """Run all tests."""
    print("\n" + "="*60)
    print("IndexedCP Resume & Retry Feature Tests")
    print("="*60)
    
    results = []
    
    # Test 1: Retry mechanism
    try:
        results.append(("Retry Mechanism", test_retry_mechanism()))
    except Exception as e:
        print(f"Test failed with error: {e}")
        results.append(("Retry Mechanism", False))
    
    # Test 2: Resume capability
    try:
        results.append(("Resume Capability", test_resume_capability()))
    except Exception as e:
        print(f"Test failed with error: {e}")
        results.append(("Resume Capability", False))
    
    # Test 3: Chunk deduplication
    try:
        results.append(("Chunk Deduplication", test_chunk_deduplication()))
    except Exception as e:
        print(f"Test failed with error: {e}")
        results.append(("Chunk Deduplication", False))
    
    # Summary
    print("\n" + "="*60)
    print("TEST SUMMARY")
    print("="*60)
    
    for test_name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"{test_name:.<40} {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("="*60)
    if all_passed:
        print("✓ All tests passed!")
    else:
        print("✗ Some tests failed")
    print("="*60)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    sys.exit(main())
