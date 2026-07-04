/**
 * Novel OS SPA - Alpine.js Application Shell
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('app', () => ({
    currentPage: 'item-level',
    workspace: 'default',
    project: '',
    workspaces: [],
    projects: [],
    status: '',
    toasts: [],

    menu: [
      {
        label: 'World',
        items: [
          { id: 'item-level', icon: '⭐', title: 'Item Levels' },
          { id: 'genre-manage', icon: '📖', title: 'Genre Manager' },
          { id: 'category-manage', icon: '📂', title: 'Category Manager' },
          { id: 'binding', icon: '🔗', title: 'Genre Binding' },
        ]
      }
    ],

    async init() {
      this.status = 'Loading workspaces...';
      try {
        const r = await window.api('/api/tool', { tool: 'workspace.list', arguments: {} });
        if (r.ok && r.result) {
          this.workspaces = r.result.filter(w => w.slug);
          if (this.workspaces.length > 0) {
            this.workspace = this.workspaces[0].slug;
            await this.loadProjects();
          }
        }
        this.status = '';
      } catch (e) {
        this.status = 'Failed: ' + e.message;
      }
    },

    async loadProjects() {
      if (!this.workspace) return;
      try {
        const r = await window.api('/api/tool', { tool: 'project.list', arguments: { workspace: this.workspace } });
        this.projects = (r.ok && r.result) ? r.result : [];
        if (this.projects.length > 0 && !this.project) {
          this.project = this.projects[0].slug;
        }
      } catch (e) {
        console.error('loadProjects:', e);
      }
    },

    navigate(pageId) {
      this.currentPage = pageId;
    },

    toast(type, msg) {
      this.toasts.push({ type, msg });
      setTimeout(() => this.toasts.shift(), 3000);
    }
  }));
});