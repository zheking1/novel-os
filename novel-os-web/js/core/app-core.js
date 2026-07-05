/**
 * Novel OS - Application Core
 * 应用核心模块，提供全局工具函数和基础功能
 * @version 1.0.0
 */

(function() {
  'use strict';

  // 确保只初始化一次
  if (window.AppCore) {
    return;
  }

  const AppCore = {
    // 版本号
    version: '1.0.0',

    // 配置
    config: {
      apiBaseUrl: '/api',
      defaultWorkspace: 'default',
      defaultLanguage: 'zh'
    },

    // 状态
    state: {
      initialized: false,
      workspace: null,
      project: null,
      user: null
    },

    /**
     * 初始化应用核心
     */
    async init() {
      if (this.state.initialized) {
        console.log('[AppCore] Already initialized');
        return;
      }

      console.log('[AppCore] Initializing...');

      // 加载保存的配置
      this.loadConfig();

      // 初始化完成
      this.state.initialized = true;
      console.log('[AppCore] Initialized successfully');

      // 触发初始化完成事件
      window.dispatchEvent(new CustomEvent('app:initialized'));
    },

    /**
     * 加载配置
     */
    loadConfig() {
      try {
        const saved = localStorage.getItem('novel-os-config');
        if (saved) {
          this.config = { ...this.config, ...JSON.parse(saved) };
        }
      } catch (e) {
        console.warn('[AppCore] Failed to load config:', e);
      }
    },

    /**
     * 保存配置
     */
    saveConfig() {
      try {
        localStorage.setItem('novel-os-config', JSON.stringify(this.config));
      } catch (e) {
        console.warn('[AppCore] Failed to save config:', e);
      }
    },

    /**
     * 显示Toast通知
     * @param {string} type - 类型: success, error, warning, info
     * @param {string} title - 标题
     * @param {string} message - 消息内容
     * @param {number} duration - 持续时间(ms)
     */
    toast(type, title, message = '', duration = 3000) {
      const event = new CustomEvent('app:toast', {
        detail: { type, title, message, duration }
      });
      window.dispatchEvent(event);
    },

    /**
     * 设置加载状态
     * @param {boolean} loading - 是否加载中
     * @param {string} message - 加载消息
     */
    setLoading(loading, message = '') {
      const event = new CustomEvent('app:loading', {
        detail: { loading, message }
      });
      window.dispatchEvent(event);
    },

    /**
     * 安全的JSON解析
     * @param {string} str - JSON字符串
     * @param {*} defaultValue - 默认值
     */
    safeJsonParse(str, defaultValue = null) {
      try {
        return JSON.parse(str);
      } catch (e) {
        return defaultValue;
      }
    },

    /**
     * 防抖函数
     * @param {Function} fn - 要执行的函数
     * @param {number} delay - 延迟时间(ms)
     */
    debounce(fn, delay = 300) {
      let timer = null;
      return function(...args) {
        if (timer) clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay);
      };
    },

    /**
     * 节流函数
     * @param {Function} fn - 要执行的函数
     * @param {number} limit - 限制时间(ms)
     */
    throttle(fn, limit = 300) {
      let inThrottle = false;
      return function(...args) {
        if (!inThrottle) {
          fn.apply(this, args);
          inThrottle = true;
          setTimeout(() => inThrottle = false, limit);
        }
      };
    }
  };

  // 暴露到全局
  window.AppCore = AppCore;

  // DOM就绪后自动初始化
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => AppCore.init());
  } else {
    AppCore.init();
  }

})();
