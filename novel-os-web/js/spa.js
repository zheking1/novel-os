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
    lang: 'en',
    
    // I18n
    i18n: {
      en: {
        itemLevel: { title: 'Item Levels', new: '+ New', edit: 'Edit', delete: 'Delete', save: 'Save', cancel: 'Cancel',
                      name: 'Name', desc: 'Description', order: 'Order', range: 'Range', loading: 'Loading...',
                      saved: 'Saved', deleted: 'Deleted', nameRequired: 'Name required', confirmDelete: 'Confirm delete?' },
        category: { title: 'Category Manager' },
        workspace: { selectWs: 'Select Workspace', selectPrj: 'Select Project' },
      },
      zh: {
        itemLevel: { title: '物品等级管理', new: '+ 新建', edit: '编辑', delete: '删除', save: '保存', cancel: '取消',
                      name: '名称', desc: '描述', order: '排序', range: '范围', loading: '加载中...',
                      saved: '已保存', deleted: '已删除', nameRequired: '请填写名称', confirmDelete: '确认删除？' },
        category: { title: '分类管理' },
        workspace: { selectWs: '选择工作区', selectPrj: '选择项目' },
      }
    },

    t(key) {
      const lang = this.i18n[this.lang] || this.i18n.en;
      const keys = key.split('.');
      let val = lang;
      for (const k of keys) { val = val?.[k]; }
      return val || key;
    },

    menu: [
      {
        label: 'World',
        items: [
          { id: 'item-level', icon: '⭐', title: this.t('itemLevel.title') },
          { id: 'character-level', icon: '📊', title: 'Character Levels' },
          { id: 'skill-level', icon: '⚡', title: 'Skill Levels' },
          { id: 'tech-level', icon: '🔬', title: 'Tech Levels' },
          { id: 'item-catalog', icon: '🎒', title: 'Item Catalog' },
          { id: 'skill-catalog', icon: '📜', title: 'Skill Catalog' },
          { id: 'location-map', icon: '🗺️', title: 'Locations' },
          { id: 'creature-bestiary', icon: '🐉', title: 'Bestiary' },
        ]
      },
      {
        label: 'Management',
        items: [
          { id: 'category-manage', icon: '📂', title: this.t('category.title') },
        ]
      }
    ],

    async init() {
      this.status = 'Loading...';
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
      } catch (e) { this.status = 'Failed: ' + e.message; }
    },

    async loadProjects() {
      if (!this.workspace) return;
      try {
        const r = await window.api('/api/tool', { tool: 'project.list', arguments: { workspace: this.workspace } });
        this.projects = (r.ok && r.result) ? r.result : [];
        if (this.projects.length > 0 && !this.project) { this.project = this.projects[0].slug; }
      } catch (e) { console.error(e); }
    },

    navigate(pageId) { this.currentPage = pageId; },
    
    toggleLang() { this.lang = this.lang === 'en' ? 'zh' : 'en'; }
  }));
  
  // Global toast wrapper
  window.showToast = function(type, title, msg) {
    const el = document.querySelector('[x-data]');
    if (el?.__x) {
      const data = el.__x.getUnobservedData();
      data.toasts.push({type, msg: title + (msg ? ': ' + msg : '')});
      setTimeout(() => data.toasts.shift(), 3000);
    }
  };
  
  window.setStatus = function(text) {
    const el = document.querySelector('[x-data]');
    if (el?.__x) el.__x.getUnobservedData().status = text;
  };
});