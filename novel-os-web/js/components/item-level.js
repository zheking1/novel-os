/**
 * Novel OS - Item Level Manager (Alpine.js)
 * 物品等级管理 — 凡品→灵品→仙品→神器
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('itemLevelManager', () => ({
    levels: [],
    editing: null,
    form: { name: '', description: '', order: 0, numericRange: '' },
    status: '',

    async init() {
      await this.load();
      this.status = '';
    },

    async load() {
      this.status = 'Loading...';
      try {
        const r = await window.api('/api/tool', {
          tool: 'setting.item.list',
          arguments: { workspace: window.currentWs || 'default', category_id: 'item-level' }
        });
        this.levels = (r.ok && r.result) ? r.result : [];
        this.status = '';
      } catch (e) {
        this.status = 'Load failed: ' + e.message;
      }
    },

    add() {
      this.editing = -1;
      this.form = { name: '', description: '', order: this.levels.length + 1, numericRange: '' };
    },

    edit(idx) {
      const l = this.levels[idx];
      this.editing = idx;
      this.form = {
        name: l.name || '',
        description: l.description || l.data?.description || '',
        order: l.sort_order || idx + 1,
        numericRange: l.data?.numeric_range || ''
      };
    },

    cancel() {
      this.editing = null;
      this.form = { name: '', description: '', order: 0, numericRange: '' };
    },

    async save() {
      if (!this.form.name) { window.showToast('warning', '请输入等级名称'); return; }
      this.status = 'Saving...';
      try {
        const result = await window.api('/api/tool', {
          tool: 'setting.item.upsert',
          arguments: {
            workspace: window.currentWs || 'default',
            category_id: 'item-level',
            core_summary: this.form.name,
            detailed_expansion: this.form.description,
            sort_order: this.form.order,
            data: { numeric_range: this.form.numericRange },
            is_global: true
          }
        });
        if (result.ok) {
          window.showToast('success', 'Saved');
          this.cancel();
          await this.load();
        }
      } catch (e) {
        this.status = 'Save failed: ' + e.message;
      }
    },

    async remove(idx) {
      const l = this.levels[idx];
      if (!confirm('Delete ' + (l.name || l.core_summary) + '?')) return;
      this.status = 'Deleting...';
      try {
        await window.api('/api/tool', {
          tool: 'setting.item.delete',
          arguments: { workspace: window.currentWs || 'default', item_id: l.id }
        });
        window.showToast('success', 'Deleted');
        await this.load();
      } catch (e) {
        this.status = 'Delete failed: ' + e.message;
      }
    }
  }));
});