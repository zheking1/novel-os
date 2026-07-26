/**
 * Novel OS - Error Handler
 * 统一的错误处理工具
 * @version 1.0.0
 */
(function() {
  'use strict';

  if (window.ErrorHandler) {
    return;
  }

  window.ErrorHandler = {
    /**
     * 错误类型映射
     */
    errorTypes: {
      NETWORK_ERROR: 'network_error',
      API_ERROR: 'api_error',
      VALIDATION_ERROR: 'validation_error',
      AUTH_ERROR: 'auth_error',
      NOT_FOUND: 'not_found',
      UNKNOWN: 'unknown'
    },

    /**
     * 解析错误类型
     * @param {Error} error - 错误对象
     * @returns {string} 错误类型
     */
    parseErrorType(error) {
      if (!error) return this.errorTypes.UNKNOWN;
      
      const message = error.message || String(error);
      
      // 网络错误
      if (error.name === 'TypeError' && message.includes('fetch')) {
        return this.errorTypes.NETWORK_ERROR;
      }
      if (message.includes('NetworkError') || message.includes('network')) {
        return this.errorTypes.NETWORK_ERROR;
      }
      
      // 认证错误
      if (error.status === 401 || message.includes('unauthorized') || message.includes('认证')) {
        return this.errorTypes.AUTH_ERROR;
      }
      
      // 未找到
      if (error.status === 404 || message.includes('not found') || message.includes('不存在')) {
        return this.errorTypes.NOT_FOUND;
      }
      
      // API 错误
      if (error.status >= 400) {
        return this.errorTypes.API_ERROR;
      }
      
      return this.errorTypes.UNKNOWN;
    },

    /**
     * 获取用户友好的错误消息
     * @param {Error} error - 错误对象
     * @returns {string} 错误消息
     */
    getErrorMessage(error) {
      const type = this.parseErrorType(error);
      const message = error?.message || '未知错误';
      
      switch (type) {
        case this.errorTypes.NETWORK_ERROR:
          return '网络连接失败，请检查网络后重试';
        case this.errorTypes.AUTH_ERROR:
          return '登录已过期，请重新登录';
        case this.errorTypes.NOT_FOUND:
          return '请求的资源不存在';
        case this.errorTypes.API_ERROR:
          return message || '服务器处理请求失败';
        case this.errorTypes.VALIDATION_ERROR:
          return message || '数据验证失败';
        default:
          return message || '发生未知错误';
      }
    },

    /**
     * 处理 API 错误
     * @param {Error} error - 错误对象
     * @param {Object} options - 配置选项
     */
    handle(error, options = {}) {
      const {
        showToast = true,
        showAlert = false,
        fallback = null,
        context = ''
      } = options;

      const type = this.parseErrorType(error);
      const message = this.getErrorMessage(error);

      // 记录错误
      console.error(`[ErrorHandler]${context ? ' [' + context + ']' : ''}`, error);

      // 认证错误特殊处理
      if (type === this.errorTypes.AUTH_ERROR) {
        this.handleAuthError();
        return fallback;
      }

      // 显示错误提示
      if (showToast && window.showToast) {
        window.showToast('error', message);
      } else if (showAlert) {
        alert(message);
      }

      return fallback;
    },

    /**
     * 处理认证错误
     */
    handleAuthError() {
      // 清除登录状态
      localStorage.removeItem('novel-token');
      localStorage.removeItem('novel-workspace');
      localStorage.removeItem('novel-project');
      
      // 显示提示
      if (window.showToast) {
        window.showToast('warning', '登录已过期，请重新登录');
      }
      
      // 延迟跳转登录页
      setTimeout(() => {
        window.location.reload();
      }, 1500);
    },

    /**
     * 包装异步函数，自动处理错误
     * @param {Function} fn - 异步函数
     * @param {Object} options - 配置选项
     * @returns {Function} 包装后的函数
     */
    wrap(fn, options = {}) {
      return async (...args) => {
        try {
          return await fn(...args);
        } catch (error) {
          return this.handle(error, options);
        }
      };
    },

    /**
     * 重试机制
     * @param {Function} fn - 要执行的函数
     * @param {Object} options - 配置选项
     * @returns {Promise}
     */
    async retry(fn, options = {}) {
      const {
        maxAttempts = 3,
        delay = 1000,
        backoff = 2,
        shouldRetry = (error) => {
          const type = this.parseErrorType(error);
          return type === this.errorTypes.NETWORK_ERROR;
        }
      } = options;

      let lastError;
      let currentDelay = delay;

      for (let attempt = 1; attempt <= maxAttempts; attempt++) {
        try {
          return await fn();
        } catch (error) {
          lastError = error;
          
          if (attempt === maxAttempts || !shouldRetry(error)) {
            throw error;
          }

          console.log(`[ErrorHandler] Retry attempt ${attempt}/${maxAttempts} after ${currentDelay}ms`);
          await this.sleep(currentDelay);
          currentDelay *= backoff;
        }
      }

      throw lastError;
    },

    /**
     * 睡眠函数
     * @param {number} ms - 毫秒
     * @returns {Promise}
     */
    sleep(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    /**
     * 全局错误处理器
     */
    setupGlobalHandlers() {
      // 未处理的 Promise 拒绝
      window.addEventListener('unhandledrejection', (event) => {
        console.error('[ErrorHandler] Unhandled promise rejection:', event.reason);
        this.handle(event.reason, { context: 'Unhandled Promise' });
      });

      // 全局错误
      window.addEventListener('error', (event) => {
        console.error('[ErrorHandler] Global error:', event.error);
        // 只处理非资源加载错误
        if (event.error) {
          this.handle(event.error, { context: 'Global' });
        }
      });

      console.log('[ErrorHandler] Global handlers installed');
    }
  };

  console.log('[ErrorHandler] Initialized');
})();
