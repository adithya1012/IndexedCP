# Resume & Retry Features

This document describes the new resume and retry features added to IndexedCP Python implementation.

## Features Overview

### 1. Automatic Retry Mechanism with Exponential Backoff

The client now automatically retries failed chunk uploads with exponential backoff, making uploads more resilient to temporary network issues.

**How it works:**
- Failed chunk uploads are automatically retried up to a configurable number of times
- Delay between retries increases exponentially (1s, 2s, 4s, etc.)
- Configurable via `max_retries` and `initial_retry_delay` parameters

**Usage:**
```python
from indexedcp import IndexCPClient

# Create client with custom retry settings
client = IndexCPClient(
    max_retries=5,              # Retry up to 5 times (default: 3)
    initial_retry_delay=2.0     # Start with 2s delay (default: 1.0)
)

# Uploads will automatically retry on failure
client.buffer_and_upload('./myfile.txt', 'http://localhost:3000/upload')
```

### 2. Resumable Upload Capability

Uploads can now be resumed from the point of failure, avoiding re-uploading chunks that were already successfully received.

**How it works:**
- Client checks with server which chunks have already been received
- Only missing chunks are uploaded
- Works across client restarts (chunks are tracked in SQLite buffer)

**Usage:**
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

# Resume upload later - only missing chunks will be uploaded
client.upload_buffered_files('http://localhost:3000/upload')
```

### 3. Server-Side Chunk Tracking

The server now tracks which chunks have been received for each file, enabling resume support.

**How it works:**
- Server maintains a SQLite database (`.indexcp_chunks.db`) tracking received chunks
- Each chunk is recorded with filename and chunk index
- Duplicate chunks are automatically detected and skipped
- Status endpoint allows clients to query received chunks

**Server tracking database location:**
```
<output_dir>/.indexcp_chunks.db
```

## API Changes

### Client API

#### Constructor Parameters

```python
IndexCPClient(
    db_name="indexcp",              # Database name (unchanged)
    chunk_size=1024*1024,           # Chunk size in bytes (unchanged)
    max_retries=3,                  # NEW: Maximum retry attempts
    initial_retry_delay=1.0         # NEW: Initial delay for exponential backoff
)
```

#### New Methods

```python
# Upload chunk with automatic retry
client._upload_chunk_with_retry(server_url, chunk_data, index, file_name, api_key)

# Get received chunks from server (for resume)
received_chunks = client._get_received_chunks(server_url, filename, api_key)
# Returns: Set[int] of received chunk indices
```

### Server API

#### New Endpoint

**GET /upload/status?filename=<filename>**

Returns the list of chunks already received for a file.

**Request:**
```
GET /upload/status?filename=myfile.txt
Authorization: Bearer <api-key>
```

**Response:**
```json
{
    "filename": "myfile.txt",
    "receivedChunks": [0, 1, 2, 5, 7]
}
```

#### New Methods

```python
# Check if chunk already received
is_received = server.is_chunk_received(filename, chunk_index)

# Mark chunk as received
server.mark_chunk_received(filename, chunk_index)

# Get all received chunks for a file
received = server.get_received_chunks(filename)
# Returns: Set[int]
```

## Behavior Changes

### Upload Process

**Before:**
1. Client uploads all chunks sequentially
2. Any failure requires manual restart
3. All chunks re-uploaded on restart

**After:**
1. Client queries server for received chunks
2. Client skips already-received chunks
3. Failed chunks are retried automatically with backoff
4. Server deduplicates chunks automatically

### Example Flow

```
Initial Upload (interrupted after chunk 3):
├── Chunk 0 ✓ uploaded → server tracks
├── Chunk 1 ✓ uploaded → server tracks
├── Chunk 2 ✓ uploaded → server tracks
├── Chunk 3 ✓ uploaded → server tracks
└── Chunk 4 ✗ failed → retry → network error

Resume Upload:
├── Query server → received: [0, 1, 2, 3]
├── Chunk 0 ⊘ skip (already received)
├── Chunk 1 ⊘ skip (already received)
├── Chunk 2 ⊘ skip (already received)
├── Chunk 3 ⊘ skip (already received)
├── Chunk 4 ✓ upload with retry
├── Chunk 5 ✓ upload with retry
└── Complete!
```

## Performance Impact

### Client
- **Initial Request:** One additional GET request per file to check received chunks
- **Resume:** Significantly faster for interrupted uploads (skips completed chunks)
- **Retry:** Minimal overhead for successful uploads, improves reliability for flaky connections

### Server
- **Storage:** ~100 bytes per chunk tracked (SQLite database)
- **Memory:** Negligible (database queries are efficient)
- **Performance:** Near-zero impact on upload speed

### Database Size Estimation

For a 1GB file with 1MB chunks:
- Chunks: 1,024
- Database size: ~100KB
- Database grows linearly with number of chunks

## Configuration Examples

### Aggressive Retry (Poor Network)

```python
client = IndexCPClient(
    max_retries=10,
    initial_retry_delay=0.5,
    chunk_size=512*1024  # Smaller chunks
)
```

### Fast Network (Minimal Retry)

```python
client = IndexCPClient(
    max_retries=2,
    initial_retry_delay=0.1,
    chunk_size=5*1024*1024  # Larger chunks
)
```

### Production Settings

```python
client = IndexCPClient(
    max_retries=5,
    initial_retry_delay=1.0,
    chunk_size=1024*1024
)
```

## Testing

Run the comprehensive test suite:

```bash
cd python
python test_resume_retry.py
```

**Tests included:**
1. Automatic retry mechanism with exponential backoff
2. Resumable upload from failure points
3. Chunk deduplication on server

## Backward Compatibility

✓ **Fully backward compatible**

- Existing code continues to work without changes
- New parameters are optional with sensible defaults
- Server gracefully handles clients without resume support
- Old servers work with new clients (resume feature disabled)

## Migration Guide

### From Old Client

**Before:**
```python
client = IndexCPClient()
client.buffer_and_upload(file, url)
```

**After (with new features):**
```python
client = IndexCPClient(max_retries=5)
client.buffer_and_upload(file, url)
# Now with automatic retry and resume!
```

No code changes required - features work automatically!

## Troubleshooting

### Resume Not Working

**Symptom:** All chunks re-uploaded on resume

**Solutions:**
1. Check server is tracking chunks: `ls <output_dir>/.indexcp_chunks.db`
2. Verify client can reach status endpoint: `GET /upload/status`
3. Check API key is consistent between uploads

### Retry Not Working

**Symptom:** Upload fails immediately without retries

**Solutions:**
1. Verify `max_retries` is set > 0
2. Check error type (authentication errors don't retry)
3. Review logs for retry attempts

### Database Growing Too Large

**Symptom:** `.indexcp_chunks.db` consuming disk space

**Solutions:**
1. Delete database after successful uploads complete
2. Implement periodic cleanup of old entries
3. Use separate output directories per upload session

## Future Enhancements

Potential improvements for future versions:

- [ ] Parallel chunk uploads with resume support
- [ ] Automatic cleanup of completed file tracking
- [ ] Progress callbacks during retry attempts
- [ ] Configurable retry strategies (linear, exponential, custom)
- [ ] Partial chunk resume (resume within a chunk)
- [ ] Cross-client resume coordination
- [ ] Chunk integrity verification (checksums)
- [ ] Rate limiting with automatic backoff

## Security Considerations

- Server chunk tracking database is in the output directory (ensure proper permissions)
- Status endpoint requires authentication (API key)
- No chunk data stored in tracking database (only metadata)
- Tracking database can be safely deleted after uploads complete

## License

Same as IndexedCP - MIT License
