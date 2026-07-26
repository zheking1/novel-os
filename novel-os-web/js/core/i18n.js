/**
 * Novel OS - i18n Module
 * Internationalization support with dynamic language loading
 * @version 1.0.0
 */

(function() {
  'use strict';

  /**
   * i18n管理器
   */
  const i18n = {
    // 当前语言
    currentLang: 'zh',

    // 语言数据缓存
    messages: {},

    // 可用语言
    availableLangs: ['zh', 'en'],

    /**
     * 加载语言包
     * @param {string} lang - 语言代码
     */
    async loadLang(lang) {
      if (this.messages[lang]) {
        return this.messages[lang];
      }

      try {
        const response = await fetch(`i18n/${lang}.json`);
        if (!response.ok) {
          throw new Error(`Failed to load ${lang}.json`);
        }
        const data = await response.json();
        this.messages[lang] = data;
        return data;
      } catch (error) {
        console.error(`Failed to load language ${lang}:`, error);
        // 如果加载失败，使用内置的备用翻译
        return this.getFallbackMessages(lang);
      }
    },

    /**
     * 获取备用翻译（内置）
     * @param {string} lang - 语言代码
     */
    getFallbackMessages(lang) {
      const fallbacks = {
        zh: {
          app: { name: 'Novel OS' },
          nav: {
            worldbuilding: '世界设定',
            knowledge: '知识管理',
            story: '故事设定',
            system: '系统管理'
          },
          common: {
            save: '保存',
            cancel: '取消',
            delete: '删除',
            edit: '编辑',
            new: '新建',
            loading: '加载中...',
            success: '操作成功',
            error: '操作失败'
          }
        },
        en: {
          app: { name: 'Novel OS' },
          nav: {
            worldbuilding: 'Worldbuilding',
            knowledge: 'Knowledge',
            story: 'Story',
            system: 'System'
          },
          common: {
            save: 'Save',
            cancel: 'Cancel',
            delete: 'Delete',
            edit: 'Edit',
            new: 'New',
            loading: 'Loading...',
            success: 'Success',
            error: 'Error'
          }
        }
      };
      return fallbacks[lang] || fallbacks.zh;
    },

    /**
     * 切换语言
     * @param {string} lang - 语言代码
     */
    async setLang(lang) {
      if (!this.availableLangs.includes(lang)) {
        console.warn(`Language ${lang} not available`);
        return false;
      }

      await this.loadLang(lang);
      this.currentLang = lang;

      // 更新Alpine store
      if (window.Alpine && Alpine.store('app')) {
        Alpine.store('app').currentLang = lang;
      }

      // 触发语言变更事件
      window.dispatchEvent(new CustomEvent('i18n:changed', {
        detail: { lang }
      }));

      return true;
    },

    /**
     * 翻译函数
     * @param {string} key - 翻译键（支持点号路径，如 'level.item.title'）
     * @param {Object} params - 插值参数
     * @returns {string}
     */
    t(key, params = {}) {
      if (!key) return '';
      const messages = this.messages[this.currentLang] || {};

      // 解析路径
      const keys = key.split('.');
      let value = messages;

      for (const k of keys) {
        if (value && typeof value === 'object') {
          value = value[k];
        } else {
          value = undefined;
          break;
        }
      }

      // 如果没有找到，返回键名
      if (value === undefined || value === null) {
        return key;
      }

      // 替换插值参数
      if (typeof value === 'string' && Object.keys(params).length > 0) {
        return value.replace(/\{(\w+)\}/g, (match, paramKey) => {
          return params[paramKey] !== undefined ? params[paramKey] : match;
        });
      }

      return value;
    },

    /**
     * 批量翻译
     * @param {Array<string>} keys - 键数组
     * @returns {Object}
     */
    translateBatch(keys) {
      const result = {};
      keys.forEach(key => {
        result[key] = this.t(key);
      });
      return result;
    },

    /**
     * 获取当前语言
     */
    getCurrentLang() {
      return this.currentLang;
    },

    /**
     * 获取可用语言列表
     */
    getAvailableLangs() {
      return this.availableLangs.map(lang => ({
        code: lang,
        name: lang === 'zh' ? '中文' : 'English'
      }));
    },

    /**
     * 初始化
     * @param {string} defaultLang - 默认语言
     */
    async init(defaultLang = 'zh') {
      // 尝试从localStorage读取用户偏好
      const savedLang = localStorage.getItem('novel-os-lang');
      const lang = savedLang || defaultLang;

      await this.setLang(lang);

      // 监听语言变更，保存到localStorage
      window.addEventListener('i18n:changed', (e) => {
        localStorage.setItem('novel-os-lang', e.detail.lang);
      });

      return true;
    }
  };

  // 暴露到全局
  window.i18n = i18n;
  window.t = (key, params) => i18n.t(key, params);

  // Alpine初始化时加载默认语言（只执行一次）
  let i18nInitialized = false;
  document.addEventListener('alpine:init', () => {
    if (i18nInitialized) return;
    i18nInitialized = true;
    i18n.init('zh');
  });

})();
