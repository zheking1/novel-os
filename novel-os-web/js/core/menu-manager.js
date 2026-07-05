/**
 * Novel OS - Menu Manager
 * 菜单管理系统，支持动态菜单、权限控制、国际化
 * @version 1.0.0
 */

(function() {
  'use strict';

  // 防止重复初始化
  if (window.MenuManager) {
    return;
  }

  /**
   * 菜单管理器
   */
  const MenuManager = {
    // 菜单定义
    menuDefinition: {
      worldbuilding: {
        id: 'worldbuilding',
        labelKey: 'nav.worldbuilding',
        label: '世界设定',
        icon: '🌍',
        order: 1,
        items: [
          { id: 'level-item', labelKey: 'level.item.title', label: '物品等级', icon: '⭐', path: '/world/level-item', requiresProject: false },
          { id: 'level-character', labelKey: 'level.character.title', label: '人物等级', icon: '📊', path: '/world/level-character', requiresProject: false },
          { id: 'level-skill', labelKey: 'level.skill.title', label: '技能等级', icon: '⚡', path: '/world/level-skill', requiresProject: false },
          { id: 'level-tech', labelKey: 'level.tech.title', label: '科技等级', icon: '🔬', path: '/world/level-tech', requiresProject: false },
          { id: 'catalog-item', labelKey: 'catalog.item.title', label: '物品图鉴', icon: '🎒', path: '/world/catalog-item', requiresProject: true },
          { id: 'catalog-skill', labelKey: 'catalog.skill.title', label: '技能图鉴', icon: '📜', path: '/world/catalog-skill', requiresProject: true }
        ]
      },
      knowledge: {
        id: 'knowledge',
        labelKey: 'nav.knowledge',
        label: '知识管理',
        icon: '📚',
        order: 2,
        items: [
          { id: 'genre-manage', labelKey: 'genre.title', label: '小说类型', icon: '📖', path: '/knowledge/genre', requiresProject: false },
          { id: 'category-manage', labelKey: 'category.title', label: '分类管理', icon: '📂', path: '/knowledge/category', requiresProject: false },
          { id: 'binding-matrix', labelKey: 'binding.title', label: '类型绑定', icon: '🔗', path: '/knowledge/binding', requiresProject: false },
          { id: 'knowledge-pack', labelKey: 'knowledge.pack.title', label: '知识包', icon: '📦', path: '/knowledge/pack', requiresProject: true }
        ]
      },
      story: {
        id: 'story',
        labelKey: 'nav.story',
        label: '故事设定',
        icon: '✍️',
        order: 3,
        items: [
          { id: 'story-canon', labelKey: 'story.canon.title', label: 'Canon文档', icon: '📄', path: '/story/canon', requiresProject: true },
          { id: 'story-entities', labelKey: 'story.entities.title', label: '实体管理', icon: '👥', path: '/story/entities', requiresProject: true },
          { id: 'story-rules', labelKey: 'story.rules.title', label: '创作规则', icon: '📋', path: '/story/rules', requiresProject: true },
          { id: 'story-volumes', labelKey: 'story.volumes.title', label: '卷管理', icon: '📚', path: '/story/volumes', requiresProject: true }
        ]
      },
      system: {
        id: 'system',
        labelKey: 'nav.system',
        label: '系统管理',
        icon: '⚙️',
        order: 4,
        items: [
          { id: 'system-health', labelKey: 'system.health.title', label: '系统健康', icon: '💓', path: '/system/health', requiresProject: false },
          { id: 'system-models', labelKey: 'system.models.title', label: '模型配置', icon: '🤖', path: '/system/models', requiresProject: false }
        ]
      }
    },

    // 状态
    state: {
      currentPage: null,
      expandedGroups: new Set(['worldbuilding', 'knowledge']),
      favorites: new Set()
    },

    /**
     * 初始化
     */
    init() {
      console.log('[MenuManager] Initializing...');
      
      // 加载保存的状态
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
          expandedGroups: Array.from(this.state.expandedGroups),
          favorites: Array.from(this.state.favorites)
        };
        localStorage.setItem('novel-os-menu-state', JSON.stringify(state));
      } catch (e) {
        console.warn('[MenuManager] Failed to save state:', e);
      }
    },

    /**
     * 获取菜单结构
     * @param {Object} options - 选项
     */
    getMenu(options = {}) {
      const { project = null, t = (key) => key } = options;
      
      const menu = [];
      
      for (const groupId in this.menuDefinition) {
        const group = this.menuDefinition[groupId];
        const items = [];
        
        for (const item of group.items) {
          // 检查是否需要项目
          if (item.requiresProject && !project) {
            continue;
          }
          
          items.push({
            ...item,
            label: t(item.labelKey) || item.label,
            isActive: this.state.currentPage === item.id,
            isFavorite: this.state.favorites.has(item.id)
          });
        }
        
        if (items.length > 0) {
          menu.push({
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
      menu.sort((a, b) => a.order - b.order);
      
      return menu;
    },

    /**
     * 切换组展开状态
     * @param {string} groupId - 组ID
     */
    toggleGroup(groupId) {
      if (this.state.expandedGroups.has(groupId)) {
        this.state.expandedGroups.delete(groupId);
      } else {
        this.state.expandedGroups.add(groupId);
      }
      this.saveState();
      
      // 触发事件
      window.dispatchEvent(new CustomEvent('menu:group-toggled', {
        detail: { groupId, expanded: this.state.expandedGroups.has(groupId) }
      }));
    },

    /**
     * 设置当前页面
     * @param {string} pageId - 页面ID
     */
    setCurrentPage(pageId) {
      this.state.currentPage = pageId;
      
      // 找到所属组并展开
      for (const groupId in this.menuDefinition) {
        const group = this.menuDefinition[groupId];
        if (group.items.some(item => item.id === pageId)) {
          this.state.expandedGroups.add(groupId);
        }
      }
      
      this.saveState();
      
      // 触发事件
      window.dispatchEvent(new CustomEvent('menu:page-changed', {
        detail: { pageId }
      }));
    },

    /**
     * 获取页面信息
     * @param {string} pageId - 页面ID
     */
    getPageInfo(pageId) {
      for (const groupId in this.menuDefinition) {
        const group = this.menuDefinition[groupId];
        const item = group.items.find(i => i.id === pageId);
        if (item) {
          return {
            ...item,
            groupId,
            groupLabel: group.label,
            groupIcon: group.icon
          };
        }
      }
      return null;
    },

    /**
     * 切换收藏
     * @param {string} pageId - 页面ID
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
     * @param {string} pageId - 页面ID
     * @param {Function} t - 翻译函数
     */
    getBreadcrumbs(pageId, t = (key) => key) {
      const breadcrumbs = [{ label: t('nav.home'), path: '/' }];
      
      const pageInfo = this.getPageInfo(pageId);
      if (pageInfo) {
        breadcrumbs.push({
          label: t(pageInfo.groupLabel) || pageInfo.groupLabel,
          path: null
        });
        breadcrumbs.push({
          label: t(pageInfo.labelKey) || pageInfo.label,
          path: pageInfo.path
        });
      }
      
      return breadcrumbs;
    }
  };

  // 暴露到全局
  window.MenuManager = MenuManager;

  // 初始化
  MenuManager.init();

})();
