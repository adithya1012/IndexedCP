# IndexedCP Demo Guide - Resumable Upload Feature

This guide provides step-by-step instructions for demonstrating the IndexedCP resumable upload feature.

---

## 🎬 Demo Structure

### Part 1: Normal Upload Demo (Existing Feature)

### Part 2: Resumable Upload Demo (New Feature)

---

## 📋 Prerequisites

```bash
cd /path/to/IndexedCP/python/demo
```

Ensure you have:

- Python 3.7+
- IndexedCP installed (`pip install -r ../requirements.txt`)
- Two terminal windows ready

---

## 🎥 PART 1: Normal Upload Demo (Keep Existing)

### Terminal 1: Start Server

```bash
# Navigate to demo folder
cd python/demo

# Start the demo server
python3 server_demo.py
```

**Expected Output:**

```
============================================================
IndexedCP Demo Server
============================================================

📋 Server Configuration:
   Port: 3000
   API Key: demo-key-2024
   Output Directory: ./uploads

✅ Server is running and ready to receive files!
```

### Terminal 2: Upload File

```bash
# Set API key
export INDEXCP_API_KEY=demo-key-2024

# Upload sample file with small chunks (better progress visualization)
python3 client_demo.py sample_file.txt 10
```

**Expected Output:**

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
   [████████████████████████████████████████] 100.0% | Chunk 74/74

✅ Upload Complete!
   Total Time: 2.15 seconds
   Average Time per Chunk: 0.029 seconds
   Throughput: 0.33 MB/s
```

**What This Shows:**

- ✅ File chunking
- ✅ Progress bar
- ✅ Upload statistics
- ✅ API authentication

---

## 🎥 PART 2: Resumable Upload Demo (NEW FEATURE)

### Step 1: Start Fresh Server (Terminal 1)

```bash
# Stop previous server (Ctrl+C)
# Clear uploads folder
rm -rf uploads/*
rm -rf uploads/.indexcp_chunks.db

# Restart server
python3 server_demo.py
```

### Step 2: Create a Test File (Optional)

```bash
# Create a larger file for better demo (Terminal 2)
dd if=/dev/urandom of=test_large_file.bin bs=1M count=10
# This creates a 10MB file
```

Or use the existing sample file:

```bash
# Use existing sample file
cp sample_file.txt test_resumable.txt
```

### Step 3: Start Upload and Interrupt

```bash
# Set API key
export INDEXCP_API_KEY=demo-key-2024

# Start upload with medium chunks
python3 client_resumable_demo.py test_resumable.txt 50
```

**During Upload:**

- Wait until progress shows ~40-50%
- **Press Ctrl+C to interrupt**

**Expected Output (Interrupted):**

```
============================================================
IndexedCP Resumable Upload Demo
============================================================

📤 Uploading File (Resumable Mode)
   File: test_resumable.txt
   Size: 750,592 bytes (0.72 MB)
   Chunk Size: 51,200 bytes
   Total Chunks: 15

⏳ Upload Progress:
   [████████████████████░░░░░░░░░░░░░░░░░░░░] 50.0% | Chunk 8/15

⚠️  Upload interrupted by user!

💡 To resume: Run the same command again
   Only missing chunks will be uploaded!
```

### Step 4: Resume the Upload

```bash
# Run THE SAME COMMAND again
python3 client_resumable_demo.py test_resumable.txt 50
```

**Expected Output (Resumed):**

```
============================================================
IndexedCP Resumable Upload Demo
============================================================

📤 Uploading File (Resumable Mode)
   File: test_resumable.txt
   Size: 750,592 bytes (0.72 MB)
   Chunk Size: 51,200 bytes
   Total Chunks: 15

🔄 RESUME DETECTED!
   Already uploaded: 8 chunks
   Remaining: 7 chunks
   Progress: 53.3%

⏳ Upload Progress:
   [████████████████████░░░░░░░░░░░░░░░░░░░░] 53.3% | Chunk 1/15 (skipped)
   [████████████████████░░░░░░░░░░░░░░░░░░░░] 53.3% | Chunk 2/15 (skipped)
   ...
   [████████████████████████████░░░░░░░░░░░░] 66.7% | Chunk 9/15
   [████████████████████████████████████████] 100.0% | Chunk 15/15

✅ Upload Complete!
   New chunks uploaded: 7
   Chunks skipped (already uploaded): 8
   Total Time: 0.85 seconds
```

**What This Shows:**

- ✅ Upload interruption handling
- ✅ Automatic resume detection
- ✅ Server-side chunk tracking
- ✅ Skipping already uploaded chunks
- ✅ Only missing chunks uploaded

---

## 🎥 PART 3: Demonstrating Automatic Retry

### Step 1: Simulate Network Issues

While upload is running, you can demonstrate retry by:

**Option A: Briefly disconnect network**

- Turn off WiFi for 2-3 seconds during upload
- Turn it back on
- Watch automatic retry messages

**Option B: Use the logs**

The client will show retry attempts if there are transient failures:

```
Retry 1/3 after 1.0s...
Retry 2/3 after 2.0s...
```

### Step 2: Show Exponential Backoff

Point out in the output:

- First retry: 1 second delay
- Second retry: 2 seconds delay
- Third retry: 4 seconds delay
- Fourth retry: 8 seconds delay

---

## 📊 Key Points to Highlight

### 1. Resume Capability

- **Interrupt upload** → Only missing chunks re-uploaded
- **Saves bandwidth** → No duplicate uploads
- **Server tracks** → Using SQLite database

### 2. Automatic Retry

- **Exponential backoff** → 1s, 2s, 4s, 8s delays
- **Configurable** → max_retries parameter
- **Smart** → Only retries transient failures

### 3. Server-Side Tracking

- **Database location**: `./uploads/.indexcp_chunks.db`
- **Tracks**: filename + chunk_index
- **Status endpoint**: `GET /upload/status?filename=...`

---

## 🔍 Verification Steps

### Check Server Tracking Database

```bash
# View chunk tracking database
sqlite3 uploads/.indexcp_chunks.db "SELECT * FROM received_chunks;"
```

### Query Upload Status via API

```bash
# Check which chunks are uploaded
curl -H "Authorization: Bearer demo-key-2024" \
  "http://localhost:3000/upload/status?filename=test_resumable.txt"
```

**Expected Response:**

```json
{
  "filename": "test_resumable.txt",
  "receivedChunks": [0, 1, 2, 3, 4, 5, 6, 7]
}
```

### Verify File Integrity

```bash
# Compare original and uploaded file
diff test_resumable.txt uploads/test_resumable.txt
# No output = files are identical
```

---

## 🎬 Demo Script Summary

### 1. Normal Upload (30 seconds)

- Start server
- Upload file with progress
- Show completion stats

### 2. Resumable Upload (2 minutes)

- Start upload
- Interrupt at 50% (Ctrl+C)
- Resume upload
- Show skip messages
- Complete upload

### 3. Verification (30 seconds)

- Show server tracking database
- Query status API
- Verify file integrity

---

## 💡 Talking Points

1. **"Watch the progress bar"** - Visual feedback during upload
2. **"I'll interrupt this now"** - Press Ctrl+C at 50%
3. **"Notice the resume detection"** - Shows already uploaded chunks
4. **"See how it skips chunks"** - Already uploaded = skipped
5. **"Only 7 chunks needed"** - Saved bandwidth (8 chunks skipped)
6. **"Server tracks everything"** - Show SQLite database
7. **"File is complete"** - Verify integrity with diff

---

## 🧹 Cleanup After Demo

```bash
# Remove test files
rm -f test_resumable.txt test_large_file.bin

# Clear uploads folder
rm -rf uploads/*
rm -rf uploads/.indexcp_chunks.db

# Stop server (Ctrl+C)
```

---

## 🚀 Quick Demo Commands (Copy-Paste Ready)

```bash
# Terminal 1: Server
cd python/demo
python3 server_demo.py

# Terminal 2: Resumable Upload
export INDEXCP_API_KEY=demo-key-2024
python3 client_resumable_demo.py sample_file.txt 50
# Press Ctrl+C at 50%
python3 client_resumable_demo.py sample_file.txt 50  # Resume

# Verify
sqlite3 uploads/.indexcp_chunks.db "SELECT * FROM received_chunks;"
curl -H "Authorization: Bearer demo-key-2024" "http://localhost:3000/upload/status?filename=sample_file.txt"
```

---

## ⏱️ Total Demo Time

- **Part 1 (Normal Upload)**: ~1 minute
- **Part 2 (Resumable Upload)**: ~2 minutes
- **Part 3 (Verification)**: ~30 seconds
- **Total**: ~3.5 minutes

Perfect length for a feature demonstration!
