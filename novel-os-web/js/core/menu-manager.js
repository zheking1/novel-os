/**
 * Novel OS - Menu Manager
 * 菜单管理系统，支持三级菜单、权限控制、国际化
 * @version 2.0.0
 */

(function() {
  'use strict';

  if (window.MenuManager) {
    return;
  }

  const MenuManager = {
    /**
     * 菜单定义 - 三级结构
     * 一级: section (project/knowledge/system)
     * 二级: group (分组)
     * 三级: item (菜单项)
     */
    menuDefinition: {
      // ==================== 📚 项目管理 ====================
      project: {
        id: 'project',
        labelKey: 'section.project',
        icon: '📚',
        order: 1,
        requiresProject: false,
        groups: {
          // 设定管理
          'project-settings': {
            id: 'project-settings',
            labelKey: 'nav.settingsGroup',
            icon: '⚙️',
            order: 1,
            items: [
              { id: 'canon-list', labelKey: 'nav.canonList', icon: '📄', path: '/project/canon' },
              { id: 'entities-list', labelKey: 'nav.entityList', icon: '👥', path: '/project/entities' },
              { id: 'rules-list', labelKey: 'nav.rulesList', icon: '📋', path: '/project/rules' },
              { id: 'graph-view', labelKey: 'nav.graphView', icon: '🔗', path: '/project/graph' }
            ]
          },
          // 剧情管理
          'project-plot': {
            id: 'project-plot',
            labelKey: 'nav.plotGroup',
            icon: '📖',
            order: 2,
            items: [
              { id: 'plot-volumes', labelKey: 'nav.volumes', icon: '📚', path: '/project/volumes' },
              { id: 'plot-threads', labelKey: 'nav.threads', icon: '🧵', path: '/project/threads' },
              { id: 'foreshadowing-list', labelKey: 'nav.foreshadowList', icon: '🔮', path: '/project/foreshadowing' }
            ]
          },
          // 生成与审查
          'project-generation': {
            id: 'project-generation',
            labelKey: 'nav.generationGroup',
            icon: '🔧',
            order: 3,
            items: [
              { id: 'context-preview', labelKey: 'nav.contextPreview', icon: '👁️', path: '/project/context' },
              { id: 'review-tasks', labelKey: 'nav.reviewTasks', icon: '🔍', path: '/project/review' },
              { id: 'compliance', labelKey: 'nav.compliance', icon: '✅', path: '/project/compliance' },
              { id: 'pipeline', labelKey: 'nav.pipeline', icon: '⚙️', path: '/project/pipeline' },
              { id: 'chapters', labelKey: 'nav.chapters', icon: '📝', path: '/project/chapters' }
            ]
          },
          // 项目知识
          'project-knowledge': {
            id: 'project-knowledge',
            labelKey: 'nav.projectKnowledgeGroup',
            icon: '🗂️',
            order: 4,
            items: [
              { id: 'project-world-rules', labelKey: 'nav.worldRules', icon: '🌍', path: '/project/world-rules' },
              { id: 'project-characters', labelKey: 'nav.characters', icon: '👤', path: '/project/characters' },
              { id: 'project-factions', labelKey: 'nav.factions', icon: '🏴', path: '/project/factions' },
              { id: 'project-world-state', labelKey: 'nav.worldState', icon: '🗺️', path: '/project/world-state' }
            ]
          },
          // 本地项目
          'project-local': {
            id: 'project-local',
            labelKey: 'nav.localGroup',
            icon: '💻',
            order: 5,
            items: [
              { id: 'knowledge-pack', labelKey: 'nav.knowledgePack', icon: '📦', path: '/project/knowledge-pack' },
              { id: 'local-projects', labelKey: 'nav.localProjects', icon: '📁', path: '/project/local-projects' },
              { id: 'local-chapters', labelKey: 'nav.localChapters', icon: '📄', path: '/project/local-chapters' },
              { id: 'local-pipeline', labelKey: 'nav.localPipeline', icon: '🔄', path: '/project/local-pipeline' }
            ]
          }
        }
      },

      // ==================== 🧠 知识库 ====================
      knowledge: {
        id: 'knowledge',
        labelKey: 'section.knowledge',
        icon: '🧠',
        order: 2,
        requiresProject: false,
        groups: {
          // 知识管理
          'knowledge-mgmt': {
            id: 'knowledge-mgmt',
            labelKey: 'nav.knowledgeMgmtGroup',
            icon: '📚',
            order: 1,
            items: [
              { id: 'uk-manage', labelKey: 'nav.ukManage', icon: '📖', path: '/knowledge/uk-manage' },
              { id: 'auto-search', labelKey: 'nav.autoSearch', icon: '🔍', path: '/knowledge/auto-search' },
              { id: 'knowledge-graph', labelKey: 'nav.knowledgeGraph', icon: '🕸️', path: '/knowledge/graph' },
              { id: 'knowledge-stats', labelKey: 'nav.knowledgeStats', icon: '📊', path: '/knowledge/stats' },
              { id: 'genre-manage', labelKey: 'genre.title', icon: '🎭', path: '/knowledge/genre' },
              { id: 'category-manage', labelKey: 'category.title', icon: '📂', path: '/knowledge/category' },
              { id: 'binding-matrix', labelKey: 'binding.title', icon: '🔗', path: '/knowledge/binding' }
            ]
          },
          // 知识审查
          'knowledge-review': {
            id: 'knowledge-review',
            labelKey: 'nav.knowledgeReviewGroup',
            icon: '🔍',
            order: 2,
            items: [
              { id: 'knowledge-review', labelKey: 'nav.knowledgeReview', icon: '📋', path: '/knowledge/review' },
              { id: 'knowledge-expiry', labelKey: 'nav.knowledgeExpiry', icon: '⏰', path: '/knowledge/expiry' }
            ]
          }
        }
      },

      // ==================== ⚙️ 系统管理 ====================
      system: {
        id: 'system',
        labelKey: 'section.system',
        icon: '⚙️',
        order: 3,
        requiresProject: false,
        groups: {
          // 项目管理
          'sys-project-mgmt': {
            id: 'sys-project-mgmt',
            labelKey: 'nav.projectMgmtGroup',
            icon: '📁',
            order: 0,
            requiresProject: false,
            items: [
              { id: 'project-manage', labelKey: 'nav.projectManage', icon: '📂', path: '/projects' }
            ]
          },
          // 模型配置
          'sys-model': {
            id: 'sys-model',
            labelKey: 'nav.modelGroup',
            icon: '🤖',
            order: 1,
            items: [
              { id: 'model-profiles', labelKey: 'nav.modelProfiles', icon: '⚙️', path: '/system/model-profiles' },
              { id: 'model-cost', labelKey: 'nav.costReport', icon: '💰', path: '/system/cost' }
            ]
          },
          // 模板管理
          'sys-template': {
            id: 'sys-template',
            labelKey: 'nav.templateGroup',
            icon: '📋',
            order: 2,
            items: [
              { id: 'template-list', labelKey: 'nav.templateList', icon: '📝', path: '/system/templates' },
              { id: 'market-browse', labelKey: 'nav.marketBrowse', icon: '🏪', path: '/system/market' }
            ]
          },
          // Skill 管理
          'sys-skill': {
            id: 'sys-skill',
            labelKey: 'nav.skillGroup',
            icon: '🎯',
            order: 3,
            items: [
              { id: 'skill-manage', labelKey: 'nav.skillManage', icon: '🎯', path: '/system/skills' }
            ]
          },
          // 数据管理
          'sys-data': {
            id: 'sys-data',
            labelKey: 'nav.dataGroup',
            icon: '💾',
            order: 4,
            items: [
              { id: 'sync-status', labelKey: 'nav.syncStatus', icon: '🔄', path: '/system/sync' },
              { id: 'sync-conflicts', labelKey: 'nav.syncConflicts', icon: '⚠️', path: '/system/conflicts' },
              { id: 'audit-logs', labelKey: 'nav.auditLogs', icon: '📜', path: '/system/audit' },
              { id: 'offline-status', labelKey: 'nav.offlineStatus', icon: '📴', path: '/system/offline' }
            ]
          },
          // 系统监控
          'sys-monitor': {
            id: 'sys-monitor',
            labelKey: 'nav.monitorGroup',
            icon: '📊',
            order: 5,
            items: [
              { id: 'sys-health', labelKey: 'nav.sysHealth', icon: '💓', path: '/system/health' },
              { id: 'sys-cache', labelKey: 'nav.sysCache', icon: '🗄️', path: '/system/cache' },
              { id: 'sys-backup', labelKey: 'nav.sysBackup', icon: '💾', path: '/system/backup' }
            ]
          },
          // 系统信息
          'sys-system': {
            id: 'sys-system',
            labelKey: 'nav.systemInfo',
            icon: 'ℹ️',
            order: 6,
            items: [
              { id: 'system-connection', labelKey: 'nav.connection', icon: '🌐', path: '/system/connection' },
              { id: 'system-account', labelKey: 'nav.account', icon: '👤', path: '/system/account' },
              { id: 'system-users', labelKey: 'nav.users', icon: '👥', path: '/system/users' },
              { id: 'system-debug', labelKey: 'nav.debug', icon: '🐛', path: '/system/debug' }
            ]
          }
        }
      }
    },

    // 状态
    state: {
      currentPage: null,
      expandedSections: new Set(['project', 'knowledge', 'system']),
      expandedGroups: new Set(['project-settings', 'knowledge-mgmt', 'sys-monitor']),
      favorites: new Set()
    },

    /**
     * 初始化
     */
    init() {
      console.log('[MenuManager] Initializing...');
      this.loadState();
      console.log('[MenuManager] Initialized');
    },

    /**
     * 加载保存的状态
     */
    loadState() {
      try {
        const saved = localStorage.getItem('novel-os-menu-state');
        if (saved) {
          const state = JSON.parse(saved);
          if (state.expandedSections) {
            this.state.expandedSections = new Set(state.expandedSections);
          }
          if (state.expandedGroups) {
            this.state.expandedGroups = new Set(state.expandedGroups);
          }
          if (state.favorites) {
            this.state.favorites = new Set(state.favorites);
          }
        }
      } catch (e) {
        console.warn('[MenuManager] Failed to load state:', e);
      }
    },

    /**
     * 保存状态
     */
    saveState() {
      try {
        const state = {
          expandedSections: Array.from(this.state.expandedSections),
          expandedGroups: Array.from(this.state.expandedGroups),
          favorites: Array.from(this.state.favorites)
        };
        localStorage.setItem('novel-os-menu-state', JSON.stringify(state));
      } catch (e) {
        console.warn('[MenuManager] Failed to save state:', e);
      }
    },

    /**
     * 获取完整菜单结构
     */
    getMenu(options = {}) {
      const { project = null, t = (key) => key } = options;
      const menu = [];

      for (const sectionId in this.menuDefinition) {
        const section = this.menuDefinition[sectionId];

        // 如果需要项目但没有选择项目，跳过
        if (section.requiresProject && !project) {
          continue;
        }

        const groups = [];

        for (const groupId in section.groups) {
          const group = section.groups[groupId];
          
          // 如果分组需要项目但没有选择项目，跳过
          if (group.requiresProject !== false && !project) {
            continue;
          }

          const items = [];

          for (const item of group.items) {
            items.push({
              ...item,
              label: t(item.labelKey) || item.label,
              isActive: this.state.currentPage === item.id,
              isFavorite: this.state.favorites.has(item.id)
            });
          }

          if (items.length > 0) {
            groups.push({
              id: group.id,
              label: t(group.labelKey) || group.label,
              icon: group.icon,
              order: group.order,
              isExpanded: this.state.expandedGroups.has(group.id),
              items
            });
          }
        }

        // 按order排序
        groups.sort((a, b) => a.order - b.order);

        if (groups.length > 0) {
          menu.push({
            id: section.id,
            label: t(section.labelKey) || section.label,
            icon: section.icon,
            order: section.order,
            isExpanded: this.state.expandedSections.has(section.id),
            groups
          });
        }
      }

      // 按order排序
      menu.sort((a, b) => a.order - b.order);

      return menu;
    },

    /**
     * 切换一级菜单展开状态
     */
    toggleSection(sectionId) {
      if (this.state.expandedSections.has(sectionId)) {
        this.state.expandedSections.delete(sectionId);
      } else {
        this.state.expandedSections.add(sectionId);
      }
      this.saveState();
      this.render();
    },

    /**
     * 切换二级分组展开状态
     */
    toggleGroup(groupId) {
      if (this.state.expandedGroups.has(groupId)) {
        this.state.expandedGroups.delete(groupId);
      } else {
        this.state.expandedGroups.add(groupId);
      }
      this.saveState();
      this.render();
    },

    /**
     * 重新渲染菜单
     */
    render() {
      window.dispatchEvent(new CustomEvent('menu:changed'));
    },

    /**
     * 设置当前页面
     */
    setCurrentPage(pageId) {
      this.state.currentPage = pageId;

      // 找到所属的一级和二级菜单并展开
      for (const sectionId in this.menuDefinition) {
        const section = this.menuDefinition[sectionId];
        for (const groupId in section.groups) {
          const group = section.groups[groupId];
          if (group.items.some(item => item.id === pageId)) {
            this.state.expandedSections.add(sectionId);
            this.state.expandedGroups.add(groupId);
          }
        }
      }

      this.saveState();

      window.dispatchEvent(new CustomEvent('menu:page-changed', {
        detail: { pageId }
      }));
    },

    /**
     * 获取页面信息
     */
    getPageInfo(pageId) {
      for (const sectionId in this.menuDefinition) {
        const section = this.menuDefinition[sectionId];
        for (const groupId in section.groups) {
          const group = section.groups[groupId];
          const item = group.items.find(i => i.id === pageId);
          if (item) {
            return {
              ...item,
              sectionId,
              sectionLabel: section.labelKey,
              sectionIcon: section.icon,
              groupId,
              groupLabel: group.labelKey,
              groupIcon: group.icon
            };
          }
        }
      }
      return null;
    },

    /**
     * 切换收藏
     */
    toggleFavorite(pageId) {
      if (this.state.favorites.has(pageId)) {
        this.state.favorites.delete(pageId);
      } else {
        this.state.favorites.add(pageId);
      }
      this.saveState();

      window.dispatchEvent(new CustomEvent('menu:favorite-toggled', {
        detail: { pageId, isFavorite: this.state.favorites.has(pageId) }
      }));
    },

    /**
     * 获取面包屑
     */
    getBreadcrumbs(pageId, t = (key) => key) {
      const breadcrumbs = [{ label: t('nav.home'), path: '/' }];

      const pageInfo = this.getPageInfo(pageId);
      if (pageInfo) {
        // 一级菜单
        breadcrumbs.push({
          label: t(pageInfo.sectionLabel),
          path: null
        });
        // 二级分组
        breadcrumbs.push({
          label: t(pageInfo.groupLabel),
          path: null
        });
        // 三级菜单
        breadcrumbs.push({
          label: t(pageInfo.labelKey),
          path: pageInfo.path
        });
      }

      return breadcrumbs;
    },

    /**
     * 查找页面所属的 section
     */
    findSectionByPageId(pageId) {
      for (const sectionId in this.menuDefinition) {
        const section = this.menuDefinition[sectionId];
        for (const groupId in section.groups) {
          const group = section.groups[groupId];
          if (group.items.some(item => item.id === pageId)) {
            return section;
          }
        }
      }
      return null;
    }
  };

  window.MenuManager = MenuManager;
  MenuManager.init();

})();
