/**
 * Novel OS - Cache Manager
 * TTL-based API response cache with deduplication.
 */
(function() {
  'use strict';
  if (window.CacheManager) return;

  const CacheManager = {
    _store: new Map(),
    _pending: new Map(),

    /** Default TTLs in ms for different cache categories */
    TTLS: {
      workspace: 300000,   // 5 min - rarely changes
      genre: 600000,       // 10 min
      category: 300000,    // 5 min
      user: 60000,         // 1 min
      project: 60000,      // 1 min
      default: 30000       // 30s
    },

    /**
     * Get cached value or fetch and cache
     * @param {string} key - Unique cache key
     * @param {Function} fetcher - Async function to fetch data
     * @param {number} ttl - Cache TTL in ms
     */
    async getOrFetch(key, fetcher, ttl) {
      // Check cache
      const cached = this._store.get(key);
      if (cached && Date.now() - cached.time < (ttl || this.TTLS.default)) {
        return cached.data;
      }

      // Deduplicate concurrent requests
      if (this._pending.has(key)) {
        return this._pending.get(key);
      }

      const promise = (async () => {
        try {
          const data = await fetcher();
          this._store.set(key, { data, time: Date.now() });
          return data;
        } finally {
          this._pending.delete(key);
        }
      })();

      this._pending.set(key, promise);
      return promise;
    },

    /** Get cached value only, no fetch */
    get(key) {
      const cached = this._store.get(key);
      if (cached) return cached.data;
      return null;
    },

    /** Set cache directly */
    set(key, data) {
      this._store.set(key, { data, time: Date.now() });
    },

    /** Invalidate a specific key */
    invalidate(key) {
      this._store.delete(key);
      this._pending.delete(key);
    },

    /** Invalidate all keys matching a prefix */
    invalidatePrefix(prefix) {
      for (const key of this._store.keys()) {
        if (key.startsWith(prefix)) this._store.delete(key);
      }
    },

    /** Clear all caches */
    clear() {
      this._store.clear();
      this._pending.clear();
    },

    /** Preload workspace list (called on app init) */
    async preloadWorkspaces() {
      try {
        const result = await window.ApiClient.callTool('workspace.list');
        this.set('workspace.list', result);
        return result;
      } catch (e) {
        console.warn('[Cache] Failed to preload workspaces:', e);
        return [];
      }
    },

    /** Preload genre list */
    async preloadGenres() {
      try {
        const result = await window.ApiClient.callTool('setting.genre.list');
        this.set('genre.list', result);
        return result;
      } catch (e) { return []; }
    }
  };

  window.CacheManager = CacheManager;
})();