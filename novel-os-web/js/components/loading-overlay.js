/**
 * Novel OS - Loading Overlay Component
 * Global loading indicator and skeleton screens
 * @version 1.0.0
 */

(function() {
  'use strict';

  document.addEventListener('alpine:init', () => {

    /**
     * Loading Overlay组件
     */
    Alpine.data('loadingOverlay', (config = {}) => ({
      // 配置
      message: config.message || '加载中...',
      spinner: config.spinner !== false,
      blur: config.blur !== false,
      opacity: config.opacity || 0.7,

      // 状态
      visible: false,

      /**
       * 显示loading
       * @param {string} message - 消息
       */
      show(message = null) {
        if (message) this.message = message;
        this.visible = true;
      },

      /**
       * 隐藏loading
       */
      hide() {
        this.visible = false;
      },

      /**
       * 切换显示状态
       */
      toggle() {
        this.visible = !this.visible;
      }
    }));

    /**
     * Skeleton Screen组件
     * 用于内容加载时的占位符
     */
    Alpine.data('skeletonScreen', (config = {}) => ({
      // 配置
      rows: config.rows || 5,
      columns: config.columns || 3,
      showHeader: config.showHeader !== false,
      animated: config.animated !== false,

      /**
       * 获取行数组
       */
      getRows() {
        return Array.from({ length: this.rows }, (_, i) => i);
      },

      /**
       * 获取列数组
       */
      getColumns() {
        return Array.from({ length: this.columns }, (_, i) => i);
      }
    }));

    /**
     * Loading Button组件
     */
    Alpine.data('loadingButton', (config = {}) => ({
      // 配置
      loadingText: config.loadingText || '处理中...',
      defaultText: config.defaultText || '提交',

      // 状态
      loading: false,

      /**
       * 开始loading
       * @param {string} text - 自定义文本
       */
      start(text = null) {
        if (text) this.loadingText = text;
        this.loading = true;
      },

      /**
       * 结束loading
       */
      stop() {
        this.loading = false;
      },

      /**
       * 执行异步操作
       * @param {Function} fn - 异步函数
       * @param {string} loadingText - loading文本
       */
      async execute(fn, loadingText = null) {
        this.start(loadingText);
        try {
          return await fn();
        } finally {
          this.stop();
        }
      }
    }));

  });

})();
