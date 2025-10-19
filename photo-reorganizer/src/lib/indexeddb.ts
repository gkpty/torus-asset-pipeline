import { RenameInstruction } from '@/types';

const DB_NAME = 'PhotoReorganizerDB';
const DB_VERSION = 1;
const STORE_NAME = 'renameInstructions';

export class IndexedDBManager {
  private db: IDBDatabase | null = null;

  async init(): Promise<void> {
    return new Promise((resolve, reject) => {
      const request = indexedDB.open(DB_NAME, DB_VERSION);

      request.onerror = () => reject(request.error);
      request.onsuccess = () => {
        this.db = request.result;
        resolve();
      };

      request.onupgradeneeded = (event) => {
        const db = (event.target as IDBOpenDBRequest).result;
        if (!db.objectStoreNames.contains(STORE_NAME)) {
          db.createObjectStore(STORE_NAME, { keyPath: 'id' });
        }
      };
    });
  }

  async saveRenameInstructions(instructions: RenameInstruction): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.put({ id: 'instructions', data: instructions });

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }

  async getRenameInstructions(): Promise<RenameInstruction> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readonly');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.get('instructions');

      request.onsuccess = () => {
        const result = request.result;
        resolve(result ? result.data : {});
      };
      request.onerror = () => reject(request.error);
    });
  }

  async clearRenameInstructions(): Promise<void> {
    if (!this.db) await this.init();

    return new Promise((resolve, reject) => {
      const transaction = this.db!.transaction([STORE_NAME], 'readwrite');
      const store = transaction.objectStore(STORE_NAME);
      const request = store.delete('instructions');

      request.onsuccess = () => resolve();
      request.onerror = () => reject(request.error);
    });
  }
}

export const dbManager = new IndexedDBManager();
