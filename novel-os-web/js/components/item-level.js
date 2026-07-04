/**
 * Novel OS - Item Level Manager (Alpine.js + i18n)
 */
document.addEventListener('alpine:init', () => {
  Alpine.data('itemLevelManager', () => ({
    levels: [],
    editing: null,
    form: { name: '', desc: '', order: 0, range: '' },
    status: '',

    t(key) { return (window.t && window.t(key)) || key; },

    async init() {
      await this.load();
    },

    async load() {
      this.status = this.t('status.loading');
      try {
        const ws = (document.getElementById('workspaceSelect')?.value) || 'default';
        // Resolve category slug to UUID
        const cat = await window.api('/api/tool', {
          tool: 'setting.category.get',
          arguments: { workspace: ws, slug: 'item-level' }
        });
        const catId = (cat && (cat.id || cat.result?.id)) || null;
        if (!catId) { this.status = 'Category not found'; return; }
        const r = await window.api('/api/tool', {
          tool: 'setting.item.list',
          arguments: { workspace: ws, category_id: catId }
        });
        this.levels = (r.ok && r.result) ? r.result : [];
        this.status = '';
      } catch (e) {
        this.status = 'Error: ' + e.message;
      }
    },

    add() {
      this.editing = -1;
      this.form = { name: '', desc: '', order: this.levels.length + 1, range: '' };
    },

    edit(idx) {
      const l = this.levels[idx];
      this.editing = idx;
      this.form = {
        name: l.core_summary || l.name || '',
        desc: l.detailed_expansion || l.data?.description || '',
        order: l.sort_order || idx + 1,
        range: l.data?.numeric_range || ''
      };
    },

    cancel() { this.editing = null; },

    async save() {
      if (!this.form.name) { window.showToast('warning', 'Name required'); return; }
      this.status = this.t('status.running');
      try {
        const ws = (document.getElementById('workspaceSelect')?.value) || 'default';
        const cat = await window.api('/api/tool', {
          tool: 'setting.category.get', arguments: { workspace: ws, slug: 'item-level' }
        });
        const catId = (cat && (cat.id || cat.result?.id)) || null;
        const r = await window.api('/api/tool', {
          tool: 'setting.item.upsert',
          arguments: {
            workspace: ws, category_id: catId,
            core_summary: this.form.name,
            detailed_expansion: this.form.desc,
            sort_order: this.form.order,
            data: { numeric_range: this.form.range },
            is_global: true
          }
        });
        if (r.ok) {
          window.showToast('success', this.t('msg.saved'));
          this.cancel();
          await this.load();
        }
      } catch (e) {
        this.status = 'Error: ' + e.message;
      }
    },

    async remove(idx) {
      const l = this.levels[idx];
      if (!confirm('Delete ' + (l.core_summary || l.name) + '?')) return;
      this.status = this.t('status.running');
      try {
        const ws = (document.getElementById('workspaceSelect')?.value) || 'default';
        await window.api('/api/tool', {
          tool: 'setting.item.delete',
          arguments: { workspace: ws, item_id: l.id }
        });
        window.showToast('success', this.t('msg.deleted'));
        await this.load();
      } catch (e) {
        this.status = 'Error: ' + e.message;
      }
    }
  }));
});