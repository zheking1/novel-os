/**
 * 项目管理页面
 * 列出工作空间内的项目，支持创建和选择项目
 */
window.ProjectManagePage = {
  currentPage: null,

  async init() {
    this.currentPage = document.getElementById('content-area');
    this.currentPage.innerHTML = `
      <div style="padding: 16px;">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
          <h2 style="margin: 0;">项目列表</h2>
          <button onclick="ProjectManagePage.showCreateModal()" style="
            padding: 8px 16px;
            background: #1a1a2e;
            color: #e0e0e0;
            border: 1px solid #444;
            border-radius: 6px;
            cursor: pointer;
          ">新建项目</button>
        </div>
        <div id="pm-list" style="
          background: #16161e;
          border: 1px solid #2a2a3e;
          border-radius: 8px;
          padding: 16px;
        ">
          <div style="color: #666;">加载中...</div>
        </div>
      </div>
    `;
    await this.loadProjects();
    return true;
  },

  async loadProjects() {
    const listEl = document.getElementById('pm-list');
    const workspace = window.AppState?.currentWorkspace;
    
    if (!workspace) {
      listEl.innerHTML = '<div style="color: #888;">请先选择工作空间</div>';
      return;
    }

    try {
      const result = await window.ApiClient.project.list(workspace);
      const projects = result.projects || [];

      if (projects.length === 0) {
        listEl.innerHTML = `
          <div style="color: #888; text-align: center; padding: 32px 0;">
            暂无项目，点击右上角"新建项目"创建
          </div>
        `;
        return;
      }

      const currentProject = window.AppState?.currentProject;

      listEl.innerHTML = projects.map(p => `
        <div class="pm-item" data-slug="${p.slug}" style="
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 12px 16px;
          border-bottom: 1px solid #2a2a3e;
          cursor: pointer;
          border-radius: 6px;
          margin-bottom: 4px;
          ${p.slug === currentProject ? 'background: #1a1a2e; border: 1px solid #4a9eff;' : ''}
        " onmouseover="this.style.background='#1a1a2e'" onmouseout="if('${p.slug}'!=='${currentProject}')this.style.background=''">
          <div style="display: flex; align-items: center; gap: 12px;">
            <span style="font-size: 20px;">📚</span>
            <div>
              <div style="font-weight: 500; color: #e0e0e0;">${p.title || p.slug}</div>
              <div style="font-size: 12px; color: #666;">${p.slug}${p.description ? ' · ' + p.description.substring(0, 50) : ''}</div>
            </div>
          </div>
          <div style="display: flex; gap: 8px; align-items: center;">
            ${p.slug === currentProject ? '<span style="color: #4a9eff; font-size: 12px;">当前</span>' : `
              <button onclick="event.stopPropagation(); ProjectManagePage.selectProject('${p.slug}')" style="
                padding: 4px 12px;
                background: #2a2a3e;
                color: #e0e0e0;
                border: 1px solid #444;
                border-radius: 4px;
                cursor: pointer;
                font-size: 12px;
              ">选择</button>
            `}
          </div>
        </div>
      `).join('');
    } catch (e) {
      listEl.innerHTML = `<div style="color: #ff6b6b;">加载失败: ${e.message}</div>`;
    }
  },

  async selectProject(slug) {
    window.AppState.currentProject = slug;
    localStorage.setItem('currentProject', slug);
    
    // 更新项目选择器
    const projectSelector = document.getElementById('project-selector');
    if (projectSelector) {
      projectSelector.value = slug;
    }
    
    // 刷新菜单和页面
    window.MenuManager?.setProject(slug);
    window.dispatchEvent(new CustomEvent('project:changed', { detail: { project: slug } }));
    
    this.currentPage.innerHTML = `
      <div style="padding: 32px; text-align: center; color: #4a9eff;">
        <div style="font-size: 48px; margin-bottom: 16px;">✅</div>
        <h3>已选择项目: ${slug}</h3>
        <p style="color: #888;">左侧菜单已更新，请选择功能模块</p>
      </div>
    `;
  },

  showCreateModal() {
    const modal = document.createElement('div');
    modal.className = 'modal-overlay';
    modal.innerHTML = `
      <div class="modal-dialog" style="width: 400px;">
        <h3>新建项目</h3>
        <form id="pm-create-form" style="margin-top: 16px;">
          <div style="margin-bottom: 12px;">
            <label style="display: block; margin-bottom: 4px; color: #aaa;">项目标识 (slug)</label>
            <input type="text" id="pm-slug" required style="
              width: 100%;
              padding: 8px 12px;
              background: #1a1a2e;
              border: 1px solid #444;
              border-radius: 4px;
              color: #e0e0e0;
            " placeholder="例如: xianni">
          </div>
          <div style="margin-bottom: 12px;">
            <label style="display: block; margin-bottom: 4px; color: #aaa;">项目标题</label>
            <input type="text" id="pm-title" required style="
              width: 100%;
              padding: 8px 12px;
              background: #1a1a2e;
              border: 1px solid #444;
              border-radius: 4px;
              color: #e0e0e0;
            " placeholder="例如: 仙逆">
          </div>
          <div style="margin-bottom: 16px;">
            <label style="display: block; margin-bottom: 4px; color: #aaa;">描述 (可选)</label>
            <textarea id="pm-desc" rows="3" style="
              width: 100%;
              padding: 8px 12px;
              background: #1a1a2e;
              border: 1px solid #444;
              border-radius: 4px;
              color: #e0e0e0;
              resize: vertical;
            " placeholder="项目简介"></textarea>
          </div>
          <div style="display: flex; justify-content: flex-end; gap: 8px;">
            <button type="button" onclick="this.closest('.modal-overlay').remove()" style="
              padding: 8px 16px;
              background: #2a2a3e;
              color: #aaa;
              border: 1px solid #444;
              border-radius: 4px;
              cursor: pointer;
            ">取消</button>
            <button type="submit" style="
              padding: 8px 16px;
              background: #4a9eff;
              color: white;
              border: none;
              border-radius: 4px;
              cursor: pointer;
            ">创建</button>
          </div>
        </form>
      </div>
    `;
    document.body.appendChild(modal);
    modal.addEventListener('click', e => { if (e.target === modal) modal.remove(); });
    
    document.getElementById('pm-create-form').onsubmit = async (e) => {
      e.preventDefault();
      await this.createProject();
    };
  },

  async createProject() {
    const slug = document.getElementById('pm-slug').value.trim();
    const title = document.getElementById('pm-title').value.trim();
    const description = document.getElementById('pm-desc').value.trim();
    const workspace = window.AppState?.currentWorkspace;

    if (!workspace) {
      alert('请先选择工作空间');
      return;
    }

    try {
      await window.ApiClient.project.create(workspace, { slug, title, description: description || undefined });
      document.querySelector('.modal-overlay')?.remove();
      await this.loadProjects();
    } catch (e) {
      alert('创建失败: ' + e.message);
    }
  }
};
