/**
 * Novel OS - API Client
 * 统一的API请求封装，提供错误处理、重试、缓存等功能
 * @version 1.0.0
 */

(function() {
  'use strict';

  // 防止重复初始化
  if (window.ApiClient) {
    return;
  }

  /**
   * API请求队列
   */
  class RequestQueue {
    constructor() {
      this.queue = [];
      this.running = false;
    }

    async add(requestFn) {
      return new Promise((resolve, reject) => {
        this.queue.push({ requestFn, resolve, reject });
        this.process();
      });
    }

    async process() {
      if (this.running || this.queue.length === 0) return;
      this.running = true;

      const { requestFn, resolve, reject } = this.queue.shift();
      try {
        const result = await requestFn();
        resolve(result);
      } catch (error) {
        reject(error);
      } finally {
        this.running = false;
        this.process();
      }
    }
  }

  /**
   * API客户端
   */
  const ApiClient = {
    // 配置
    config: {
      baseUrl: '/api',
      timeout: 30000,
      retries: 3,
      retryDelay: 1000
    },

    // 状态
    state: {
      requestCount: 0,
      errorCount: 0,
      isOnline: true
    },

    // 请求队列
    queue: new RequestQueue(),

    // 缓存
    cache: new Map(),

    /**
     * 初始化
     */
    init() {
      console.log('[ApiClient] Initializing...');
      
      // 监听网络状态
      window.addEventListener('online', () => {
        this.state.isOnline = true;
        console.log('[ApiClient] Network online');
      });
      
      window.addEventListener('offline', () => {
        this.state.isOnline = false;
        console.log('[ApiClient] Network offline');
      });

      console.log('[ApiClient] Initialized');
    },

    /**
     * 基础请求方法
     * @param {string} method - HTTP方法
     * @param {string} endpoint - API端点
     * @param {Object} data - 请求数据
     * @param {Object} options - 请求选项
     */
    async request(method, endpoint, data = null, options = {}) {
      const {
        showLoading = true,
        showError = true,
        cache = false,
        cacheKey = null,
        cacheDuration = 5 * 60 * 1000, // 5分钟
        retry = true
      } = options;

      // 检查缓存
      if (cache && cacheKey && this.cache.has(cacheKey)) {
        const cached = this.cache.get(cacheKey);
        if (Date.now() - cached.time < cacheDuration) {
          console.log('[ApiClient] Cache hit:', cacheKey);
          return cached.data;
        }
      }

      // 显示加载状态
      if (showLoading) {
        window.AppCore?.setLoading(true);
      }

      this.state.requestCount++;

      try {
        const url = `${this.config.baseUrl}${endpoint}`;
        
        const fetchOptions = {
          method,
          headers: {
            'Content-Type': 'application/json',
            'X-Request-ID': this.generateRequestId()
          }
        };

        if (data && (method === 'POST' || method === 'PUT')) {
          fetchOptions.body = JSON.stringify(data);
        }

        // 发送请求
        const response = await fetch(url, fetchOptions);
        
        // 解析响应
        const result = await response.json();

        // 检查业务错误
        if (!result.ok) {
          throw new Error(result.error || 'Request failed');
        }

        // 缓存结果
        if (cache && cacheKey) {
          this.cache.set(cacheKey, { data: result.result, time: Date.now() });
        }

        return result.result;

      } catch (error) {
        this.state.errorCount++;
        
        // 重试逻辑
        if (retry && this.shouldRetry(error)) {
          console.log('[ApiClient] Retrying request...');
          await this.delay(this.config.retryDelay);
          return this.request(method, endpoint, data, { ...options, retry: false });
        }

        // 显示错误
        if (showError) {
          window.AppCore?.toast('error', '请求失败', error.message);
        }

        throw error;
      } finally {
        if (showLoading) {
          window.AppCore?.setLoading(false);
        }
      }
    },

    /**
     * GET请求
     */
    async get(endpoint, options = {}) {
      return this.request('GET', endpoint, null, options);
    },

    /**
     * POST请求
     */
    async post(endpoint, data, options = {}) {
      return this.request('POST', endpoint, data, options);
    },

    /**
     * PUT请求
     */
    async put(endpoint, data, options = {}) {
      return this.request('PUT', endpoint, data, options);
    },

    /**
     * DELETE请求
     */
    async delete(endpoint, options = {}) {
      return this.request('DELETE', endpoint, null, options);
    },

    /**
     * MCP工具调用
     * @param {string} tool - 工具名称
     * @param {Object} args - 参数
     * @param {Object} options - 选项
     */
    async callTool(tool, args = {}, options = {}) {
      return this.post('/tool', { tool, arguments: args }, options);
    },

    /**
     * 清除缓存
     * @param {string} pattern - 匹配模式
     */
    clearCache(pattern = null) {
      if (!pattern) {
        this.cache.clear();
      } else {
        for (const key of this.cache.keys()) {
          if (key.includes(pattern)) {
            this.cache.delete(key);
          }
        }
      }
    },

    /**
     * 生成请求ID
     */
    generateRequestId() {
      return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    },

    /**
     * 判断是否应重试
     */
    shouldRetry(error) {
      // 网络错误或5xx错误应重试
      return !navigator.onLine || 
             error.name === 'TypeError' || 
             (error.status >= 500 && error.status < 600);
    },

    /**
     * 延迟
     */
    delay(ms) {
      return new Promise(resolve => setTimeout(resolve, ms));
    },

    // ============== API快捷方法 ==============

    workspace: {
      async list(options = {}) {
        return ApiClient.callTool('workspace.list', {}, options);
      }
    },

    project: {
      async list(workspace, options = {}) {
        return ApiClient.callTool('project.list', { workspace }, options);
      }
    },

    setting: {
      async list(workspace, options = {}) {
        return ApiClient.callTool('setting.category.list', { workspace }, options);
      },
      
      async get(workspace, slug, options = {}) {
        return ApiClient.callTool('setting.category.get', { workspace, slug }, options);
      },
      
      async upsert(workspace, data, options = {}) {
        return ApiClient.callTool('setting.category.upsert', { workspace, ...data }, options);
      },
      
      async delete(workspace, categoryId, options = {}) {
        return ApiClient.callTool('setting.category.delete', { workspace, category_id: categoryId }, options);
      }
    },

    item: {
      async list(workspace, categoryId, options = {}) {
        return ApiClient.callTool('setting.item.list', { workspace, category_id: categoryId }, options);
      },
      
      async upsert(workspace, data, options = {}) {
        return ApiClient.callTool('setting.item.upsert', { workspace, ...data }, options);
      },
      
      async delete(workspace, itemId, options = {}) {
        return ApiClient.callTool('setting.item.delete', { workspace, item_id: itemId }, options);
      }
    },

    genre: {
      async list(options = {}) {
        return ApiClient.callTool('setting.genre.list', {}, options);
      },
      
      async upsert(data, options = {}) {
        return ApiClient.callTool('setting.genre.upsert', data, options);
      },
      
      async delete(slug, options = {}) {
        return ApiClient.callTool('setting.genre.delete', { slug }, options);
      }
    },

    promptTemplate: {
      async list(workspace, filters = {}, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('prompt.template.list', { workspace, project, ...filters }, options);
      },
      
      async get(workspace, templateKey, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('prompt.template.get', { workspace, project, template_key: templateKey }, options);
      },
      
      async create(workspace, data, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('prompt.template.upsert', { workspace, project, ...data }, options);
      },
      
      async update(workspace, templateKey, data, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('prompt.template.upsert', { workspace, project, template_key: templateKey, ...data }, options);
      },
      
      async delete(workspace, templateKey, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('prompt.template.delete', { workspace, project, template_key: templateKey }, options);
      }
    },

    modelProfile: {
      async list(workspace, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('model.profile.list', { workspace, project, ...options }, options);
      },
      
      async get(workspace, profileKey, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('model.profile.list', { workspace, project, profile_key: profileKey }, options);
      },
      
      async create(workspace, data, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('model.profile.upsert', { workspace, project, ...data }, options);
      },
      
      async update(workspace, profileKey, data, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('model.profile.upsert', { workspace, project, profile_key: profileKey, ...data }, options);
      },
      
      async delete(workspace, profileKey, options = {}) {
        const project = window.AppState?.currentProject;
        return ApiClient.callTool('model.profile.upsert', { workspace, project, profile_key: profileKey, status: 'inactive' }, options);
      }
    }
  };

  // 暴露到全局
  window.ApiClient = ApiClient;

  // 初始化
  ApiClient.init();

})();
