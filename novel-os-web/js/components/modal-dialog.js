/**
 * Novel OS - Modal Dialog Component
 * Reusable modal dialog with various configurations
 * @version 1.0.0
 */

(function() {
  'use strict';

  document.addEventListener('alpine:init', () => {

    /**
     * Modal组件
     * @param {Object} config - 配置
     */
    Alpine.data('modalDialog', (config = {}) => ({
      // 状态
      isOpen: false,
      isClosing: false,

      // 配置
      title: config.title || '',
      size: config.size || 'md', // 'sm', 'md', 'lg', 'xl', 'full'
      closable: config.closable !== false,
      backdrop: config.backdrop !== false,
      keyboard: config.keyboard !== false,

      // 内容
      content: config.content || null,
      component: config.component || null,
      componentData: config.componentData || null,

      // 按钮
      showConfirm: config.showConfirm !== false,
      showCancel: config.showCancel !== false,
      confirmText: config.confirmText || '确认',
      cancelText: config.cancelText || '取消',
      confirmDisabled: false,

      // 回调
      onOpen: config.onOpen || null,
      onClose: config.onClose || null,
      onConfirm: config.onConfirm || null,
      onCancel: config.onCancel || null,

      /**
       * 初始化
       */
      init() {
        // 监听ESC键
        if (this.keyboard) {
          document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.isOpen) {
              this.close();
            }
          });
        }
      },

      /**
       * 打开模态框
       * @param {Object} options - 打开选项
       */
      open(options = {}) {
        // 合并选项
        if (options.title) this.title = options.title;
        if (options.size) this.size = options.size;
        if (options.content) this.content = options.content;
        if (options.component) this.component = options.component;
        if (options.componentData) this.componentData = options.componentData;
        if (options.confirmText) this.confirmText = options.confirmText;
        if (options.cancelText) this.cancelText = options.cancelText;

        // 设置回调
        if (options.onConfirm) this.onConfirm = options.onConfirm;
        if (options.onCancel) this.onCancel = options.onCancel;
        if (options.onClose) this.onClose = options.onClose;

        this.isOpen = true;
        this.isClosing = false;

        // 防止背景滚动
        document.body.style.overflow = 'hidden';

        // 触发打开回调
        if (typeof this.onOpen === 'function') {
          this.onOpen();
        }

        // 触发全局事件
        window.dispatchEvent(new CustomEvent('modal:opened', {
          detail: { modal: this }
        }));
      },

      /**
       * 关闭模态框
       * @param {Object} result - 关闭结果
       */
      close(result = null) {
        if (!this.closable && result !== 'force') return;

        this.isClosing = true;

        // 动画结束后完全关闭
        setTimeout(() => {
          this.isOpen = false;
          this.isClosing = false;

          // 恢复背景滚动
          document.body.style.overflow = '';

          // 触发关闭回调
          if (typeof this.onClose === 'function') {
            this.onClose(result);
          }

          // 触发全局事件
          window.dispatchEvent(new CustomEvent('modal:closed', {
            detail: { modal: this, result }
          }));
        }, 200);
      },

      /**
       * 确认
       */
      async confirm() {
        if (this.confirmDisabled) return;

        this.confirmDisabled = true;

        try {
          let shouldClose = true;

          if (typeof this.onConfirm === 'function') {
            const result = await this.onConfirm();
            if (result === false) {
              shouldClose = false;
            }
          }

          if (shouldClose) {
            this.close('confirmed');
          }
        } catch (error) {
          console.error('Modal confirm error:', error);
        } finally {
          this.confirmDisabled = false;
        }
      },

      /**
       * 取消
       */
      cancel() {
        if (typeof this.onCancel === 'function') {
          this.onCancel();
        }
        this.close('cancelled');
      },

      /**
       * 点击背景
       * @param {Event} event - 点击事件
       */
      backdropClick(event) {
        if (this.backdrop && event.target === event.currentTarget) {
          this.close('backdrop');
        }
      },

      /**
       * 获取尺寸类名
       */
      getSizeClass() {
        const sizeMap = {
          'sm': 'max-w-sm',
          'md': 'max-w-md',
          'lg': 'max-w-lg',
          'xl': 'max-w-xl',
          '2xl': 'max-w-2xl',
          '3xl': 'max-w-3xl',
          '4xl': 'max-w-4xl',
          '5xl': 'max-w-5xl',
          'full': 'max-w-full mx-4'
        };
        return sizeMap[this.size] || sizeMap['md'];
      },

      /**
       * 设置内容
       * @param {string} content - HTML内容
       */
      setContent(content) {
        this.content = content;
      },

      /**
       * 设置标题
       * @param {string} title - 标题
       */
      setTitle(title) {
        this.title = title;
      },

      /**
       * 禁用确认按钮
       * @param {boolean} disabled - 是否禁用
       */
      setConfirmDisabled(disabled) {
        this.confirmDisabled = disabled;
      }
    }));

    /**
     * 全局Modal管理器
     */
    Alpine.data('modalManager', () => ({
      modals: [],
      activeModal: null,

      /**
       * 创建并打开模态框
       * @param {Object} config - 配置
       */
      create(config) {
        const modal = {
          id: Date.now(),
          ...config,
          isOpen: true
        };

        this.modals.push(modal);
        this.activeModal = modal;

        return modal;
      },

      /**
       * 关闭指定模态框
       * @param {number} id - 模态框ID
       */
      close(id) {
        const index = this.modals.findIndex(m => m.id === id);
        if (index > -1) {
          this.modals.splice(index, 1);
          this.activeModal = this.modals[this.modals.length - 1] || null;
        }
      },

      /**
       * 关闭所有模态框
       */
      closeAll() {
        this.modals = [];
        this.activeModal = null;
      }
    }));

  });

  /**
   * 便捷函数：显示确认对话框
   * @param {Object} options - 选项
   */
  window.confirmDialog = function(options = {}) {
    const {
      title = '确认',
      message = '确定要执行此操作吗？',
      confirmText = '确认',
      cancelText = '取消',
      type = 'warning' // 'warning', 'danger', 'info'
    } = options;

    return new Promise((resolve) => {
      const modal = document.createElement('div');
      modal.innerHTML = `
        <div x-data="modalDialog({
          title: '${title}',
          size: 'sm',
          closable: false,
          onConfirm: () => resolve(true),
          onCancel: () => resolve(false)
        })" x-init="open()">
          <template x-if="isOpen">
            <div class="fixed inset-0 bg-black/50 z-50 flex items-center justify-center"
                 @click="backdropClick($event)">
              <div class="bg-white rounded-lg shadow-xl w-full max-w-sm p-6"
                   :class="{ 'opacity-0 scale-95': isClosing, 'opacity-100 scale-100': !isClosing }"
                   style="transition: all 0.2s ease-out">
                <div class="flex items-start gap-4">
                  <div class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center
                              ${type === 'danger' ? 'bg-red-100 text-red-600' : type === 'warning' ? 'bg-yellow-100 text-yellow-600' : 'bg-blue-100 text-blue-600'}">
                    ${type === 'danger' ? '⚠️' : type === 'warning' ? '⚡' : 'ℹ️'}
                  </div>
                  <div class="flex-1">
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">${title}</h3>
                    <p class="text-gray-600">${message}</p>
                  </div>
                </div>
                <div class="flex justify-end gap-3 mt-6">
                  <button @click="cancel()" class="px-4 py-2 text-gray-700 hover:bg-gray-100 rounded-lg transition-colors">
                    ${cancelText}
                  </button>
                  <button @click="confirm()" class="px-4 py-2 text-white rounded-lg transition-colors
                             ${type === 'danger' ? 'bg-red-600 hover:bg-red-700' : type === 'warning' ? 'bg-yellow-600 hover:bg-yellow-700' : 'bg-blue-600 hover:bg-blue-700'}">
                    ${confirmText}
                  </button>
                </div>
              </div>
            </div>
          </template>
        </div>
      `;

      document.body.appendChild(modal);

      // Alpine会自动处理
      setTimeout(() => {
        Alpine.initTree(modal);
      }, 0);
    });
  };

})();
