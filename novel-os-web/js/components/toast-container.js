/**
 * Novel OS - Toast Container Component
 * Global toast notification system
 * @version 1.0.0
 */

(function() {
  'use strict';

  document.addEventListener('alpine:init', () => {

    /**
     * Toast Container组件
     * 与Alpine store 'app'中的toasts集成
     */
    Alpine.data('toastContainer', () => ({
      /**
       * 获取toasts（从store）
       */
      get toasts() {
        return Alpine.store('app')?.toasts || [];
      },

      /**
       * 获取图标
       * @param {string} type - 类型
       */
      getIcon(type) {
        const icons = {
          success: '✓',
          error: '✕',
          warning: '⚠',
          info: 'ℹ'
        };
        return icons[type] || icons.info;
      },

      /**
       * 获取样式类
       * @param {string} type - 类型
       */
      getClass(type) {
        const classes = {
          success: 'bg-green-500 border-green-600',
          error: 'bg-red-500 border-red-600',
          warning: 'bg-yellow-500 border-yellow-600',
          info: 'bg-blue-500 border-blue-600'
        };
        return classes[type] || classes.info;
      },

      /**
       * 移除toast
       * @param {number} id - Toast ID
       */
      remove(id) {
        Alpine.store('app')?.removeToast(id);
      }
    }));

  });

  /**
   * 便捷函数：显示Toast
   * @param {string} type - 类型
   * @param {string} title - 标题
   * @param {string} message - 消息
   * @param {number} duration - 持续时间
   */
  window.showToast = function(type, title, message = '', duration = 3000) {
    const app = Alpine?.store('app');
    if (app) {
      app.addToast(type, title, message, duration);
    } else {
      // Fallback: 使用原生alert或console
      console.log(`[${type.toUpperCase()}] ${title}: ${message}`);
    }
  };

})();
