/**
 * Novel OS - API Wrapper Layer
 * 统一的API调用封装，提供错误处理、loading状态、缓存机制
 * @version 1.0.0
 */

(function() {
  'use strict';

  /**
   * API客户端
   */
  const apiClient = {
    /**
     * 基础API调用
     * @param {string} tool - 工具名称
     * @param {Object} args - 参数
     * @param {Object} options - 配置选项
     * @returns {Promise<any>}
     */
    async call(tool, args = {}, options = {}) {
      const {
        showLoading = true,
        showError = true,
        cache = false,
        cacheKey = null,
        cacheDuration = 5 * 60 * 1000 // 5分钟缓存
      } = options;

      // 检查缓存
      if (cache && cacheKey) {
        const cached = this.cache.get(cacheKey);
        if (cached && Date.now() - cached.time < cacheDuration) {
          return cached.data;
        }
      }

      // 显示loading
      if (showLoading && window.Alpine && Alpine.store('app')) {
        Alpine.store('app').setLoading(true);
      }

      try {
        const result = await window.api('/api/tool', { tool, arguments: args });

        if (!result.ok) {
          const errorMsg = result.error?.message || result.error || 'API调用失败';
          throw new Error(errorMsg);
        }

        // 缓存结果
        if (cache && cacheKey) {
          this.cache.set(cacheKey, { data: result.result, time: Date.now() });
        }

        return result.result;
      } catch (error) {
        if (showError) {
          window.showToast('error', '请求失败', error.message);
        }
        throw error;
      } finally {
        if (showLoading && window.Alpine && Alpine.store('app')) {
          Alpine.store('app').setLoading(false);
        }
      }
    },

    /**
     * 缓存存储
     */
    cache: new Map(),

    /**
     * 清除缓存
     * @param {string} pattern - 匹配模式（可选）
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

    // ==================== Setting API ====================

    setting: {
      /**
       * 列出分类
       * @param {string} workspace - 工作区
       * @param {Object} options - 选项
       */
      async list(workspace, options = {}) {
        return apiClient.call('setting.category.list', {
          workspace,
          is_active: options.isActive !== false
        }, options);
      },

      /**
       * 获取分类
       * @param {string} workspace - 工作区
       * @param {string} slug - 分类slug
       */
      async get(workspace, slug, options = {}) {
        return apiClient.call('setting.category.get', {
          workspace,
          slug
        }, options);
      },

      /**
       * 创建/更新分类
       * @param {string} workspace - 工作区
       * @param {Object} data - 数据
       */
      async upsert(workspace, data, options = {}) {
        return apiClient.call('setting.category.upsert', {
          workspace,
          ...data
        }, { ...options, showLoading: true });
      },

      /**
       * 删除分类
       * @param {string} workspace - 工作区
       * @param {string} categoryId - 分类ID
       */
      async delete(workspace, categoryId, options = {}) {
        return apiClient.call('setting.category.delete', {
          workspace,
          category_id: categoryId
        }, { ...options, showLoading: true });
      }
    },

    // ==================== Item API ====================

    item: {
      /**
       * 列出条目
       * @param {string} workspace - 工作区
       * @param {string} categoryId - 分类ID
       */
      async list(workspace, categoryId, options = {}) {
        return apiClient.call('setting.item.list', {
          workspace,
          category_id: categoryId
        }, options);
      },

      /**
       * 获取条目
       * @param {string} workspace - 工作区
       * @param {string} itemId - 条目ID
       */
      async get(workspace, itemId, options = {}) {
        return apiClient.call('setting.item.get', {
          workspace,
          item_id: itemId
        }, options);
      },

      /**
       * 创建/更新条目
       * @param {string} workspace - 工作区
       * @param {Object} data - 数据
       */
      async upsert(workspace, data, options = {}) {
        return apiClient.call('setting.item.upsert', {
          workspace,
          ...data
        }, { ...options, showLoading: true });
      },

      /**
       * 删除条目
       * @param {string} workspace - 工作区
       * @param {string} itemId - 条目ID
       */
      async delete(workspace, itemId, options = {}) {
        return apiClient.call('setting.item.delete', {
          workspace,
          item_id: itemId
        }, { ...options, showLoading: true });
      }
    },

    // ==================== Genre API ====================

    genre: {
      /**
       * 列出小说类型
       */
      async list(options = {}) {
        return apiClient.call('setting.genre.list', {}, options);
      },

      /**
       * 获取小说类型
       * @param {string} slug - 类型标识
       */
      async get(slug, options = {}) {
        // genre没有get接口，从list中查找
        const list = await this.list(options);
        return list.find(g => (g.slug || g.genre) === slug);
      },

      /**
       * 创建/更新小说类型
       * @param {Object} data - 数据
       */
      async upsert(data, options = {}) {
        return apiClient.call('setting.genre.upsert', data, {
          ...options,
          showLoading: true
        });
      },

      /**
       * 删除小说类型
       * @param {string} slug - 类型标识
       */
      async delete(slug, options = {}) {
        return apiClient.call('setting.genre.delete', { slug }, {
          ...options,
          showLoading: true
        });
      }
    },

    // ==================== Binding API ====================

    binding: {
      /**
       * 列出绑定关系
       * @param {string} genreSlug - 类型标识（可选）
       */
      async list(genreSlug = null, options = {}) {
        return apiClient.call('genre.binding.list', {
          genre_slug: genreSlug
        }, options);
      },

      /**
       * 获取绑定矩阵
       */
      async matrix(options = {}) {
        return apiClient.call('genre.binding.matrix', {}, options);
      },

      /**
       * 批量更新绑定
       * @param {Array} bindings - 绑定数据
       */
      async bulkUpsert(bindings, options = {}) {
        return apiClient.call('genre.binding.bulk_upsert', { bindings }, {
          ...options,
          showLoading: true
        });
      }
    },

    // ==================== Canon API ====================

    canon: {
      /**
       * 列出Canon文档
       * @param {string} workspace - 工作区
       * @param {string} project - 项目
       * @param {Object} filters - 过滤器
       */
      async list(workspace, project, filters = {}, options = {}) {
        return apiClient.call('canon.doc.list', {
          workspace,
          project,
          doc_types: filters.types || null,
          statuses: filters.statuses || null,
          query: filters.search || null,
          limit: filters.limit || 50,
          offset: filters.offset || 0
        }, options);
      },

      /**
       * 获取Canon文档
       * @param {string} workspace - 工作区
       * @param {string} project - 项目
       * @param {string} key - 文档key
       */
      async get(workspace, project, key, options = {}) {
        return apiClient.call('canon.doc.get', {
          workspace,
          project,
          key
        }, options);
      },

      /**
       * 创建/更新Canon文档
       * @param {string} workspace - 工作区
       * @param {string} project - 项目
       * @param {Object} data - 数据
       */
      async upsert(workspace, project, data, options = {}) {
        return apiClient.call('canon.doc.upsert', {
          workspace,
          project,
          ...data
        }, { ...options, showLoading: true });
      }
    },

    // ==================== Entity API ====================

    entity: {
      /**
       * 列出实体
       * @param {string} workspace - 工作区
       * @param {string} project - 项目
       * @param {Object} filters - 过滤器
       */
      async list(workspace, project, filters = {}, options = {}) {
        return apiClient.call('state.entity.list', {
          workspace,
          project,
          entity_type: filters.type || null,
          query: filters.search || null,
          tags: filters.tags || null,
          limit: filters.limit || 100,
          offset: filters.offset || 0
        }, options);
      },

      /**
       * 获取实体
       * @param {string} workspace - 工作区
       * @param {string} project - 项目
       * @param {string} entityType - 实体类型
       * @param {string} name - 实体名称
       */
      async get(workspace, project, entityType, name, options = {}) {
        return apiClient.call('state.entity.get', {
          workspace,
          project,
          entity_type: entityType,
          name
        }, options);
      },

      /**
       * 创建/更新实体
       * @param {string} workspace - 工作区
       * @param {string} project - 项目
       * @param {Object} data - 数据
       */
      async upsert(workspace, project, data, options = {}) {
        return apiClient.call('state.entity.upsert', {
          workspace,
          project,
          ...data
        }, { ...options, showLoading: true });
      }
    },

    // ==================== Workspace/Project API ====================

    workspace: {
      /**
       * 列出工作区
       */
      async list(options = {}) {
        return apiClient.call('workspace.list', {}, options);
      }
    },

    project: {
      /**
       * 列出项目
       * @param {string} workspace - 工作区
       */
      async list(workspace, options = {}) {
        return apiClient.call('project.list', { workspace }, options);
      }
    }
  };

  // 暴露到全局
  window.apiClient = apiClient;

})();
