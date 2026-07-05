/**
 * Novel OS - Form Builder Component
 * Dynamic form generation with validation
 * @version 1.0.0
 */

(function() {
  'use strict';

  document.addEventListener('alpine:init', () => {

    /**
     * FormBuilder组件
     * @param {Object} config - 配置
     */
    Alpine.data('formBuilder', (config = {}) => ({
      // 表单数据
      model: config.initialData || {},
      originalModel: null, // 用于检测变更

      // 字段配置
      fields: config.fields || [],

      // 状态
      submitting: false,
      dirty: false,
      touched: {},
      errors: {},

      // 回调
      onSubmit: config.onSubmit || null,
      onChange: config.onChange || null,
      onValidate: config.onValidate || null,

      /**
       * 初始化
       */
      init() {
        // 保存原始数据用于比较
        this.originalModel = JSON.parse(JSON.stringify(this.model));

        // 初始化touched状态
        this.fields.forEach(field => {
          this.touched[field.name] = false;
        });

        // 监听变更
        this.$watch('model', () => {
          this.checkDirty();
          this.validate();

          if (typeof this.onChange === 'function') {
            this.onChange(this.model, this.errors);
          }
        }, { deep: true });
      },

      /**
       * 检查是否有变更
       */
      checkDirty() {
        this.dirty = JSON.stringify(this.model) !== JSON.stringify(this.originalModel);
      },

      /**
       * 验证表单
       * @param {boolean} showErrors - 是否显示错误
       */
      validate(showErrors = false) {
        const errors = {};
        let isValid = true;

        this.fields.forEach(field => {
          const value = this.model[field.name];
          const fieldErrors = this.validateField(field, value);

          if (fieldErrors.length > 0) {
            errors[field.name] = fieldErrors;
            isValid = false;
          }
        });

        this.errors = errors;

        // 调用自定义验证
        if (typeof this.onValidate === 'function') {
          const customErrors = this.onValidate(this.model);
          if (customErrors) {
            Object.assign(this.errors, customErrors);
            isValid = false;
          }
        }

        return isValid;
      },

      /**
       * 验证单个字段
       * @param {Object} field - 字段配置
       * @param {*} value - 字段值
       */
      validateField(field, value) {
        const errors = [];

        // 必填验证
        if (field.required) {
          if (value === undefined || value === null || value === '') {
            errors.push(field.requiredMessage || '此项为必填');
          }
        }

        // 类型验证
        if (value !== undefined && value !== null && value !== '') {
          // 最小长度
          if (field.minLength && String(value).length < field.minLength) {
            errors.push(`长度不能少于${field.minLength}个字符`);
          }

          // 最大长度
          if (field.maxLength && String(value).length > field.maxLength) {
            errors.push(`长度不能超过${field.maxLength}个字符`);
          }

          // 最小值
          if (field.min !== undefined && Number(value) < field.min) {
            errors.push(`不能小于${field.min}`);
          }

          // 最大值
          if (field.max !== undefined && Number(value) > field.max) {
            errors.push(`不能大于${field.max}`);
          }

          // 正则匹配
          if (field.pattern && !new RegExp(field.pattern).test(String(value))) {
            errors.push(field.patternMessage || '格式不正确');
          }

          // 自定义验证
          if (typeof field.validator === 'function') {
            const result = field.validator(value, this.model);
            if (result !== true) {
              errors.push(result || '验证失败');
            }
          }
        }

        return errors;
      },

      /**
       * 字段失去焦点
       * @param {string} fieldName - 字段名
       */
      blur(fieldName) {
        this.touched[fieldName] = true;
        this.validate();
      },

      /**
       * 获取字段错误
       * @param {string} fieldName - 字段名
       */
      getFieldErrors(fieldName) {
        if (!this.touched[fieldName]) return [];
        return this.errors[fieldName] || [];
      },

      /**
       * 是否有字段错误
       * @param {string} fieldName - 字段名
       */
      hasFieldError(fieldName) {
        return this.touched[fieldName] && this.errors[fieldName] && this.errors[fieldName].length > 0;
      },

      /**
       * 提交表单
       */
      async submit() {
        // 标记所有字段为touched
        this.fields.forEach(field => {
          this.touched[field.name] = true;
        });

        // 验证
        if (!this.validate(true)) {
          // 聚焦第一个错误字段
          const firstErrorField = this.fields.find(f => this.errors[f.name]);
          if (firstErrorField) {
            const el = document.querySelector(`[name="${firstErrorField.name}"]`);
            if (el) el.focus();
          }
          return false;
        }

        this.submitting = true;

        try {
          if (typeof this.onSubmit === 'function') {
            await this.onSubmit(this.model);
          }

          // 更新原始数据
          this.originalModel = JSON.parse(JSON.stringify(this.model));
          this.dirty = false;

          return true;
        } catch (error) {
          console.error('Form submit error:', error);

          // 处理服务器返回的错误
          if (error.fieldErrors) {
            Object.assign(this.errors, error.fieldErrors);
          }

          return false;
        } finally {
          this.submitting = false;
        }
      },

      /**
       * 重置表单
       * @param {Object} data - 重置数据
       */
      reset(data = null) {
        if (data) {
          this.model = { ...data };
        } else {
          this.model = this.fields.reduce((acc, field) => {
            acc[field.name] = field.default !== undefined ? field.default : '';
            return acc;
          }, {});
        }

        this.originalModel = JSON.parse(JSON.stringify(this.model));
        this.errors = {};
        this.touched = {};
        this.dirty = false;
      },

      /**
       * 设置字段值
       * @param {string} name - 字段名
       * @param {*} value - 值
       */
      setFieldValue(name, value) {
        this.model[name] = value;
      },

      /**
       * 获取字段值
       * @param {string} name - 字段名
       */
      getFieldValue(name) {
        return this.model[name];
      },

      /**
       * 设置错误
       * @param {Object} errors - 错误对象
       */
      setErrors(errors) {
        this.errors = errors;
        // 标记所有有错误的字段为touched
        Object.keys(errors).forEach(fieldName => {
          this.touched[fieldName] = true;
        });
      },

      /**
       * 清除错误
       * @param {string} fieldName - 字段名（可选）
       */
      clearErrors(fieldName = null) {
        if (fieldName) {
          delete this.errors[fieldName];
        } else {
          this.errors = {};
        }
      },

      /**
       * 检查表单是否有效
       */
      isValid() {
        return Object.keys(this.errors).length === 0;
      },

      /**
       * 获取变更的字段
       */
      getChangedFields() {
        const changed = {};
        Object.keys(this.model).forEach(key => {
          if (JSON.stringify(this.model[key]) !== JSON.stringify(this.originalModel[key])) {
            changed[key] = this.model[key];
          }
        });
        return changed;
      }
    }));

    /**
     * 字段类型渲染辅助函数
     */
    window.formFieldTypes = {
      /**
       * 文本输入
       */
      text(field, model, errors) {
        return `
          <input type="text"
                 name="${field.name}"
                 x-model="model.${field.name}"
                 @blur="blur('${field.name}')"
                 class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${errors[field.name] ? 'border-red-500' : 'border-gray-300'}"
                 :placeholder="'${field.placeholder || ''}'"
                 ${field.disabled ? 'disabled' : ''}
                 ${field.readonly ? 'readonly' : ''}>
        `;
      },

      /**
       * 文本域
       */
      textarea(field, model, errors) {
        return `
          <textarea name="${field.name}"
                    x-model="model.${field.name}"
                    @blur="blur('${field.name}')"
                    rows="${field.rows || 3}"
                    class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                           ${errors[field.name] ? 'border-red-500' : 'border-gray-300'}"
                    :placeholder="'${field.placeholder || ''}'"
                    ${field.disabled ? 'disabled' : ''}
                    ${field.readonly ? 'readonly' : ''}></textarea>
        `;
      },

      /**
       * 数字输入
       */
      number(field, model, errors) {
        return `
          <input type="number"
                 name="${field.name}"
                 x-model.number="model.${field.name}"
                 @blur="blur('${field.name}')"
                 class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                        ${errors[field.name] ? 'border-red-500' : 'border-gray-300'}"
                 ${field.min !== undefined ? `min="${field.min}"` : ''}
                 ${field.max !== undefined ? `max="${field.max}"` : ''}
                 ${field.step ? `step="${field.step}"` : ''}
                 ${field.disabled ? 'disabled' : ''}>
        `;
      },

      /**
       * 选择框
       */
      select(field, model, errors) {
        const options = field.options || [];
        const optionsHtml = options.map(opt => {
          const value = typeof opt === 'object' ? opt.value : opt;
          const label = typeof opt === 'object' ? opt.label : opt;
          return `<option value="${value}">${label}</option>`;
        }).join('');

        return `
          <select name="${field.name}"
                  x-model="model.${field.name}"
                  @change="blur('${field.name}')"
                  class="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500
                         ${errors[field.name] ? 'border-red-500' : 'border-gray-300'}"
                  ${field.disabled ? 'disabled' : ''}>
            ${field.placeholder ? `<option value="">${field.placeholder}</option>` : ''}
            ${optionsHtml}
          </select>
        `;
      },

      /**
       * 复选框
       */
      checkbox(field, model, errors) {
        return `
          <input type="checkbox"
                 name="${field.name}"
                 x-model="model.${field.name}"
                 @change="blur('${field.name}')"
                 class="w-4 h-4 text-blue-600 border-gray-300 rounded focus:ring-blue-500"
                 ${field.disabled ? 'disabled' : ''}>
        `;
      },

      /**
       * 单选框组
       */
      radio(field, model, errors) {
        const options = field.options || [];
        return options.map(opt => {
          const value = typeof opt === 'object' ? opt.value : opt;
          const label = typeof opt === 'object' ? opt.label : opt;
          return `
            <label class="inline-flex items-center mr-4">
              <input type="radio"
                     name="${field.name}"
                     value="${value}"
                     x-model="model.${field.name}"
                     @change="blur('${field.name}')"
                     class="w-4 h-4 text-blue-600 border-gray-300 focus:ring-blue-500"
                     ${field.disabled ? 'disabled' : ''}>
              <span class="ml-2">${label}</span>
            </label>
          `;
        }).join('');
      }
    };

  });

})();
