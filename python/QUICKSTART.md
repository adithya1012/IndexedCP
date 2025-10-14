# IndexedCP Python Client - Quick Start Guide

## Installation

1. **Install dependencies:**
   ```bash
   cd python
   pip install -r requirements.txt
   ```

2. **Make CLI executable:**
   ```bash
   chmod +x bin/indexcp
   ```

## Quick Test

### 1. Start the Node.js Server (Required)

In the parent directory:
```bash
# Start server and note the API key
node bin/indexcp server 3000
```

The server will display an API key like:
```
Server listening on http://localhost:3000
API Key: abc123def456...
```

### 2. Test Python Client

In a new terminal, from the `python` directory:

```bash
# Set the API key from the server
export INDEXCP_API_KEY="<the-api-key-from-server>"

# Create a test file
echo "Hello from Python IndexedCP!" > test.txt

# Add file to buffer
python bin/indexcp add test.txt

# List buffered files
python bin/indexcp list

# Upload to server
python bin/indexcp upload http://localhost:3000/upload

# Check the uploaded file in the parent directory
cat uploaded_file.txt  # or check the server's output directory
```

## CLI Commands Reference

```bash
# Add files to buffer
python bin/indexcp add <file-path>

# List buffered files
python bin/indexcp list

# Upload buffered files
python bin/indexcp upload <server-url>

# Clear buffer
python bin/indexcp clear

# Show help
python bin/indexcp help
```

## Programmatic Usage Example

```python
from lib.client import IndexCPClient
import os

# Set API key
os.environ['INDEXCP_API_KEY'] = 'your-api-key'

# Create client
client = IndexCPClient()

# Add file
client.add_file('test.txt')

# Upload
results = client.upload_buffered_files('http://localhost:3000/upload')
print(f"Upload results: {results}")
```

## Running Examples

```bash
# Make sure server is running first!
# Then run examples:

python examples/client_only.py
python examples/programmatic_upload.py
python examples/buffer_management.py
```

## Storage Location

Buffered chunks are stored at:
```
~/.indexcp/db/chunks.json
```

You can inspect this file to see buffered chunks:
```bash
cat ~/.indexcp/db/chunks.json
```

## Troubleshooting

### "Authentication failed: Invalid API key"
- Make sure you set `INDEXCP_API_KEY` environment variable
- Check that the API key matches what the server displayed

### "Upload failed: Connection refused"
- Make sure the Node.js server is running
- Check the server URL (default: http://localhost:3000/upload)

### "File not found"
- Use absolute paths or ensure you're in the correct directory
- Check file permissions

### Clear stuck uploads
```bash
python bin/indexcp clear
```

## Testing Resumable Uploads

```bash
# Add a large file
python bin/indexcp add large_file.zip

# Start upload
python bin/indexcp upload http://localhost:3000/upload

# Interrupt with Ctrl+C

# Check buffered chunks (some will be deleted)
python bin/indexcp list

# Resume upload
python bin/indexcp upload http://localhost:3000/upload
```

The client will only upload remaining chunks!
