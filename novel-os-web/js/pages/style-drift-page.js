/**
 * Style Drift Page
 * 文风漂移检测 - 检测文风是否偏离基准线
 */
(function() {
  window.StyleDriftPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.styleDrift') || '文风漂移检测'}</h1>
          <div class="flex gap-2">
            <button onclick="StyleDriftPage.showDetectModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">🔍 检测漂移</button>
            <button onclick="StyleDriftPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="style-drift-content">
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">点击"检测漂移"开始分析文风漂移情况</div>
        </div>
      `;
      return true;
    },

    async loadData() {
      const container = document.getElementById('style-drift-content');
      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">使用"检测漂移"功能来分析文风漂移</div>';
    },

    showDetectModal() {
      ModalDialog.show({
        title: '检测文风漂移',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">检测章节 <span class="text-red-500">*</span></label>
              <input type="number" id="drift-chapter" class="w-full border rounded px-3 py-2" placeholder="例如: 20" />
              <p class="text-xs text-gray-500 mt-1">将对比该章节与之前章节的文风差异</p>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">对比窗口（章节数）</label>
              <input type="number" id="drift-window" class="w-full border rounded px-3 py-2" value="10" min="3" max="50" />
              <p class="text-xs text-gray-500 mt-1">与之前多少章进行对比</p>
            </div>
            <div>
              <label class="block text-sm font-medium mb-1">漂移阈值</label>
              <input type="number" id="drift-threshold" class="w-full border rounded px-3 py-2" value="0.3" min="0.1" max="1" step="0.1" />
              <p class="text-xs text-gray-500 mt-1">超过此值认为发生漂移 (0.1-1.0)</p>
            </div>
          </div>`,
        onConfirm: async () => {
          const chapterNo = parseInt(document.getElementById('drift-chapter').value);
          const window = parseInt(document.getElementById('drift-window').value) || 10;
          const threshold = parseFloat(document.getElementById('drift-threshold').value) || 0.3;
          
          if (!chapterNo) { alert('请输入章节号'); return; }
          
          try {
            ModalDialog.close();
            await StyleDriftPage.detectDrift(chapterNo, window, threshold);
          } catch (e) { alert('检测失败: ' + e.message); }
        }
      });
    },

    async detectDrift(chapterNo, window, threshold) {
      const container = document.getElementById('style-drift-content');
      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">检测中...</div>';

      try {
        const workspace = window.AppState.currentWorkspace;
        const project = window.AppState.currentProject;
        
        const result = await window.ApiClient.callTool('style.detect_drift', {
          workspace,
          project,
          chapter_no: chapterNo,
          window: 20,
          threshold: threshold
        });

        this.renderDriftResult(result, chapterNo);
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">检测失败: ${e.message}</div>`;
      }
    },

    renderDriftResult(result, chapterNo) {
      const container = document.getElementById('style-drift-content');
      const drift = result?.drift || result || {};
      const hasDrift = drift.has_drift || drift.drift_detected || false;
      const score = drift.drift_score || drift.score || 0;
      const changes = drift.changes || drift.significant_changes || [];

      container.innerHTML = `
        <div class="space-y-6">
          <!-- 总体评估 -->
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">📊 第${chapterNo}章 文风漂移评估</h3>
            <div class="flex items-center gap-4 mb-4">
              <div class="text-4xl">${hasDrift ? '⚠️' : '✅'}</div>
              <div>
                <div class="font-semibold ${hasDrift ? 'text-orange-600' : 'text-green-600'}">
                  ${hasDrift ? '检测到文风漂移' : '文风稳定'}
                </div>
                <div class="text-sm text-gray-500">漂移评分: ${(score * 100).toFixed(1)}%</div>
              </div>
            </div>
            ${drift.summary ? `<p class="text-gray-600">${drift.summary}</p>` : ''}
          </div>

          ${hasDrift && changes.length > 0 ? `
            <!-- 变化详情 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">📈 显著变化指标</h3>
              <div class="space-y-3">
                ${changes.map(change => `
                  <div class="flex items-center justify-between p-3 bg-gray-50 rounded">
                    <span class="font-medium">${this.getMetricLabel(change.metric)}</span>
                    <div class="flex items-center gap-3">
                      <span class="text-sm text-gray-500">${change.previous?.toFixed(2) || '-'}</span>
                      <span class="text-gray-400">→</span>
                      <span class="text-sm font-medium">${change.current?.toFixed(2) || '-'}</span>
                      <span class="px-2 py-0.5 text-xs rounded ${change.change > 0 ? 'bg-red-100 text-red-700' : 'bg-blue-100 text-blue-700'}">
                        ${change.change > 0 ? '+' : ''}${(change.change * 100).toFixed(1)}%
                      </span>
                    </div>
                  </div>
                `).join('')}
              </div>
            </div>
          ` : ''}

          ${drift.suggestions && drift.suggestions.length > 0 ? `
            <!-- 建议 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">💡 改进建议</h3>
              <ul class="space-y-2">
                ${drift.suggestions.map(s => `
                  <li class="flex items-start gap-2">
                    <span class="text-primary-600 mt-1">•</span>
                    <span class="text-gray-700">${s}</span>
                  </li>
                `).join('')}
              </ul>
            </div>
          ` : ''}
        </div>
      `;
    },

    getMetricLabel(metric) {
      const labels = {
        'avg_sentence_length': '平均句长',
        'vocabulary_diversity': '词汇多样性',
        'dialogue_ratio': '对话比例',
        'formality': '正式程度',
        'descriptive_density': '描写密度',
        'paragraph_length': '段落长度',
        'sentence_complexity': '句子复杂度'
      };
      return labels[metric] || metric;
    },

    loadData() {
      this.loadData();
    }
  };
})();
