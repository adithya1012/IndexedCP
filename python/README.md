# IndexedCP Python Client

Python client implementation for IndexedCP - a secure, efficient, and resumable file transfer system. This client is fully compatible with the Node.js IndexedCP server.

## Features

- **Client-only implementation** - Works with Node.js IndexedCP server
- **Chunked file transfer** with configurable chunk sizes
- **SQLite-based buffering** for reliable, resumable uploads
- **Automatic retry with exponential backoff** for failed uploads
- **Resumable uploads** from failure points (server-side chunk tracking)
- **API key authentication** for secure transfers
- **CLI and library interfaces** for flexibility
- **Cross-platform compatibility** (Windows, macOS, Linux)
- **Full compatibility** with Node.js IndexedCP server

## Installation

### From Source

```bash
git clone https://github.com/mieweb/IndexedCP.git
cd IndexedCP/python
pip install -r requirements.txt
```

### Dependencies

- Python 3.7+
- `requests` library for HTTP operations
- SQLite3 (included with Python)

## Server Setup

This Python package provides the **client only**. You need to run the Node.js IndexedCP server to receive uploads.

### Start the Node.js Server

```bash
# In the root IndexedCP directory
npm install
node examples/server.js
```

The server will display an API key that you'll need for uploads.

## Quick Start

### Client Library Usage

```python
from indexedcp import IndexCPClient

# Create client with retry configuration
client = IndexCPClient(
    max_retries=5,              # Retry failed uploads (default: 3)
    initial_retry_delay=1.0     # Exponential backoff starting delay (default: 1.0)
)

# Add file to buffer
client.add_file('./myfile.txt')

# Upload to server (with automatic retry and resume)
results = client.upload_buffered_files('http://localhost:3000/upload')
print(f"Upload results: {results}")

# Or upload directly without buffering
client.buffer_and_upload('./myfile.txt', 'http://localhost:3000/upload')
```

### Client CLI Usage

```bash
# Set API key (recommended)
export INDEXCP_API_KEY=your-api-key-here

# Add file to buffer
python3 bin/indexcp add ./myfile.txt

# List buffered files
python3 bin/indexcp list

# Upload buffered files
python3 bin/indexcp upload http://localhost:3000/upload

# Direct upload without buffering
python3 bin/indexcp buffer-and-upload ./myfile.txt http://localhost:3000/upload

# Clear buffer
python3 bin/indexcp clear
```

## Resume & Retry Features

### Automatic Retry with Exponential Backoff

Failed chunk uploads are automatically retried with increasing delays between attempts:

```python
from indexedcp import IndexCPClient

# Configure retry behavior
client = IndexCPClient(
    max_retries=5,              # Retry up to 5 times
    initial_retry_delay=1.0     # Start with 1s, then 2s, 4s, 8s, 16s
)

# Uploads will automatically retry on failure
client.buffer_and_upload('./myfile.txt', 'http://localhost:3000/upload')
```

### Resumable Uploads

Uploads can be resumed from the point of failure. The server tracks received chunks, and the client skips already-uploaded chunks:

```python
from indexedcp import IndexCPClient

client = IndexCPClient()

# Add file to buffer
client.add_file('./large_file.zip')

# Start upload (may fail partway through)
try:
    client.upload_buffered_files('http://localhost:3000/upload')
except Exception as e:
    print(f"Upload interrupted: {e}")

# Resume later - only missing chunks will be uploaded
client.upload_buffered_files('http://localhost:3000/upload')
```

### Server-Side Chunk Tracking

The server maintains a SQLite database (`.indexcp_chunks.db`) to track received chunks:

- Duplicate chunks are automatically detected and skipped
- Status endpoint (`/upload/status?filename=<name>`) returns received chunks
- Enables resume capability across client restarts

**Query upload status:**

```bash
curl -H "Authorization: Bearer <api-key>" \
  "http://localhost:3000/upload/status?filename=myfile.txt"
```

**Response:**

```json
{
  "filename": "myfile.txt",
  "receivedChunks": [0, 1, 2, 5, 7]
}
```

## API Reference

### IndexCPClient Class

#### Constructor

```python
IndexCPClient(db_name="indexcp", chunk_size=1024*1024, max_retries=3, initial_retry_delay=1.0)
```

- `db_name`: Name of the SQLite database for storing chunks
- `chunk_size`: Size of each chunk in bytes (default: 1MB)
- `max_retries`: Maximum retry attempts for failed uploads (default: 3)
- `initial_retry_delay`: Initial delay in seconds for exponential backoff (default: 1.0)

#### Methods

##### `add_file(file_path: str) -> int`

Add a file to the buffer by splitting it into chunks.

- **file_path**: Path to the file to add
- **Returns**: Number of chunks created
- **Raises**: `FileNotFoundError` if file doesn't exist

##### `upload_buffered_files(server_url: str) -> Dict[str, str]`

Upload all buffered files to the server.

- **server_url**: URL of the upload endpoint
- **Returns**: Dictionary mapping client filenames to server filenames
- **Raises**: `requests.RequestException` for upload errors

##### `buffer_and_upload(file_path: str, server_url: str)`

Convenience method to buffer and immediately upload a file.

- **file_path**: Path to the file to upload
- **server_url**: URL of the upload endpoint

##### `get_buffered_files() -> List[str]`

Get list of files currently in the buffer.

- **Returns**: List of file paths in the buffer

##### `clear_buffer()`

Clear all chunks from the buffer.

##### `get_api_key() -> str`

Get API key from environment variable or user input.

- **Returns**: API key string
- **Note**: Checks `INDEXCP_API_KEY` environment variable first, then prompts user

## Configuration

### API Key Authentication

The client supports multiple ways to provide API keys:

1. **Environment Variable (Recommended)**:

   ```bash
   export INDEXCP_API_KEY=your-secure-api-key
   ```

2. **Direct Assignment**:

   ```python
   client = IndexCPClient()
   client.api_key = "your-api-key"
   ```

3. **Interactive Prompt**: If no API key is set, the client will prompt you securely.

### Chunk Size

You can customize the chunk size for different use cases:

```python
# Small chunks for slow connections
client = IndexCPClient(chunk_size=64*1024)  # 64KB chunks

# Large chunks for fast connections
client = IndexCPClient(chunk_size=5*1024*1024)  # 5MB chunks
```

### Database Location

The client stores chunks in a SQLite database located at:

- Linux/macOS: `~/.indexcp/indexcp.db`
- Windows: `%USERPROFILE%\.indexcp\indexcp.db`

## Examples

### Basic Client Upload Example

```python
from indexedcp import IndexCPClient

def upload_example():
    client = IndexCPClient()

    # Add multiple files
    client.add_file('./document.pdf')
    client.add_file('./image.jpg')

    # List what's in buffer
    files = client.get_buffered_files()
    print(f"Files to upload: {files}")

    # Upload everything
    results = client.upload_buffered_files('http://localhost:3000/upload')

    for client_file, server_file in results.items():
        print(f"Uploaded: {client_file} -> {server_file}")

if __name__ == "__main__":
    upload_example()
```

### Streaming Upload Example

```python
from indexedcp import IndexCPClient

def streaming_upload(file_path, server_url):
    """Upload file in streaming fashion (chunk by chunk)."""
    client = IndexCPClient(chunk_size=1024*1024)  # 1MB chunks

    with open(file_path, 'rb') as f:
        chunk_index = 0
        while True:
            chunk_data = f.read(client.chunk_size)
            if not chunk_data:
                break

            # Upload chunk immediately
            client.upload_chunk(server_url, chunk_data, chunk_index, file_path)
            print(f"Uploaded chunk {chunk_index}")
            chunk_index += 1

    print("Streaming upload complete!")

# Usage
streaming_upload('./large_file.zip', 'http://localhost:3000/upload')
```

## Testing

````

### Basic Server Example

```python
from indexedcp import IndexCPServer

def server_example():
    # Create server
    server = IndexCPServer(
        output_dir="./uploads",
        port=3000,
        api_key="your-secure-api-key"
    )

    # Start server
    print("Starting IndexedCP server...")
    server.listen()

if __name__ == "__main__":
    server_example()
````

### Complete Client-Server Example

```python
import threading
import time
from indexedcp import IndexCPClient, IndexCPServer

def run_server():
    server = IndexCPServer(output_dir="./uploads", port=3000, api_key="demo-key")
    server.listen()

def run_client():
    time.sleep(1)  # Wait for server
    client = IndexCPClient()
    client.api_key = "demo-key"
    client.buffer_and_upload('./myfile.txt', 'http://localhost:3000/upload')

# Start server in background
server_thread = threading.Thread(target=run_server, daemon=True)
server_thread.start()

# Run client
run_client()
```

### Server with Custom Filename Generator

```python
import os
import time
from indexedcp import IndexCPServer

def timestamp_filename_generator(client_filename, chunk_index, request_handler):
    """Add timestamp to uploaded filenames."""
    base_name = os.path.splitext(os.path.basename(client_filename))[0]
    extension = os.path.splitext(client_filename)[1]
    timestamp = int(time.time())
    return f"{base_name}_{timestamp}{extension}"

server = IndexCPServer(
    output_dir="./timestamped_uploads",
    port=3001,
    filename_generator=timestamp_filename_generator
)

server.listen()
```

### Streaming Upload Example

```python
from indexedcp import IndexCPClient

def streaming_upload(file_path, server_url):
    """Upload file in streaming fashion (chunk by chunk)."""
    client = IndexCPClient(chunk_size=1024*1024)  # 1MB chunks

    with open(file_path, 'rb') as f:
        chunk_index = 0
        while True:
            chunk_data = f.read(client.chunk_size)
            if not chunk_data:
                break

            # Upload chunk immediately
            client.upload_chunk(server_url, chunk_data, chunk_index, file_path)
            print(f"Uploaded chunk {chunk_index}")
            chunk_index += 1

    print("Streaming upload complete!")

# Usage
streaming_upload('./large_file.zip', 'http://localhost:3000/upload')
```

## Testing

Run the client test suite:

```bash
cd python
python3 test_client.py
```

## Compatibility

This Python client is fully compatible with the Node.js IndexedCP server.

**Client Compatibility:**

- Python client ↔ Node.js server ✓

**Protocol Compatibility:**
Both implementations use the same HTTP-based protocol:

- HTTP POST requests to upload endpoint
- `Authorization: Bearer <api-key>` header for authentication
- `X-Chunk-Index` header for chunk sequencing
- `X-File-Name` header for filename information
- `Content-Type: application/octet-stream` for binary data

**Feature Support:**

- ✓ Chunked file transfers
- ✓ API key authentication
- ✓ SQLite buffering (client-side)
- ✓ Resumable uploads (with Node.js server support)
- ✓ Automatic retry with exponential backoff
- ✓ CLI interface
- ✓ Error handling

## Error Handling

The client handles various error conditions:

- **File not found**: Raises `FileNotFoundError`
- **Network errors**: Raises `requests.RequestException`
- **Authentication errors**: Raises `ValueError` with clear message
- **Server errors**: Propagates HTTP status codes and error messages

## Contributing

Contributions are welcome! Please ensure:

1. Code follows Python PEP 8 style guidelines
2. All tests pass (`python3 test_client.py`)
3. New features include appropriate tests
4. Documentation is updated for API changes

## License

MIT License - see the main repository LICENSE file for details.
