const path = require('path');
const os = require('os');
const fs = require('fs');
const websql = require('websql');
const { createLogger } = require('./logger');

const logger = createLogger({ prefix: '[SQLiteEncryptedDB]' });

/**
 * Enhanced SQLite-backed encrypted storage
 * 
 * Schema:
 * - sessions: { sessionId, kid, wrappedKey, createdAt }
 * - packets: { id, sessionId, seq, iv, aad, ciphertext, authTag, status }
 * - keyCache: { kid, publicKey, fetchedAt, expiresAt }
 */
class SQLiteEncryptedDB {
  constructor(dbName, version) {
    this.dbName = dbName;
    this.version = version;
    this.dbDir = path.join(os.homedir(), '.indexedcp');
    this.dbPath = path.join(this.dbDir, `${dbName}-encrypted.db`);
    this.ensureDbDir();
    
    // Open WebSQL database (backed by SQLite)
    this.db = websql(this.dbPath, String(version), dbName, 10 * 1024 * 1024);
    logger.debug(`SQLite encrypted database opened: ${this.dbPath}`);
    
    // Initialize tables
    this.initializeTables();
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
   * Initialize all tables for encrypted storage
   */
  async initializeTables() {
    try {
      // Sessions table
      await this.executeSql(`
        CREATE TABLE IF NOT EXISTS sessions (
          sessionId TEXT PRIMARY KEY,
          kid TEXT,
          wrappedKey TEXT,
          createdAt INTEGER,
          data TEXT
        )
      `);

      // Packets table
      await this.executeSql(`
        CREATE TABLE IF NOT EXISTS packets (
          id TEXT PRIMARY KEY,
          sessionId TEXT,
          seq INTEGER,
          iv TEXT,
          aad TEXT,
          ciphertext TEXT,
          authTag TEXT,
          status TEXT,
          data TEXT
        )
      `);
      
      // Create index on sessionId for faster lookups
      await this.executeSql(`
        CREATE INDEX IF NOT EXISTS idx_packets_session ON packets(sessionId)
      `);

      // Key cache table
      await this.executeSql(`
        CREATE TABLE IF NOT EXISTS keyCache (
          kid TEXT PRIMARY KEY,
          publicKey TEXT,
          fetchedAt INTEGER,
          expiresAt INTEGER,
          data TEXT
        )
      `);

      logger.debug('Encrypted database tables initialized');
    } catch (error) {
      logger.error('Failed to initialize tables:', error);
      throw error;
    }
  }

  /**
   * Add a record to a store
   */
  async add(storeName, record) {
    const data = JSON.stringify(record);
    
    if (storeName === 'sessions') {
      await this.executeSql(
        `INSERT INTO sessions (sessionId, kid, wrappedKey, createdAt, data) VALUES (?, ?, ?, ?, ?)`,
        [record.sessionId, record.kid, record.wrappedKey, record.createdAt, data]
      );
    } else if (storeName === 'packets') {
      const id = record.id || `${record.sessionId}-${record.seq}`;
      await this.executeSql(
        `INSERT INTO packets (id, sessionId, seq, iv, aad, ciphertext, authTag, status, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [id, record.sessionId, record.seq, record.iv, record.aad, record.ciphertext, record.authTag, record.status, data]
      );
    } else if (storeName === 'keyCache') {
      await this.executeSql(
        `INSERT INTO keyCache (kid, publicKey, fetchedAt, expiresAt, data) VALUES (?, ?, ?, ?, ?)`,
        [record.kid, record.publicKey, record.fetchedAt, record.expiresAt, data]
      );
    }
    
    return record;
  }

  /**
   * Put (insert or update) a record
   */
  async put(storeName, record) {
    const data = JSON.stringify(record);
    
    if (storeName === 'sessions') {
      await this.executeSql(
        `INSERT OR REPLACE INTO sessions (sessionId, kid, wrappedKey, createdAt, data) VALUES (?, ?, ?, ?, ?)`,
        [record.sessionId, record.kid, record.wrappedKey, record.createdAt, data]
      );
    } else if (storeName === 'packets') {
      const id = record.id || `${record.sessionId}-${record.seq}`;
      await this.executeSql(
        `INSERT OR REPLACE INTO packets (id, sessionId, seq, iv, aad, ciphertext, authTag, status, data) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)`,
        [id, record.sessionId, record.seq, record.iv, record.aad, record.ciphertext, record.authTag, record.status, data]
      );
    } else if (storeName === 'keyCache') {
      await this.executeSql(
        `INSERT OR REPLACE INTO keyCache (kid, publicKey, fetchedAt, expiresAt, data) VALUES (?, ?, ?, ?, ?)`,
        [record.kid, record.publicKey, record.fetchedAt, record.expiresAt, data]
      );
    }
    
    return record;
  }

  /**
   * Get a record by key
   */
  async get(storeName, key) {
    let results;
    
    if (storeName === 'sessions') {
      results = await this.executeSql(
        `SELECT data FROM sessions WHERE sessionId = ?`,
        [key]
      );
    } else if (storeName === 'packets') {
      results = await this.executeSql(
        `SELECT data FROM packets WHERE id = ?`,
        [key]
      );
    } else if (storeName === 'keyCache') {
      results = await this.executeSql(
        `SELECT data FROM keyCache WHERE kid = ?`,
        [key]
      );
    }
    
    if (results && results.rows.length > 0) {
      return JSON.parse(results.rows.item(0).data);
    }
    return undefined;
  }

  /**
   * Delete a record by key
   */
  async delete(storeName, key) {
    if (storeName === 'sessions') {
      await this.executeSql(`DELETE FROM sessions WHERE sessionId = ?`, [key]);
    } else if (storeName === 'packets') {
      await this.executeSql(`DELETE FROM packets WHERE id = ?`, [key]);
    } else if (storeName === 'keyCache') {
      await this.executeSql(`DELETE FROM keyCache WHERE kid = ?`, [key]);
    }
    return true;
  }

  /**
   * Get all records from a store
   */
  async getAll(storeName) {
    const results = await this.executeSql(`SELECT data FROM ${storeName}`);
    
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
    let results;
    
    if (storeName === 'packets' && indexName === 'sessionId') {
      results = await this.executeSql(
        `SELECT data FROM packets WHERE sessionId = ?`,
        [value]
      );
    } else {
      // Fallback to filter-based approach
      const records = await this.getAll(storeName);
      return records.filter(r => r[indexName] === value);
    }
    
    const records = [];
    for (let i = 0; i < results.rows.length; i++) {
      records.push(JSON.parse(results.rows.item(i).data));
    }
    return records;
  }

  /**
   * Create a transaction-like interface for compatibility
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

  /**
   * Cleanup old packets by session ID
   */
  async cleanupSession(sessionId) {
    await this.executeSql(`DELETE FROM packets WHERE sessionId = ?`, [sessionId]);
    await this.executeSql(`DELETE FROM sessions WHERE sessionId = ?`, [sessionId]);
  }

  /**
   * Get pending packets for upload
   */
  async getPendingPackets() {
    const results = await this.executeSql(
      `SELECT data FROM packets WHERE status = ?`,
      ['pending']
    );
    
    const packets = [];
    for (let i = 0; i < results.rows.length; i++) {
      packets.push(JSON.parse(results.rows.item(i).data));
    }
    return packets;
  }

  /**
   * Update packet status
   */
  async updatePacketStatus(packetId, status) {
    // First get the packet to update the full record
    const results = await this.executeSql(
      `SELECT data FROM packets WHERE id = ?`,
      [packetId]
    );
    
    if (results.rows.length > 0) {
      const packet = JSON.parse(results.rows.item(0).data);
      packet.status = status;
      const data = JSON.stringify(packet);
      
      await this.executeSql(
        `UPDATE packets SET status = ?, data = ? WHERE id = ?`,
        [status, data, packetId]
      );
    }
  }
}

/**
 * Factory function to create SQLiteEncryptedDB instance
 */
async function openSQLiteEncryptedDB(dbName, version, options) {
  const db = new SQLiteEncryptedDB(dbName, version);
  
  // Run upgrade if provided (for compatibility)
  if (options && options.upgrade) {
    const mockDB = {
      createObjectStore: (name, opts) => {
        // Return mock with index creation support
        return {
          createIndex: (indexName, keyPath, opts) => {
            // Indexes are handled in SQLite schema
          }
        };
      },
      objectStoreNames: {
        contains: (name) => ['sessions', 'packets', 'keyCache'].includes(name)
      }
    };
    options.upgrade(mockDB);
  }
  
  return db;
}

module.exports = { openSQLiteEncryptedDB, SQLiteEncryptedDB };
