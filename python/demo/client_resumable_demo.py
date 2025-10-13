#!/usr/bin/env python3
"""
IndexedCP Resumable Upload Demo
Demonstrates automatic retry and resume capabilities
"""

import sys
import os
from pathlib import Path
import time
import signal

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from indexedcp import IndexCPClient


class ResumableProgressClient(IndexCPClient):
    """Enhanced client with resume and progress tracking."""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.interrupted = False
    
    def upload_chunk_with_progress(self, server_url: str, chunk_data: bytes, 
                                   index: int, file_name: str, total_chunks: int,
                                   api_key=None):
        """Upload a single chunk with progress display."""
        start_time = time.time()
        
        # Show progress
        progress = ((index + 1) / total_chunks) * 100
        bar_length = 40
        filled = int(bar_length * (index + 1) / total_chunks)
        bar = '█' * filled + '░' * (bar_length - filled)
        
        print(f"\r   [{bar}] {progress:.1f}% | Chunk {index + 1}/{total_chunks} | {len(chunk_data)} bytes", 
              end='', flush=True)
        
        # Upload the chunk with retry
        result = self._upload_chunk_with_retry(server_url, chunk_data, index, file_name, api_key)
        
        elapsed = time.time() - start_time
        
        return result, elapsed
    
    def upload_file_with_resume(self, file_path: str, server_url: str):
        """Upload a file with resume capability."""
        api_key = self.get_api_key()
        
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"❌ File not found: {file_path}")
        
        # Calculate total chunks
        file_size = file_path.stat().st_size
        total_chunks = (file_size + self.chunk_size - 1) // self.chunk_size
        
        print(f"\n📤 Uploading File (Resumable Mode)")
        print(f"   File: {file_path.name}")
        print(f"   Size: {file_size:,} bytes ({file_size / (1024*1024):.2f} MB)")
        print(f"   Chunk Size: {self.chunk_size:,} bytes")
        print(f"   Total Chunks: {total_chunks}")
        
        # Check for already uploaded chunks (RESUME FEATURE)
        server_filename = file_path.name
        received_chunks = self._get_received_chunks(server_url, server_filename, api_key)
        
        if received_chunks:
            print(f"\n🔄 RESUME DETECTED!")
            print(f"   Already uploaded: {len(received_chunks)} chunks")
            print(f"   Remaining: {total_chunks - len(received_chunks)} chunks")
            print(f"   Progress: {len(received_chunks) / total_chunks * 100:.1f}%")
        
        print(f"\n⏳ Upload Progress:")
        
        chunk_index = 0
        total_time = 0
        uploaded_count = 0
        skipped_count = 0
        
        with open(file_path, "rb") as f:
            while True:
                chunk_data = f.read(self.chunk_size)
                if not chunk_data:
                    break
                
                # Skip already uploaded chunks (RESUME FEATURE)
                if chunk_index in received_chunks:
                    skipped_count += 1
                    # Update progress bar for skipped chunks too
                    progress = ((chunk_index + 1) / total_chunks) * 100
                    bar_length = 40
                    filled = int(bar_length * (chunk_index + 1) / total_chunks)
                    bar = '█' * filled + '░' * (bar_length - filled)
                    print(f"\r   [{bar}] {progress:.1f}% | Chunk {chunk_index + 1}/{total_chunks} (skipped)", 
                          end='', flush=True)
                else:
                    result, elapsed = self.upload_chunk_with_progress(
                        server_url, chunk_data, chunk_index, 
                        str(file_path), total_chunks, api_key
                    )
                    total_time += elapsed
                    uploaded_count += 1
                
                chunk_index += 1
        
        print("\n")  # New line after progress bar
        
        # Calculate statistics
        if uploaded_count > 0:
            avg_time = total_time / uploaded_count
            throughput = (uploaded_count * self.chunk_size) / total_time if total_time > 0 else 0
            
            print(f"\n✅ Upload Complete!")
            print(f"   New chunks uploaded: {uploaded_count}")
            if skipped_count > 0:
                print(f"   Chunks skipped (already uploaded): {skipped_count}")
            print(f"   Total Time: {total_time:.2f} seconds")
            print(f"   Average Time per Chunk: {avg_time:.3f} seconds")
            print(f"   Throughput: {throughput / (1024*1024):.2f} MB/s")
        else:
            print(f"\n✅ File Already Uploaded!")
            print(f"   All {skipped_count} chunks were already on server")


def main():
    """Main function for the resumable demo."""
    print("=" * 60)
    print("IndexedCP Resumable Upload Demo")
    print("=" * 60)
    
    # Check arguments
    if len(sys.argv) < 2:
        print("\n❌ Usage: python client_resumable_demo.py <file_path> [chunk_size_kb]")
        print("\nExamples:")
        print("   python client_resumable_demo.py sample.txt")
        print("   python client_resumable_demo.py large_file.zip 256")
        print("\nFeatures:")
        print("   ✓ Automatic retry with exponential backoff")
        print("   ✓ Resume from interruption (press Ctrl+C to test)")
        print("   ✓ Server-side chunk tracking")
        print("\nNote: Make sure INDEXCP_API_KEY is set or you'll be prompted")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    # Optional chunk size argument (in KB)
    chunk_size = 256 * 1024  # Default: 256KB
    if len(sys.argv) > 2:
        try:
            chunk_size = int(sys.argv[2]) * 1024
            print(f"\n📦 Using custom chunk size: {chunk_size // 1024} KB")
        except ValueError:
            print(f"\n⚠️  Invalid chunk size, using default: {chunk_size // 1024} KB")
    
    # Check if file exists
    if not Path(file_path).exists():
        print(f"\n❌ Error: File '{file_path}' not found!")
        sys.exit(1)
    
    # Server URL
    server_url = "http://localhost:3000/upload"
    
    print(f"\n🎯 Target Server: {server_url}")
    print(f"📦 Chunk Size: {chunk_size // 1024} KB")
    print(f"🔄 Max Retries: 3 (with exponential backoff)")
    
    # Check for API key
    if not os.environ.get("INDEXCP_API_KEY"):
        print("\n⚠️  INDEXCP_API_KEY not found in environment variables")
        print("   You'll be prompted to enter it manually")
    
    print("\n💡 TIP: Press Ctrl+C during upload to simulate interruption")
    print("        Then run the same command again to see resume in action!")
    print("=" * 60)
    
    try:
        # Create client with retry configuration
        client = ResumableProgressClient(
            chunk_size=chunk_size,
            max_retries=3,
            initial_retry_delay=1.0
        )
        
        # Upload file with resume capability
        client.upload_file_with_resume(file_path, server_url)
        
        print("\n" + "=" * 60)
        print("✨ Demo Complete!")
        print("   Check the './uploads' directory on the server")
        print("=" * 60)
        
    except KeyboardInterrupt:
        print("\n\n⚠️  Upload interrupted by user!")
        print("\n💡 To resume: Run the same command again")
        print("   Only missing chunks will be uploaded!")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
