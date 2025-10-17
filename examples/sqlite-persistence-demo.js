/**
 * Example: Demonstrating SQLite-backed persistent storage with IndexedCP
 * 
 * This example shows how IndexedCP now uses SQLite for durable storage,
 * ensuring data survives process restarts with full ACID compliance.
 */

const IndexCPClient = require('../lib/client');
const path = require('path');
const fs = require('fs');

async function demonstratePersistence() {
  console.log('=== IndexedCP with SQLite Backend ===\n');

  // Create a test file
  const testFile = '/tmp/indexedcp-demo.txt';
  fs.writeFileSync(testFile, 'Demo content for SQLite persistence');

  // Step 1: Add file to buffer
  console.log('Step 1: Adding file to buffer...');
  const client = new IndexCPClient();
  await client.addFile(testFile);
  console.log('✓ File added to buffer\n');

  // Step 2: Verify data is persisted in SQLite
  console.log('Step 2: Verifying SQLite persistence...');
  const dbPath = path.join(require('os').homedir(), '.indexcp', 'db', 'D_indexcp.sqlite');
  if (fs.existsSync(dbPath)) {
    const stats = fs.statSync(dbPath);
    console.log(`✓ SQLite database created: ${dbPath}`);
    console.log(`  Size: ${stats.size} bytes\n`);
  }

  // Step 3: Query the database to verify content
  console.log('Step 3: Querying database...');
  const db = await client.initDB();
  const tx = db.transaction('chunks', 'readonly');
  const store = tx.objectStore('chunks');
  const chunks = await store.getAll();
  if (tx.done) await tx.done;
  
  console.log(`✓ Found ${chunks.length} chunk(s) in database`);
  chunks.forEach((chunk, i) => {
    console.log(`  Chunk ${i}: ${chunk.fileName} (${chunk.data.length} bytes)`);
  });
  console.log();

  // Step 4: Demonstrate persistence across "restarts"
  console.log('Step 4: Data persists across process restarts');
  console.log('  (This data will remain in SQLite until explicitly deleted)\n');

  // Cleanup
  console.log('Cleaning up...');
  await db.delete('chunks', chunks[0].id);
  db.close();
  fs.unlinkSync(testFile);
  console.log('✓ Demo complete\n');

  console.log('=== Storage Modes ===');
  console.log('Default (SQLite): Full ACID persistence');
  console.log('  INDEXCP_CLI_MODE=json    - Legacy JSON file storage');
  console.log('  INDEXCP_CLI_MODE=false   - In-memory (fake-indexeddb for testing)');
}

// Run the demo
demonstratePersistence().catch(console.error);
