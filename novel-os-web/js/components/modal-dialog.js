/**
 * Novel OS - Modal Dialog Component
 * 通用模态框组件，支持确认、表单、自定义内容
 * @version 1.0.0
 */

(function() {
  'use strict';

  if (window.ModalDialog) {
    return;
  }

  const ModalDialog = {
    // 当前打开的模态框
    currentModal: null,

    /**
     * 显示模态框
     * @param {Object} config - 模态框配置
     */
    show(config) {
      const {
        id = 'modal-' + Date.now(),
        title = '',
        content = '',
        size = 'md', // sm, md, lg, xl
        showClose = true,
        showFooter = true,
        confirmText = null,
        cancelText = null,
        onConfirm = null,
        onCancel = null,
        onClose = null
      } = config;

      // 关闭已有模态框
      if (this.currentModal) {
        this.close();
      }

      const sizeClass = {
        sm: 'max-w-md',
        md: 'max-w-lg',
        lg: 'max-w-2xl',
        xl: 'max-w-4xl'
      }[size] || 'max-w-lg';

      const modalHtml = `
        <div id="${id}" class="fixed inset-0 z-50 flex items-center justify-center p-4" aria-modal="true">
          <!-- 背景遮罩 -->
          <div class="fixed inset-0 transition-opacity bg-gray-500 bg-opacity-75" onclick="ModalDialog.close()"></div>
          
          <!-- 模态框内容 -->
          <div class="${sizeClass} w-full relative z-10 transform overflow-hidden rounded-2xl bg-white text-left align-top shadow-xl transition-all">
              <!-- 头部 -->
              <div class="flex items-center justify-between px-6 py-4 border-b border-gray-200">
                <h3 class="text-lg font-semibold text-gray-900">${title}</h3>
                ${showClose ? `
                  <button onclick="ModalDialog.close()" class="text-gray-400 hover:text-gray-500">
                    <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12"/>
                    </svg>
                  </button>
                ` : ''}
              </div>
              
              <!-- 内容 -->
              <div class="px-6 py-4" id="${id}-content">
                ${content}
              </div>
              
              <!-- 底部 -->
              ${showFooter ? `
                <div class="flex justify-end gap-3 px-6 py-4 border-t border-gray-200 bg-gray-50">
                  <button onclick="ModalDialog.close()" 
                          class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-md hover:bg-gray-50 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                    ${cancelText || t('common.cancel')}
                  </button>
                  ${onConfirm ? `
                    <button id="${id}-confirm-btn"
                            class="px-4 py-2 text-sm font-medium text-white bg-primary-600 border border-transparent rounded-md hover:bg-primary-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-primary-500">
                      ${confirmText || t('common.confirm')}
                    </button>
                  ` : ''}
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      `;

      document.body.insertAdjacentHTML('beforeend', modalHtml);
      this.currentModal = document.getElementById(id);

      // 绑定确认按钮事件
      if (onConfirm) {
        const confirmBtn = document.getElementById(`${id}-confirm-btn`);
        if (confirmBtn) {
          confirmBtn.addEventListener('click', async () => {
            await onConfirm(id);
          });
        }
      }

      // 绑定取消按钮事件
      if (onCancel) {
        const cancelBtn = this.currentModal.querySelector('.bg-white.border');
        if (cancelBtn) {
          cancelBtn.addEventListener('click', () => {
            onCancel(id);
          });
        }
      }

      // ESC键关闭
      const escHandler = (e) => {
        if (e.key === 'Escape') {
          this.close();
          document.removeEventListener('keydown', escHandler);
        }
      };
      document.addEventListener('keydown', escHandler);

      return id;
    },

    /**
     * 关闭模态框
     */
    close() {
      if (this.currentModal) {
        this.currentModal.remove();
        this.currentModal = null;
      }
    },

    /**
     * 显示确认对话框
     * @param {string} message - 提示信息
     * @param {Function} onConfirm - 确认回调
     */
    confirm(message, onConfirm) {
      return this.show({
        title: t('common.confirm'),
        content: `<p class="text-gray-600">${message}</p>`,
        size: 'sm',
        confirmText: t('common.confirm'),
        cancelText: t('common.cancel'),
        onConfirm: async (id) => {
          await onConfirm();
          this.close();
        }
      });
    },

    /**
     * 显示提示信息
     * @param {string} message - 提示信息
     * @param {string} type - 类型: info, success, warning, error
     */
    alert(message, type = 'info') {
      const icons = {
        info: '💡',
        success: '✅',
        warning: '⚠️',
        error: '❌'
      };

      return this.show({
        title: icons[type] + ' ' + t('common.info'),
        content: `<p class="text-gray-600">${message}</p>`,
        size: 'sm',
        showFooter: true,
        onConfirm: () => this.close()
      });
    },

    /**
     * 获取模态框内容容器
     * @param {string} modalId - 模态框ID
     */
    getContentContainer(modalId) {
      return document.getElementById(`${modalId}-content`);
    }
  };

  window.ModalDialog = ModalDialog;

})();
