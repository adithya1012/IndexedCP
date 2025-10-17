const path = require('path');
const os = require('os');
const fs = require('fs');

// Dynamic import for ES modules - cache the promise
let setupPromise = null;

/**
 * Initialize IndexedDBShim with WebSQL backend (SQLite)
 * This provides a persistent, SQLite-backed IndexedDB implementation for Node.js
 * 
 * @returns {Promise<Function>} Returns the openDB function from idb library
 */
async function setupIndexedDBShim() {
  // Return cached setup if already initialized
  if (setupPromise) {
    return setupPromise;
  }
  
  setupPromise = (async () => {
    // Import indexeddbshim from ES module source
    const { default: setGlobalVars } = await import('indexeddbshim/src/node.js');
    
    // Ensure window object exists for the shim
    if (typeof global.window === 'undefined') {
      global.window = global;
    }
    
    // Set up the database directory
    const dbDir = path.join(os.homedir(), '.indexcp', 'db');
    if (!fs.existsSync(dbDir)) {
      fs.mkdirSync(dbDir, { recursive: true });
    }
    
    // Configure the shim to use SQLite databases in our data directory
    // The src/node.js version automatically sets up websql with sqlite3
    setGlobalVars(global.window, {
      checkOrigin: false,
      databaseBasePath: dbDir  // This tells websql where to store databases
    });
    
    // Return the openDB wrapper from idb library
    const { openDB: idbOpenDB } = require('idb');
    return idbOpenDB;
  })();
  
  return setupPromise;
}

module.exports = { setupIndexedDBShim };
