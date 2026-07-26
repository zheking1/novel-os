/**
 * Novel OS - DOM Utilities
 * Debounce, throttle, and rendering optimizations.
 */
(function() {
  'use strict';
  if (window.DOMUtils) return;

  const DOMUtils = {
    /**
     * Creates a debounced version of a function.
     * The function will be called after `delay` ms of inactivity.
     */
    debounce(fn, delay) {
      let timer;
      return function(...args) {
        clearTimeout(timer);
        timer = setTimeout(() => fn.apply(this, args), delay || 300);
      };
    },

    /**
     * Creates a throttled version of a function.
     * The function will be called at most once per `limit` ms.
     */
    throttle(fn, limit) {
      let inThrottle = false;
      return function(...args) {
        if (!inThrottle) {
          fn.apply(this, args);
          inThrottle = true;
          setTimeout(() => { inThrottle = false; }, limit || 200);
        }
      };
    },

    /**
     * Batch DOM updates using requestAnimationFrame.
     * Returns a function that schedules the update.
     */
    batchUpdate(callback) {
      let scheduled = false;
      return function(...args) {
        if (!scheduled) {
          scheduled = true;
          requestAnimationFrame(() => {
            callback.apply(this, args);
            scheduled = false;
          });
        }
      };
    },

    /**
     * Simple virtual list renderer.
     * Renders only visible items in a scrollable container.
     * @param {Object} options - { container, data, itemHeight, renderItem, overscan }
     */
    createVirtualList(options) {
      const {
        container,
        data,
        itemHeight = 40,
        renderItem,
        overscan = 5
      } = options;

      let scrollTop = 0;
      let visibleHeight = 0;

      const wrapper = document.createElement('div');
      const spacer = document.createElement('div');
      spacer.style.height = (data.length * itemHeight) + 'px';
      spacer.style.position = 'relative';
      wrapper.style.overflow = 'hidden';
      wrapper.style.position = 'relative';

      const itemsContainer = document.createElement('div');
      itemsContainer.style.position = 'absolute';
      itemsContainer.style.top = '0';
      itemsContainer.style.left = '0';
      itemsContainer.style.right = '0';

      wrapper.appendChild(spacer);
      wrapper.appendChild(itemsContainer);
      
      if (typeof container === 'string') {
        container = document.getElementById(container);
      }
      container.innerHTML = '';
      container.appendChild(wrapper);

      function renderVisible() {
        visibleHeight = wrapper.clientHeight || 400;
        const startIdx = Math.max(0, Math.floor(scrollTop / itemHeight) - overscan);
        const endIdx = Math.min(data.length, Math.ceil((scrollTop + visibleHeight) / itemHeight) + overscan);

        itemsContainer.style.transform = `translateY(${startIdx * itemHeight}px)`;
        itemsContainer.innerHTML = '';

        const fragment = document.createDocumentFragment();
        for (let i = startIdx; i < endIdx; i++) {
          const el = renderItem(data[i], i);
          el.style.height = itemHeight + 'px';
          fragment.appendChild(el);
        }
        itemsContainer.appendChild(fragment);
      }

      wrapper.addEventListener('scroll', () => {
        scrollTop = wrapper.scrollTop;
        requestAnimationFrame(renderVisible);
      });

      // Initial render
      requestAnimationFrame(renderVisible);

      return {
        updateData(newData) {
          data = newData;
          spacer.style.height = (data.length * itemHeight) + 'px';
          renderVisible();
        },
        refresh() {
          renderVisible();
        }
      };
    },

    /** Show tooltip-like notification that auto-fades */
    toast(message, type) {
      type = type || 'info';
      const colors = { info: 'bg-blue-600', success: 'bg-green-600', error: 'bg-red-600', warn: 'bg-orange-500' };
      const toast = document.createElement('div');
      toast.className = `${colors[type] || colors.info} text-white px-4 py-2 rounded-lg shadow-lg text-sm fixed top-4 right-4 z-50 transition-opacity`;
      toast.textContent = message;
      document.body.appendChild(toast);
      setTimeout(() => {
        toast.style.opacity = '0';
        setTimeout(() => toast.remove(), 300);
      }, 2500);
    }
  };

  window.DOMUtils = DOMUtils;
})();