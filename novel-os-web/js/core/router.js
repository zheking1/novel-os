/**
 * Novel OS - Router
 * 客户端路由管理，支持hash路由和页面切换
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.NovelRouter) {
    return;
  }

  const NovelRouter = {
    // 当前路由
    currentRoute: null,
    
    // 路由表
    routes: {},
    
    // 导航钩子
    beforeHooks: [],
    afterHooks: [],

    /**
     * 初始化路由
     */
    init() {
      console.log('[Router] Initializing...');
      
      // 监听hash变化
      window.addEventListener('hashchange', () => this.handleRouteChange());
      
      // 监听popstate
      window.addEventListener('popstate', () => this.handleRouteChange());
      
      // 初始路由
      this.handleRouteChange();
      
      console.log('[Router] Initialized');
    },

    /**
     * 注册路由
     * @param {string} path - 路由路径
     * @param {Object} config - 路由配置
     */
    register(path, config) {
      this.routes[path] = {
        path,
        component: config.component,
        beforeEnter: config.beforeEnter,
        meta: config.meta || {}
      };
    },

    /**
     * 导航到指定路径
     * @param {string} path - 目标路径
     * @param {Object} options - 导航选项
     */
    async navigate(path, options = {}) {
      const { replace = false, query = {} } = options;
      
      // 构建完整URL
      let url = path;
      if (Object.keys(query).length > 0) {
        const queryString = new URLSearchParams(query).toString();
        url += '?' + queryString;
      }
      
      // 执行导航
      if (replace) {
        window.location.replace('#' + url);
      } else {
        window.location.hash = url;
      }
    },

    /**
     * 处理路由变化
     */
    async handleRouteChange() {
      const hash = window.location.hash.slice(1) || '/';
      const [path, queryString] = hash.split('?');
      const query = queryString ? Object.fromEntries(new URLSearchParams(queryString)) : {};
      
      console.log('[Router] Route changed:', path, query);
      
      // 查找匹配的路由
      const route = this.matchRoute(path);
      
      if (!route) {
        console.warn('[Router] No route matched:', path);
        this.navigate('/');
        return;
      }
      
      // 执行before钩子
      for (const hook of this.beforeHooks) {
        const result = await hook(route, this.currentRoute);
        if (result === false) {
          return; // 取消导航
        }
      }
      
      // 执行路由beforeEnter
      if (route.beforeEnter) {
        const result = await route.beforeEnter(route, this.currentRoute);
        if (result === false) {
          return;
        }
      }
      
      // 更新当前路由
      const prevRoute = this.currentRoute;
      this.currentRoute = { ...route, query };
      
      // 触发路由变化事件
      window.dispatchEvent(new CustomEvent('route:changed', {
        detail: { 
          to: this.currentRoute, 
          from: prevRoute,
          path,
          query
        }
      }));
      
      // 执行after钩子
      for (const hook of this.afterHooks) {
        await hook(this.currentRoute, prevRoute);
      }
    },

    /**
     * 匹配路由
     * @param {string} path - 路径
     */
    matchRoute(path) {
      // 精确匹配
      if (this.routes[path]) {
        return this.routes[path];
      }
      
      // 动态路由匹配（简单实现）
      for (const routePath in this.routes) {
        if (this.isMatch(path, routePath)) {
          return this.routes[routePath];
        }
      }
      
      return null;
    },

    /**
     * 检查路径是否匹配
     * @param {string} path - 实际路径
     * @param {string} routePath - 路由路径
     */
    isMatch(path, routePath) {
      // 简单实现，支持 :param 格式
      const pathParts = path.split('/');
      const routeParts = routePath.split('/');
      
      if (pathParts.length !== routeParts.length) {
        return false;
      }
      
      for (let i = 0; i < routeParts.length; i++) {
        if (routeParts[i].startsWith(':')) {
          continue; // 动态参数，匹配任意
        }
        if (routeParts[i] !== pathParts[i]) {
          return false;
        }
      }
      
      return true;
    },

    /**
     * 添加before钩子
     * @param {Function} hook - 钩子函数
     */
    beforeEach(hook) {
      this.beforeHooks.push(hook);
    },

    /**
     * 添加after钩子
     * @param {Function} hook - 钩子函数
     */
    afterEach(hook) {
      this.afterHooks.push(hook);
    },

    /**
     * 获取当前路由
     */
    getCurrentRoute() {
      return this.currentRoute;
    },

    /**
     * 后退
     */
    back() {
      window.history.back();
    },

    /**
     * 前进
     */
    forward() {
      window.history.forward();
    }
  };

  window.NovelRouter = NovelRouter;
  NovelRouter.init();

})();
