/**
 * Novel OS - Lazy Loader
 * Loads page scripts on demand instead of all at startup.
 */
(function() {
  'use strict';
  if (window.LazyLoader) return;

  const LazyLoader = {
    _loaded: new Set(),
    _loading: new Map(),

    /** Map page IDs to their filenames */
    pageMap: {
      // System
      'workspace-manage': 'workspace-manage-page.js',
      'member-manage': 'member-manage-page.js',
      'project-manage': 'project-manage-page.js',
      'model-profiles': 'model-profiles-page.js',
      'model-routes': 'model-routes-page.js',
      'model-rate-limits': 'model-rate-limits-page.js',
      'template-list': 'template-list-page.js',
      'skill-manage': 'skill-manage-page.js',
      'sync-status': 'sync-status-page.js',
      'sync-conflicts': 'sync-conflicts-page.js',
      'audit-logs': 'audit-logs-page.js',
      'offline-status': 'offline-status-page.js',
      'sys-cache': 'sys-cache-page.js',
      'sys-backup': 'sys-backup-page.js',
      'connection': 'connection-page.js',
      'account': 'account-page.js',
      'api-keys': 'api-tokens-page.js',
      'review-council': 'review-council-page.js',
      'users': 'users-page.js',
      'debug': 'debug-page.js',
      'health': 'health-page.js',
      'style-profiles': 'style-profiles-page.js',
      'style-analysis': 'style-analysis-page.js',
      'style-drift': 'style-drift-page.js',
      // Project
      'canon-list': 'canon-list-page.js',
      'entities-list': 'entities-list-page.js',
      'rules-list': 'rules-list-page.js',
      'foreshadowing-list': 'foreshadowing-list-page.js',
      'plot-threads': 'plot-threads-page.js',
      'plot-volumes': 'plot-volumes-page.js',
      'context-preview': 'context-preview-page.js',
      'review-tasks': 'review-tasks-page.js',
      'pipeline': 'pipeline-page.js',
      'chapters': 'chapters-page.js',
      'project-world-rules': 'project-world-rules-page.js',
      'project-characters': 'project-characters-page.js',
      'project-factions': 'project-factions-page.js',
      'project-world-state': 'project-world-state-page.js',
      'arc-characters': 'arc-characters-page.js',
      'pacing-analysis': 'pacing-analysis-page.js',
      // Knowledge
      'kb-pk-list': 'kb-pk-list-page.js',
      'kb-uk-list': 'kb-uk-list-page.js',
      'kb-genres': 'kb-genres-page.js',
      'materials': 'materials-page.js',
      'kb-categories': 'kb-categories-page.js',
      'knowledge-graph': 'knowledge-graph-page.js',
      'knowledge-stats': 'knowledge-stats-page.js',
      'knowledge-review': 'knowledge-review-page.js',
      'knowledge-expiry': 'knowledge-expiry-page.js',
      'expectations': 'expectations-page.js',
      'kb-search': 'kb-search-page.js',
      'kb-auto-search': 'kb-auto-search-page.js',
      'system-evolution': 'system-evolution-page.js',
      'system-notifications': 'system-notifications-page.js',
      'discussion-room': 'discussion-room-page.js',
      'entity-detail': 'entity-detail-page.js',
      'chapter-plans': 'chapter-plans-page.js',
      // Settings
      'genre-manage': 'genre-manager.js',
      'category-manage': 'kb-categories-page.js',
      'binding-matrix': 'binding-matrix-manager.js',
      'level-manage': 'level-manager.js',
    },

    /** Check if a page is already loaded */
    isLoaded(pageId) {
      return this._loaded.has(pageId);
    },

    /** Load a page script on demand */
    async load(pageId) {
      if (this._loaded.has(pageId)) return true;

      // Deduplicate concurrent loads
      if (this._loading.has(pageId)) {
        return this._loading.get(pageId);
      }

      const filename = this.pageMap[pageId];
      if (!filename) {
        console.warn('[LazyLoader] Unknown page:', pageId);
        return false;
      }

      const promise = new Promise((resolve, reject) => {
        const script = document.createElement('script');
        script.src = `js/pages/${filename}?v=${Date.now()}`;
        script.onload = () => {
          this._loaded.add(pageId);
          this._loading.delete(pageId);
          resolve(true);
        };
        script.onerror = () => {
          this._loading.delete(pageId);
          console.error('[LazyLoader] Failed to load:', filename);
          reject(new Error(`Failed to load ${filename}`));
        };
        document.head.appendChild(script);
      });

      this._loading.set(pageId, promise);
      return promise;
    },

    /** Preload commonly used pages in background */
    preloadCommon() {
      const commonPages = ['project-manage', 'canon-list', 'chapters'];
      setTimeout(() => {
        commonPages.forEach(p => this.load(p).catch(() => {}));
      }, 2000);
    }
  };

  window.LazyLoader = LazyLoader;
})();