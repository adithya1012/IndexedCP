# IndexedCP Python Client Demo

A simple demonstration of the IndexedCP Python client showing file upload with real-time progress tracking to a Node.js IndexedCP server.

## 📁 Files

- `client_demo.py` - Client with progress bar and statistics
- `client_resumable_demo.py` - Client with resumable upload demonstration
- `sample_file.txt` - Sample file for testing
- `DEMO_README.md` - This file

## 🚀 How to Run the Demo

### Step 1: Start the Node.js Server (Terminal 1)

```bash
# Navigate to the root IndexedCP directory
cd ../..

# Install dependencies
npm install

# Start the server
node examples/server.js
```

**Important:** Note the API key from the server output.

### Step 2: Upload a File (Terminal 2)

```bash
cd python/demo

# Set the API key (use the one from server output)
export INDEXCP_API_KEY=<api-key-from-server>

# Upload sample file with small chunks (creates ~74 chunks for nice progress demo)
python client_demo.py sample_file.txt 10

# Or upload with different chunk sizes:
python client_demo.py sample_file.txt 50     # ~15 chunks
python client_demo.py sample_file.txt 256    # ~3 chunks

# Or upload your own file
python client_demo.py /path/to/your/file.pdf 256
```

**Note:** The second argument is chunk size in KB. Smaller chunks = more progress updates (better for demo).

## 📊 What You'll See

### Server Terminal (Node.js):

```
Server listening on http://localhost:3000
API Key: <generated-api-key>
Include this API key in requests using the Authorization: Bearer <token> header

Chunk 0 received for sample_file.txt -> sample_file.txt
Chunk 1 received for sample_file.txt -> sample_file.txt
...
```

### Client Terminal (Python):

```
============================================================
IndexedCP Demo Client
============================================================

📤 Uploading File
   File: sample_file.txt
   Size: 750,592 bytes (0.72 MB)
   Chunk Size: 10,240 bytes
   Total Chunks: 74

⏳ Upload Progress:
   [████████████████████████████████████████] 100.0% | Chunk 74/74 | 10240 bytes

✅ Upload Complete!
   Total Time: 2.15 seconds
   Average Time per Chunk: 0.029 seconds
   Throughput: 0.33 MB/s
```

## 🎯 Features Demonstrated

✅ **File Chunking** - Files split into configurable chunks  
✅ **Progress Bar** - Real-time visual progress: `[████████░░░░] 75%`  
✅ **Chunk Counter** - Shows current chunk and total  
✅ **Statistics** - Upload time, throughput, averages  
✅ **API Authentication** - Secure transfer with API keys

## 🔧 Troubleshooting

**Port already in use?**

```bash
lsof -i :3000
kill -9 <PID>
```

**API key not set?**

```bash
export INDEXCP_API_KEY=demo-key-2024
```

**Perfect for:** Showing file chunking, progress tracking, and transfer statistics
