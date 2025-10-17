#!/usr/bin/env node
/**
 * Test all storage modes: SQLite, JSON, and fake-indexeddb
 */

const { spawn } = require('child_process');
const path = require('path');
const fs = require('fs');
const os = require('os');

const colors = {
  reset: '\x1b[0m',
  green: '\x1b[32m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  cyan: '\x1b[36m',
  bold: '\x1b[1m',
};

function log(msg, color = 'reset') {
  console.log(`${colors[color]}${msg}${colors.reset}`);
}

function cleanup() {
  const dbDir = path.join(os.homedir(), '.indexcp', 'db');
  if (fs.existsSync(dbDir)) {
    fs.rmSync(dbDir, { recursive: true, force: true });
  }
}

function runTest(script, env = {}) {
  return new Promise((resolve) => {
    const proc = spawn('node', ['-e', script], {
      cwd: path.dirname(__dirname),
      env: { ...process.env, ...env },
      stdio: 'pipe'
    });

    let stdout = '';
    let stderr = '';

    proc.stdout.on('data', (data) => {
      stdout += data.toString();
    });

    proc.stderr.on('data', (data) => {
      stderr += data.toString();
    });

    proc.on('close', (code) => {
      resolve({ code, stdout, stderr });
    });
  });
}

async function testSQLiteMode() {
  log('\n' + '═'.repeat(70), 'cyan');
  log('Testing: Default SQLite Mode', 'bold');
  log('═'.repeat(70), 'cyan');

  cleanup();

  const script = `
    const IndexCPClient = require('./lib/client');
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    
    (async () => {
      const client = new IndexCPClient();
      await client.addFile('/tmp/test-cli.txt');
      
      const dbDir = path.join(os.homedir(), '.indexcp', 'db');
      const files = fs.readdirSync(dbDir);
      const sqliteFiles = files.filter(f => f.endsWith('.sqlite'));
      
      if (sqliteFiles.length < 1) {
        throw new Error('SQLite file not created');
      }
      
      const db = await client.initDB();
      const tx = db.transaction('chunks', 'readonly');
      const store = tx.objectStore('chunks');
      const chunks = await store.getAll();
      if (tx.done) await tx.done;
      
      if (chunks.length !== 1) {
        throw new Error('Expected 1 chunk, got ' + chunks.length);
      }
      
      console.log('✓ SQLite mode works correctly');
    })();
  `;

  const result = await runTest(script);
  if (result.code !== 0) {
    log('✗ SQLite mode test failed', 'red');
    log(result.stderr, 'red');
    return false;
  }
  log(result.stdout.trim(), 'green');
  return true;
}

async function testJSONMode() {
  log('\n' + '═'.repeat(70), 'cyan');
  log('Testing: JSON File Mode (Legacy)', 'bold');
  log('═'.repeat(70), 'cyan');

  cleanup();

  const script = `
    const IndexCPClient = require('./lib/client');
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    
    (async () => {
      const client = new IndexCPClient();
      await client.addFile('/tmp/test-cli.txt');
      
      const jsonPath = path.join(os.homedir(), '.indexcp', 'db', 'chunks.json');
      if (!fs.existsSync(jsonPath)) {
        throw new Error('JSON file not created');
      }
      
      const data = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
      if (data.length !== 1) {
        throw new Error('Expected 1 chunk in JSON, got ' + data.length);
      }
      
      console.log('✓ JSON mode works correctly');
    })();
  `;

  const result = await runTest(script, { INDEXCP_CLI_MODE: 'json' });
  if (result.code !== 0) {
    log('✗ JSON mode test failed', 'red');
    log(result.stderr, 'red');
    return false;
  }
  log(result.stdout.trim(), 'green');
  return true;
}

async function testFakeIndexedDBMode() {
  log('\n' + '═'.repeat(70), 'cyan');
  log('Testing: fake-indexeddb Mode (In-Memory)', 'bold');
  log('═'.repeat(70), 'cyan');

  cleanup();

  const script = `
    const IndexCPClient = require('./lib/client');
    const fs = require('fs');
    const path = require('path');
    const os = require('os');
    
    (async () => {
      const client = new IndexCPClient();
      await client.addFile('/tmp/test-cli.txt');
      
      // Check no files were created
      const dbDir = path.join(os.homedir(), '.indexcp', 'db');
      if (fs.existsSync(dbDir)) {
        const files = fs.readdirSync(dbDir);
        if (files.length > 0) {
          throw new Error('Files created in in-memory mode: ' + files.join(', '));
        }
      }
      
      // Verify data is in memory
      const db = await client.initDB();
      const tx = db.transaction('chunks', 'readonly');
      const store = tx.objectStore('chunks');
      const chunks = await store.getAll();
      if (tx.done) await tx.done;
      
      if (chunks.length !== 1) {
        throw new Error('Expected 1 chunk in memory, got ' + chunks.length);
      }
      
      console.log('✓ fake-indexeddb mode works correctly');
    })();
  `;

  const result = await runTest(script, { INDEXCP_CLI_MODE: 'false' });
  if (result.code !== 0) {
    log('✗ fake-indexeddb mode test failed', 'red');
    log(result.stderr, 'red');
    return false;
  }
  log(result.stdout.trim(), 'green');
  return true;
}

async function main() {
  log('\n' + '═'.repeat(70), 'yellow');
  log('IndexedCP - Storage Modes Test', 'yellow');
  log('═'.repeat(70) + '\n', 'yellow');

  // Create test file
  fs.writeFileSync('/tmp/test-cli.txt', 'Test file content for storage modes');

  const results = [];
  results.push(await testSQLiteMode());
  results.push(await testJSONMode());
  results.push(await testFakeIndexedDBMode());

  // Cleanup
  cleanup();
  if (fs.existsSync('/tmp/test-cli.txt')) {
    fs.unlinkSync('/tmp/test-cli.txt');
  }

  // Summary
  log('\n' + '═'.repeat(70), 'yellow');
  log('Test Summary', 'yellow');
  log('═'.repeat(70), 'yellow');

  const passed = results.filter(r => r).length;
  const failed = results.length - passed;

  log(`Total Tests: ${results.length}`, 'cyan');
  log(`Passed: ${passed}`, passed === results.length ? 'green' : 'yellow');
  log(`Failed: ${failed}`, failed > 0 ? 'red' : 'green');
  log('═'.repeat(70) + '\n', 'yellow');

  if (failed > 0) {
    log('Some tests failed.', 'red');
    process.exit(1);
  } else {
    log('All storage mode tests passed! 🎉', 'green');
    process.exit(0);
  }
}

main().catch((error) => {
  log('Test runner error: ' + error.message, 'red');
  console.error(error);
  process.exit(1);
});
