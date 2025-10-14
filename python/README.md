# IndexedCP Python Client

**IndexedCP Python Client** is a Python implementation of the IndexedCP file transfer system. It provides secure, efficient, and resumable file uploads with filesystem-based buffering.

---

## Features

- ✅ **Chunked file transfer** - Files split into 1MB chunks
- ✅ **Filesystem buffering** - Chunks stored in `~/.indexcp/db/chunks.json`
- ✅ **Resumable uploads** - Resume interrupted uploads
- ✅ **CLI tool** - Command-line interface for easy usage
- ✅ **Programmatic API** - Use as a Python library
- ✅ **API key authentication** - Secure uploads with Bearer tokens
- ✅ **Compatible with Node.js server** - Works with the Node.js IndexedCP server

---

## Installation

### From Source

```bash
cd python
pip install -r requirements.txt
```

### Make CLI executable

```bash
chmod +x bin/indexcp
```

Add to your PATH (optional):

```bash
# Add to ~/.bashrc or ~/.zshrc
export PATH="$PATH:/path/to/IndexedDB_adithya/python/bin"
```

---

## Usage

### CLI Usage

#### 1. Add files to buffer

```bash
python bin/indexcp add ./myfile.txt
python bin/indexcp add ./document.pdf
```

#### 2. List buffered files

```bash
python bin/indexcp list
```

#### 3. Upload buffered files

```bash
# Using environment variable (recommended)
export INDEXCP_API_KEY="your-api-key-here"
python bin/indexcp upload http://localhost:3000/upload

# Or with --api-key flag (not recommended for security)
python bin/indexcp upload http://localhost:3000/upload --api-key your-api-key
```

#### 4. Clear buffer

```bash
python bin/indexcp clear
```

---

### Programmatic Usage

#### Example 1: Basic Usage

```python
from lib.client import IndexCPClient

# Initialize client
client = IndexCPClient()

# Add file to buffer
client.add_file('./myfile.txt')

# Upload buffered files
client.api_key = 'your-api-key'  # Or use INDEXCP_API_KEY env var
upload_results = client.upload_buffered_files('http://localhost:3000/upload')

print(f"Upload complete: {upload_results}")
```

#### Example 2: Buffer and Upload in One Call

```python
from lib.client import IndexCPClient

client = IndexCPClient()
client.api_key = 'your-api-key'

# Buffer and upload immediately
results = client.buffer_and_upload('./document.pdf', 'http://localhost:3000/upload')
```

#### Example 3: Buffer Management

```python
from lib.client import IndexCPClient

client = IndexCPClient()

# Add multiple files
client.add_file('./file1.txt')
client.add_file('./file2.txt')

# List buffered files
buffered = client.list_buffered_files()
print(f"Buffered files: {buffered}")

# Clear buffer
client.clear_buffer()
```

---

## Architecture

### Directory Structure

```
python/
├── bin/
│   └── indexcp              # CLI executable
├── lib/
│   ├── __init__.py          # Package init
│   ├── client.py            # IndexCPClient class
│   └── filesystem_db.py     # Filesystem storage implementation
├── examples/
│   ├── client_only.py       # Basic usage example
│   ├── programmatic_upload.py   # Programmatic API example
│   └── buffer_management.py     # Buffer management example
├── requirements.txt         # Python dependencies
├── setup.py                 # Package setup
└── README.md               # This file
```

### Storage Location

Buffered chunks are stored in:

```
~/.indexcp/db/chunks.json
```

This location is compatible with the Node.js CLI implementation, allowing you to switch between Node.js and Python clients.

---

## How It Works

### 1. File Buffering

When you add a file:

1. File is read in 1MB chunks
2. Each chunk is stored with metadata (filename, chunk index)
3. Binary data is base64-encoded for JSON storage
4. Chunks persist until successfully uploaded

### 2. Upload Process

When you upload:

1. Client retrieves all buffered chunks
2. Groups chunks by filename
3. Sorts chunks by index (ensures correct order)
4. Uploads each chunk with headers:
   - `Content-Type: application/octet-stream`
   - `X-Chunk-Index: <index>`
   - `X-File-Name: <filename>`
   - `Authorization: Bearer <api-key>`
5. Deletes chunks after successful upload

### 3. Resumability

If upload is interrupted:

- Successfully uploaded chunks are deleted from buffer
- Remaining chunks stay in storage
- Next upload attempt continues from where it left off
- Server appends chunks to existing file

---

## Examples

Run the example scripts:

```bash
# Basic client usage
python examples/client_only.py

# Programmatic upload
python examples/programmatic_upload.py

# Buffer management
python examples/buffer_management.py
```

---

## API Reference

### IndexCPClient

#### `__init__()`

Initialize the client.

#### `add_file(file_path: str) -> int`

Add a file to the buffer.

- **Parameters**: `file_path` - Path to file
- **Returns**: Number of chunks created

#### `upload_buffered_files(server_url: str) -> Dict[str, str]`

Upload all buffered files.

- **Parameters**: `server_url` - Upload endpoint URL
- **Returns**: Dictionary mapping client filenames to server filenames

#### `buffer_and_upload(file_path: str, server_url: str) -> Dict[str, str]`

Convenience method to buffer and upload in one call.

#### `list_buffered_files() -> List[str]`

Get list of buffered filenames.

#### `clear_buffer()`

Clear all buffered chunks.

---

## Compatibility

### Node.js Server

This Python client is fully compatible with the Node.js IndexedCP server:

```bash
# Start Node.js server (in parent directory)
node bin/indexcp server 3000

# Use Python client to upload
export INDEXCP_API_KEY="<server-api-key>"
python bin/indexcp add myfile.txt
python bin/indexcp upload http://localhost:3000/upload
```

### Storage Compatibility

The Python client uses the same storage format and location as the Node.js CLI:

- Storage path: `~/.indexcp/db/chunks.json`
- Data format: Base64-encoded chunks in JSON

You can switch between Node.js and Python clients seamlessly!

---

## Requirements

- Python 3.8+
- requests >= 2.28.0

---

## Environment Variables

- `INDEXCP_API_KEY` - API key for server authentication (recommended method)

---

## Security Notes

1. **Never hardcode API keys** in your code
2. Use environment variables: `export INDEXCP_API_KEY="..."`
3. Avoid passing API keys via command-line flags (visible in process list)
4. Server validates API keys via Bearer token authentication

---

## Differences from Node.js Implementation

### What's Included ✅

- Client functionality (file buffering and upload)
- CLI tool with all commands
- Filesystem storage (`~/.indexcp/db/chunks.json`)
- API key authentication
- Compatible with Node.js server

### What's NOT Included ❌

- Server implementation (use Node.js server)
- IndexedDB implementation (uses filesystem only)
- Browser support (Python is server-side only)

---

## License

MIT License - See LICENSE file in parent directory

---

## Contributing

This is a Python port of the Node.js IndexedCP client. For issues and contributions, please refer to the main repository.
