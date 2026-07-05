/**
 * Novel OS - Router Module
 * 结构化路由管理，支持路由守卫和动态导航
 * @version 1.0.0
 */

(function() {
  'use strict';

  /**
   * 路由配置
   */
  const routes = {
    // ============ Worldbuilding Group ============
    'level-item': {
      component: 'itemLevelManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '物品等级',
      titleKey: 'level.item.title',
      icon: '⭐',
      requiresProject: false
    },
    'level-character': {
      component: 'characterLevelManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '人物等级',
      titleKey: 'level.character.title',
      icon: '📊',
      requiresProject: false
    },
    'level-skill': {
      component: 'skillLevelManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '技能等级',
      titleKey: 'level.skill.title',
      icon: '⚡',
      requiresProject: false
    },
    'level-tech': {
      component: 'techLevelManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '科技等级',
      titleKey: 'level.tech.title',
      icon: '🔬',
      requiresProject: false
    },
    'catalog-item': {
      component: 'itemCatalogManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '物品图鉴',
      titleKey: 'catalog.item.title',
      icon: '🎒',
      requiresProject: true
    },
    'catalog-skill': {
      component: 'skillCatalogManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '技能图鉴',
      titleKey: 'catalog.skill.title',
      icon: '📜',
      requiresProject: true
    },
    'world-location': {
      component: 'locationManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '地图地点',
      titleKey: 'world.location.title',
      icon: '🗺️',
      requiresProject: true
    },
    'world-creature': {
      component: 'creatureManager',
      group: 'worldbuilding',
      groupLabel: '世界设定',
      title: '生物图鉴',
      titleKey: 'world.creature.title',
      icon: '🐉',
      requiresProject: true
    },

    // ============ Knowledge Group ============
    'genre-manage': {
      component: 'genreManager',
      group: 'knowledge',
      groupLabel: '知识管理',
      title: '小说类型',
      titleKey: 'genre.title',
      icon: '📖',
      requiresProject: false
    },
    'category-manage': {
      component: 'categoryManager',
      group: 'knowledge',
      groupLabel: '知识管理',
      title: '分类管理',
      titleKey: 'category.title',
      icon: '📂',
      requiresProject: false
    },
    'binding-matrix': {
      component: 'bindingManager',
      group: 'knowledge',
      groupLabel: '知识管理',
      title: '类型绑定',
      titleKey: 'binding.title',
      icon: '🔗',
      requiresProject: false
    },
    'knowledge-pack': {
      component: 'knowledgePackManager',
      group: 'knowledge',
      groupLabel: '知识管理',
      title: '知识包',
      titleKey: 'knowledge.pack.title',
      icon: '📦',
      requiresProject: true
    },

    // ============ Story Group ============
    'story-canon': {
      component: 'canonManager',
      group: 'story',
      groupLabel: '故事设定',
      title: 'Canon文档',
      titleKey: 'story.canon.title',
      icon: '📄',
      requiresProject: true
    },
    'story-entities': {
      component: 'entityManager',
      group: 'story',
      groupLabel: '故事设定',
      title: '实体管理',
      titleKey: 'story.entities.title',
      icon: '👥',
      requiresProject: true
    },
    'story-rules': {
      component: 'rulesManager',
      group: 'story',
      groupLabel: '故事设定',
      title: '创作规则',
      titleKey: 'story.rules.title',
      icon: '📋',
      requiresProject: true
    },
    'story-volumes': {
      component: 'volumeManager',
      group: 'story',
      groupLabel: '故事设定',
      title: '卷管理',
      titleKey: 'story.volumes.title',
      icon: '📚',
      requiresProject: true
    },
    'story-threads': {
      component: 'threadManager',
      group: 'story',
      groupLabel: '故事设定',
      title: '情节线',
      titleKey: 'story.threads.title',
      icon: '🧵',
      requiresProject: true
    },
    'story-foreshadowing': {
      component: 'foreshadowingManager',
      group: 'story',
      groupLabel: '故事设定',
      title: '伏笔管理',
      titleKey: 'story.foreshadowing.title',
      icon: '🔮',
      requiresProject: true
    },

    // ============ System Group ============
    'system-health': {
      component: 'healthManager',
      group: 'system',
      groupLabel: '系统管理',
      title: '系统健康',
      titleKey: 'system.health.title',
      icon: '💓',
      requiresProject: false
    },
    'system-models': {
      component: 'modelManager',
      group: 'system',
      groupLabel: '系统管理',
      title: '模型配置',
      titleKey: 'system.models.title',
      icon: '🤖',
      requiresProject: false
    },
    'system-users': {
      component: 'userManager',
      group: 'system',
      groupLabel: '系统管理',
      title: '用户管理',
      titleKey: 'system.users.title',
      icon: '👤',
      requiresProject: false,
      requiresAdmin: true
    }
  };

  /**
   * 菜单组配置
   */
  const menuGroups = [
    {
      id: 'worldbuilding',
      label: '世界设定',
      labelKey: 'nav.worldbuilding',
      icon: '🌍',
      collapsed: false
    },
    {
      id: 'knowledge',
      label: '知识管理',
      labelKey: 'nav.knowledge',
      icon: '📚',
      collapsed: false
    },
    {
      id: 'story',
      label: '故事设定',
      labelKey: 'nav.story',
      icon: '✍️',
      collapsed: false
    },
    {
      id: 'system',
      label: '系统管理',
      labelKey: 'nav.system',
      icon: '⚙️',
      collapsed: true
    }
  ];

  /**
   * 路由器
   */
  const router = {
    routes,
    menuGroups,

    /**
     * 获取路由配置
     * @param {string} pageId - 页面ID
     */
    getRoute(pageId) {
      return this.routes[pageId];
    },

    /**
     * 获取所有路由
     */
    getAllRoutes() {
      return this.routes;
    },

    /**
     * 按组获取路由
     * @param {string} groupId - 组ID
     */
    getRoutesByGroup(groupId) {
      return Object.entries(this.routes)
        .filter(([_, route]) => route.group === groupId)
        .map(([id, route]) => ({ id, ...route }));
    },

    /**
     * 检查路由权限
     * @param {string} pageId - 页面ID
     * @param {Object} user - 用户对象
     */
    canAccess(pageId, user = null) {
      const route = this.getRoute(pageId);
      if (!route) return false;

      // 检查是否需要管理员权限
      if (route.requiresAdmin && user && !user.isAdmin) {
        return false;
      }

      return true;
    },

    /**
     * 导航到页面
     * @param {string} pageId - 页面ID
     * @param {Object} options - 选项
     */
    navigate(pageId, options = {}) {
      const route = this.getRoute(pageId);
      if (!route) {
        console.error(`Route not found: ${pageId}`);
        return false;
      }

      // 检查权限
      const user = Alpine?.store('user');
      if (!this.canAccess(pageId, user)) {
        console.warn(`Access denied to page: ${pageId}`);
        Alpine?.store('app')?.addToast('error', '访问被拒绝', '您没有权限访问此页面');
        return false;
      }

      // 检查是否需要项目
      const app = Alpine?.store('app');
      if (route.requiresProject && !app?.project) {
        Alpine?.store('app')?.addToast('warning', '请先选择项目', '');
        return false;
      }

      // 更新状态
      app?.setPage(pageId, route.group);

      // 更新URL hash（可选）
      if (!options.silent) {
        window.location.hash = pageId;
      }

      // 触发路由变更事件
      window.dispatchEvent(new CustomEvent('route:changed', {
        detail: { pageId, route, from: options.from }
      }));

      return true;
    },

    /**
     * 获取当前路由
     */
    getCurrentRoute() {
      const app = Alpine?.store('app');
      if (!app) return null;
      return this.getRoute(app.currentPage);
    },

    /**
     * 从URL hash初始化路由
     */
    initFromHash() {
      const hash = window.location.hash.slice(1);
      if (hash && this.routes[hash]) {
        this.navigate(hash, { silent: true });
        return true;
      }
      return false;
    },

    /**
     * 构建菜单数据
     * @param {Function} t - 翻译函数
     */
    buildMenu(t = (k) => k) {
      return this.menuGroups.map(group => ({
        ...group,
        label: t(group.labelKey) || group.label,
        items: this.getRoutesByGroup(group.id).map(route => ({
          id: route.id,
          title: t(route.titleKey) || route.title,
          icon: route.icon,
          requiresProject: route.requiresProject
        }))
      }));
    }
  };

  // 暴露到全局
  window.router = router;

  // 监听hash变化
  window.addEventListener('hashchange', (e) => {
    const newHash = window.location.hash.slice(1);
    if (router.routes[newHash]) {
      router.navigate(newHash, { silent: true });
    }
  });

})();
