const path = require('path');
const os = require('os');
const fs = require('fs');
const websql = require('websql');
const { createLogger } = require('./logger');

const logger = createLogger({ prefix: '[SQLiteDB]' });

/**
 * SQLite-backed IndexedDB-compatible storage using WebSQL
 * This provides real SQLite persistence in ~/.indexedcp with an IndexedDB-like API
 */
class SQLiteDB {
  constructor(dbName, version) {
    this.dbName = dbName;
    this.version = version;
    this.dbDir = path.join(os.homedir(), '.indexedcp');
    this.dbPath = path.join(this.dbDir, `${dbName}.db`);
    this.ensureDbDir();
    
    // Open WebSQL database (backed by SQLite)
    this.db = websql(this.dbPath, String(version), dbName, 5 * 1024 * 1024);
    logger.debug(`SQLite database opened: ${this.dbPath}`);
    
    // Track which stores have been initialized
    this.initializedStores = new Set();
  }

  ensureDbDir() {
    if (!fs.existsSync(this.dbDir)) {
      fs.mkdirSync(this.dbDir, { recursive: true });
    }
  }

  /**
   * Execute SQL in a transaction with promise support
   */
  executeSql(sql, params = []) {
    return new Promise((resolve, reject) => {
      this.db.transaction((tx) => {
        tx.executeSql(sql, params, (tx, results) => {
          resolve(results);
        }, (tx, error) => {
          reject(error);
        });
      });
    });
  }

  /**
   * Sanitize table name for SQL
   */
  sanitizeTableName(name) {
    // Replace hyphens and other special chars with underscores
    return name.replace(/[^a-zA-Z0-9_]/g, '_');
  }

  /**
   * Initialize object store table
   */
  async initializeStore(storeName, options = {}) {
    const safeName = this.sanitizeTableName(storeName);
    
    // Skip if already initialized
    if (this.initializedStores.has(storeName)) {
      return;
    }
    
    const autoIncrement = options.autoIncrement ? 'AUTOINCREMENT' : '';
    const keyPath = options.keyPath || 'id';
    
    // Create table if it doesn't exist
    const createTableSQL = `
      CREATE TABLE IF NOT EXISTS ${safeName} (
        ${keyPath} ${options.autoIncrement ? 'INTEGER PRIMARY KEY' : 'TEXT PRIMARY KEY'} ${autoIncrement},
        data TEXT NOT NULL
      )
    `;
    
    await this.executeSql(createTableSQL);
    this.initializedStores.add(storeName);
    logger.debug(`Object store '${storeName}' initialized as table '${safeName}'`);
  }

  /**
   * Ensure a store exists before accessing it
   */
  async ensureStore(storeName) {
    if (!this.initializedStores.has(storeName)) {
      await this.initializeStore(storeName, { keyPath: 'id', autoIncrement: false });
    }
  }

  /**
   * Add a record to the store
   */
  async add(storeName, record) {
    await this.ensureStore(storeName);
    const safeName = this.sanitizeTableName(storeName);
    const keyPath = 'id'; // Default key path
    const key = record[keyPath];
    const data = JSON.stringify(record);
    
    if (key !== undefined) {
      await this.executeSql(
        `INSERT INTO ${safeName} (${keyPath}, data) VALUES (?, ?)`,
        [key, data]
      );
    } else {
      // Auto-increment case
      await this.executeSql(
        `INSERT INTO ${safeName} (data) VALUES (?)`,
        [data]
      );
    }
    
    return record;
  }

  /**
   * Put (insert or update) a record
   */
  async put(storeName, record) {
    await this.ensureStore(storeName);
    const safeName = this.sanitizeTableName(storeName);
    const keyPath = 'id';
    const key = record[keyPath];
    const data = JSON.stringify(record);
    
    await this.executeSql(
      `INSERT OR REPLACE INTO ${safeName} (${keyPath}, data) VALUES (?, ?)`,
      [key, data]
    );
    
    return record;
  }

  /**
   * Get a record by key
   */
  async get(storeName, key) {
    await this.ensureStore(storeName);
    const safeName = this.sanitizeTableName(storeName);
    const keyPath = 'id';
    const results = await this.executeSql(
      `SELECT data FROM ${safeName} WHERE ${keyPath} = ?`,
      [key]
    );
    
    if (results.rows.length > 0) {
      return JSON.parse(results.rows.item(0).data);
    }
    return undefined;
  }

  /**
   * Delete a record by key
   */
  async delete(storeName, key) {
    await this.ensureStore(storeName);
    const safeName = this.sanitizeTableName(storeName);
    const keyPath = 'id';
    await this.executeSql(
      `DELETE FROM ${safeName} WHERE ${keyPath} = ?`,
      [key]
    );
    return true;
  }

  /**
   * Get all records from a store
   */
  async getAll(storeName) {
    await this.ensureStore(storeName);
    const safeName = this.sanitizeTableName(storeName);
    const results = await this.executeSql(
      `SELECT data FROM ${safeName}`
    );
    
    const records = [];
    for (let i = 0; i < results.rows.length; i++) {
      records.push(JSON.parse(results.rows.item(i).data));
    }
    return records;
  }

  /**
   * Get all records matching an index value
   */
  async getAllFromIndex(storeName, indexName, value) {
    const records = await this.getAll(storeName);
    return records.filter(r => r[indexName] === value);
  }

  /**
   * Create a transaction-like interface for compatibility with IndexedDB API
   */
  transaction(storeNames, mode) {
    const self = this;
    const stores = Array.isArray(storeNames) ? storeNames : [storeNames];
    
    const storeHandlers = {};
    stores.forEach(storeName => {
      storeHandlers[storeName] = {
        add: (record) => self.add(storeName, record),
        put: (record) => self.put(storeName, record),
        get: (key) => self.get(storeName, key),
        delete: (key) => self.delete(storeName, key),
        getAll: () => self.getAll(storeName),
        index: (indexName) => ({
          getAll: (value) => self.getAllFromIndex(storeName, indexName, value)
        })
      };
    });

    return {
      objectStore: (name) => storeHandlers[name],
      done: Promise.resolve()
    };
  }
}

/**
 * Factory function to create SQLiteDB instance
 * Compatible with the openDB API pattern
 */
async function openSQLiteDB(dbName, version, options) {
  const db = new SQLiteDB(dbName, version);
  
  // Run upgrade if provided
  if (options && options.upgrade) {
    const stores = [];
    
    const mockDB = {
      createObjectStore: (name, opts) => {
        // Store the store creation request
        stores.push({ name, opts });
        
        // Return mock with index creation support
        return {
          createIndex: (indexName, keyPath, opts) => {
            // Indexes are handled via filtering in getAllFromIndex
            // For simplicity, we don't create actual SQL indexes here
          }
        };
      },
      objectStoreNames: {
        contains: (name) => {
          // For simplicity, assume stores exist after creation
          return true;
        }
      }
    };
    
    options.upgrade(mockDB);
    
    // Now actually create the stores synchronously
    for (const store of stores) {
      await db.initializeStore(store.name, store.opts);
    }
  }
  
  return db;
}

module.exports = { openSQLiteDB, SQLiteDB };
