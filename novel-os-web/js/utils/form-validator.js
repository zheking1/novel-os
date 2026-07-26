/**
 * Novel OS - Form Validator
 * 表单验证工具函数库
 * @version 1.0.0
 */
(function() {
  'use strict';

  if (window.FormValidator) {
    return;
  }

  window.FormValidator = {
    /**
     * 验证规则配置
     */
    rules: {
      required: {
        message: '此字段为必填项',
        validate: (value) => {
          if (value === null || value === undefined) return false;
          if (typeof value === 'string') return value.trim().length > 0;
          if (Array.isArray(value)) return value.length > 0;
          return true;
        }
      },
      
      email: {
        message: '请输入有效的邮箱地址',
        validate: (value) => {
          if (!value) return true; // 可选字段
          return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
        }
      },
      
      slug: {
        message: '只能包含小写字母、数字和横线',
        validate: (value) => {
          if (!value) return true;
          return /^[a-z0-9][a-z0-9\-]*$/.test(value);
        }
      },
      
      alphanumeric: {
        message: '只能包含字母和数字',
        validate: (value) => {
          if (!value) return true;
          return /^[a-zA-Z0-9]+$/.test(value);
        }
      },
      
      minLength: {
        message: (min) => `最少需要 ${min} 个字符`,
        validate: (value, min) => {
          if (!value) return true;
          return String(value).length >= min;
        }
      },
      
      maxLength: {
        message: (max) => `最多允许 ${max} 个字符`,
        validate: (value, max) => {
          if (!value) return true;
          return String(value).length <= max;
        }
      },
      
      number: {
        message: '请输入有效的数字',
        validate: (value) => {
          if (!value && value !== 0) return true;
          return !isNaN(Number(value));
        }
      },
      
      range: {
        message: (min, max) => `数值必须在 ${min} 到 ${max} 之间`,
        validate: (value, min, max) => {
          if (!value && value !== 0) return true;
          const num = Number(value);
          return !isNaN(num) && num >= min && num <= max;
        }
      },
      
      json: {
        message: '请输入有效的 JSON 格式',
        validate: (value) => {
          if (!value) return true;
          try {
            JSON.parse(value);
            return true;
          } catch {
            return false;
          }
        }
      },
      
      url: {
        message: '请输入有效的 URL',
        validate: (value) => {
          if (!value) return true;
          try {
            new URL(value);
            return true;
          } catch {
            return false;
          }
        }
      }
    },

    /**
     * 验证单个字段
     * @param {string} value - 字段值
     * @param {Array} validations - 验证规则数组 [{ rule: 'required', message: '自定义消息' }, { rule: 'minLength', params: [3] }]
     * @returns {Object} { valid: boolean, error: string|null }
     */
    validateField(value, validations) {
      for (const validation of validations) {
        const ruleName = validation.rule;
        const rule = this.rules[ruleName];
        
        if (!rule) {
          console.warn(`[FormValidator] Unknown rule: ${ruleName}`);
          continue;
        }
        
        const params = validation.params || [];
        const isValid = rule.validate(value, ...params);
        
        if (!isValid) {
          let message = validation.message || rule.message;
          if (typeof message === 'function') {
            message = message(...params);
          }
          return { valid: false, error: message };
        }
      }
      
      return { valid: true, error: null };
    },

    /**
     * 验证整个表单
     * @param {Object} fields - 字段配置对象 { fieldName: { value: '', validations: [] } }
     * @returns {Object} { valid: boolean, errors: { fieldName: errorMessage } }
     */
    validateForm(fields) {
      const errors = {};
      let isValid = true;
      
      for (const [fieldName, config] of Object.entries(fields)) {
        const result = this.validateField(config.value, config.validations);
        if (!result.valid) {
          errors[fieldName] = result.error;
          isValid = false;
        }
      }
      
      return { valid: isValid, errors };
    },

    /**
     * 显示字段错误
     * @param {string} fieldId - 字段 ID
     * @param {string} error - 错误消息
     */
    showFieldError(fieldId, error) {
      const field = document.getElementById(fieldId);
      if (!field) return;
      
      // 添加错误样式
      field.classList.add('border-red-500', 'focus:ring-red-500');
      field.classList.remove('border-gray-300', 'focus:ring-primary-500');
      
      // 查找或创建错误提示元素
      let errorEl = document.getElementById(`${fieldId}-error`);
      if (!errorEl) {
        errorEl = document.createElement('p');
        errorEl.id = `${fieldId}-error`;
        errorEl.className = 'text-red-500 text-xs mt-1';
        field.parentNode.appendChild(errorEl);
      }
      errorEl.textContent = error;
    },

    /**
     * 清除字段错误
     * @param {string} fieldId - 字段 ID
     */
    clearFieldError(fieldId) {
      const field = document.getElementById(fieldId);
      if (!field) return;
      
      // 移除错误样式
      field.classList.remove('border-red-500', 'focus:ring-red-500');
      field.classList.add('border-gray-300', 'focus:ring-primary-500');
      
      // 移除错误提示
      const errorEl = document.getElementById(`${fieldId}-error`);
      if (errorEl) {
        errorEl.remove();
      }
    },

    /**
     * 清除所有字段错误
     * @param {Array} fieldIds - 字段 ID 数组
     */
    clearAllErrors(fieldIds) {
      fieldIds.forEach(id => this.clearFieldError(id));
    },

    /**
     * 快速验证并显示错误
     * @param {Object} fields - 字段配置
     * @returns {boolean} 是否全部通过
     */
    validateAndShowErrors(fields) {
      const result = this.validateForm(fields);
      
      // 清除所有旧错误
      this.clearAllErrors(Object.keys(fields));
      
      // 显示新错误
      if (!result.valid) {
        for (const [fieldName, error] of Object.entries(result.errors)) {
          this.showFieldError(fieldName, error);
        }
      }
      
      return result.valid;
    },

    /**
     * 常用验证配置
     */
    presets: {
      required: [{ rule: 'required' }],
      requiredSlug: [
        { rule: 'required' },
        { rule: 'slug' }
      ],
      requiredEmail: [
        { rule: 'required' },
        { rule: 'email' }
      ],
      optionalEmail: [{ rule: 'email' }],
      requiredJson: [
        { rule: 'required' },
        { rule: 'json' }
      ],
      optionalJson: [{ rule: 'json' }],
      requiredNumber: [
        { rule: 'required' },
        { rule: 'number' }
      ],
      optionalNumber: [{ rule: 'number' }],
      requiredUrl: [
        { rule: 'required' },
        { rule: 'url' }
      ],
      optionalUrl: [{ rule: 'url' }]
    }
  };

  console.log('[FormValidator] Initialized');
})();
