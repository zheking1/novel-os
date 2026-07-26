/**
 * Style Analysis Page
 * 文风分析 - 分析章节文风指标
 */
(function() {
  window.StyleAnalysisPage = {
    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.styleAnalysis') || '文风分析'}</h1>
          <div class="flex gap-2">
            <button onclick="StyleAnalysisPage.showAnalyzeModal()" class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 text-sm">🔍 分析章节</button>
            <button onclick="StyleAnalysisPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="style-analysis-content">
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">点击"分析章节"开始文风分析</div>
        </div>
      `;
      return true;
    },

    async loadData() {
      // Load recent analyzed chapters
      const container = document.getElementById('style-analysis-content');
      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">使用"分析章节"功能来分析具体章节</div>';
    },

    showAnalyzeModal() {
      ModalDialog.show({
        title: '分析章节文风',
        content: `
          <div class="space-y-4">
            <div>
              <label class="block text-sm font-medium mb-1">章节号 <span class="text-red-500">*</span></label>
              <input type="number" id="analyze-chapter" class="w-full border rounded px-3 py-2" placeholder="例如: 15" />
            </div>
          </div>`,
        onConfirm: async () => {
          const chapterNo = parseInt(document.getElementById('analyze-chapter').value);
          if (!chapterNo) { alert('请输入章节号'); return; }
          
          try {
            const projectId = window.AppState.currentProjectId || window.AppState.currentProject || '';
            ModalDialog.close();
            await StyleAnalysisPage.analyzeChapter(chapterNo);
          } catch (e) { alert('分析失败: ' + e.message); }
        }
      });
    },

    async analyzeChapter(chapterNo) {
      const container = document.getElementById('style-analysis-content');
      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">分析中...</div>';

      try {
        
        // Get chapter content first
        const chapterResult = await window.ApiClient.callTool('local.chapter.read', {
          workspace: window.AppState.currentWorkspace,
          project: window.AppState.currentProject,
          chapter_no: chapterNo
        }).catch(() => null);

        if (!chapterResult || !chapterResult.content) {
          container.innerHTML = `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">无法读取章节 ${chapterNo} 内容</div>`;
          return;
        }

        // Analyze style
        const result = await window.ApiClient.callTool('style.analyze_chapter', {
          workspace: window.AppState.currentWorkspace,
          project: window.AppState.currentProject,
          chapter_no: chapterNo,
          content: chapterResult.content
        });

        this.renderAnalysis(result, chapterNo);
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">分析失败: ${e.message}</div>`;
      }
    },

    renderAnalysis(analysis, chapterNo) {
      const container = document.getElementById('style-analysis-content');
      const metrics = analysis?.metrics || analysis || {};

      container.innerHTML = `
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <!-- 基础指标 -->
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">📊 第${chapterNo}章 文风指标</h3>
            <div class="grid grid-cols-2 gap-4">
              ${metrics.avg_sentence_length !== undefined ? `
                <div class="bg-gray-50 p-3 rounded">
                  <div class="text-xs text-gray-500">平均句长</div>
                  <div class="text-lg font-semibold">${metrics.avg_sentence_length.toFixed(1)} 字</div>
                </div>
              ` : ''}
              ${metrics.vocabulary_diversity !== undefined ? `
                <div class="bg-gray-50 p-3 rounded">
                  <div class="text-xs text-gray-500">词汇多样性</div>
                  <div class="text-lg font-semibold">${(metrics.vocabulary_diversity * 100).toFixed(1)}%</div>
                </div>
              ` : ''}
              ${metrics.dialogue_ratio !== undefined ? `
                <div class="bg-gray-50 p-3 rounded">
                  <div class="text-xs text-gray-500">对话比例</div>
                  <div class="text-lg font-semibold">${(metrics.dialogue_ratio * 100).toFixed(1)}%</div>
                </div>
              ` : ''}
              ${metrics.paragraph_count !== undefined ? `
                <div class="bg-gray-50 p-3 rounded">
                  <div class="text-xs text-gray-500">段落数</div>
                  <div class="text-lg font-semibold">${metrics.paragraph_count}</div>
                </div>
              ` : ''}
            </div>
          </div>

          <!-- 修辞手法 -->
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">✨ 修辞手法</h3>
            ${metrics.rhetorical_devices && Object.keys(metrics.rhetorical_devices).length > 0 ? `
              <div class="space-y-2">
                ${Object.entries(metrics.rhetorical_devices).map(([device, count]) => `
                  <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span class="text-sm">${this.getDeviceLabel(device)}</span>
                    <span class="font-medium">${count} 次</span>
                  </div>
                `).join('')}
              </div>
            ` : '<p class="text-gray-500">未检测到明显的修辞手法</p>'}
          </div>

          <!-- 句式分布 -->
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">📝 句式分布</h3>
            ${metrics.sentence_types && Object.keys(metrics.sentence_types).length > 0 ? `
              <div class="space-y-2">
                ${Object.entries(metrics.sentence_types).map(([type, count]) => `
                  <div class="flex items-center justify-between p-2 bg-gray-50 rounded">
                    <span class="text-sm">${this.getSentenceTypeLabel(type)}</span>
                    <div class="flex items-center gap-2">
                      <div class="w-24 bg-gray-200 rounded-full h-2">
                        <div class="bg-primary-600 h-2 rounded-full" style="width: ${Math.min(100, (count / (metrics.total_sentences || 1)) * 100)}%"></div>
                      </div>
                      <span class="text-sm font-medium">${count}</span>
                    </div>
                  </div>
                `).join('')}
              </div>
            ` : '<p class="text-gray-500">暂无句式分布数据</p>'}
          </div>

          <!-- 风格特征 -->
          <div class="bg-white rounded-lg shadow p-6">
            <h3 class="text-lg font-semibold mb-4">🎨 风格特征</h3>
            <div class="space-y-3">
              ${metrics.formality !== undefined ? `
                <div>
                  <div class="flex justify-between text-sm mb-1">
                    <span>正式程度</span>
                    <span>${(metrics.formality * 100).toFixed(0)}%</span>
                  </div>
                  <div class="bg-gray-200 rounded-full h-2">
                    <div class="bg-blue-600 h-2 rounded-full" style="width: ${metrics.formality * 100}%"></div>
                  </div>
                </div>
              ` : ''}
              ${metrics.descriptive_density !== undefined ? `
                <div>
                  <div class="flex justify-between text-sm mb-1">
                    <span>描写密度</span>
                    <span>${(metrics.descriptive_density * 100).toFixed(0)}%</span>
                  </div>
                  <div class="bg-gray-200 rounded-full h-2">
                    <div class="bg-green-600 h-2 rounded-full" style="width: ${metrics.descriptive_density * 100}%"></div>
                  </div>
                </div>
              ` : ''}
            </div>
          </div>
        </div>
      `;
    },

    getDeviceLabel(device) {
      const labels = {
        'metaphor': '隐喻',
        'simile': '明喻',
        'personification': '拟人',
        'exaggeration': '夸张',
        'rhetorical_question': '反问',
        'parallelism': '排比',
        'contrast': '对比'
      };
      return labels[device] || device;
    },

    getSentenceTypeLabel(type) {
      const labels = {
        'short': '短句',
        'medium': '中句',
        'long': '长句',
        'complex': '复合句',
        'simple': '简单句'
      };
      return labels[type] || type;
    },

    loadData() {
      this.loadData();
    }
  };
})();
