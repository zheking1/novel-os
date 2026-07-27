/**
 * Pacing Analysis Page
 * 节奏分析 - 分析小说节奏、紧张度曲线
 */
(function() {
  window.PacingAnalysisPage = {
    currentVolume: null,

    async init() {
      const contentArea = document.getElementById('content-area');
      contentArea.innerHTML = `
        <div class="flex items-center justify-between mb-6">
          <h1 class="text-2xl font-bold text-gray-800">${window.t('nav.pacingAnalysis') || '节奏分析'}</h1>
          <div class="flex gap-2">
            <select id="volume-selector" class="border rounded px-3 py-2 text-sm" onchange="PacingAnalysisPage.onVolumeChange(this.value)">
              <option value="">选择卷...</option>
            </select>
            <button onclick="PacingAnalysisPage.loadData()" class="px-4 py-2 bg-gray-100 text-gray-700 rounded-lg hover:bg-gray-200 text-sm">🔄 刷新</button>
          </div>
        </div>
        <div id="pacing-content">
          <div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">请先选择卷</div>
        </div>
      `;
      await this.loadVolumes();
      return true;
    },

    async loadVolumes() {
      try {
        const workspace = window.AppState.currentWorkspace || '';
        const project = window.AppState.currentProject || '';
        const result = await window.ApiClient.callTool('volume.list', { workspace, project }).catch(() => []);
        const volumes = Array.isArray(result) ? result : (result?.volumes || result?.result || []);
        const selector = document.getElementById('volume-selector');
        if (selector && volumes.length > 0) {
          selector.innerHTML = '<option value="">选择卷...</option>' +
            volumes.map(v => `<option value="${v.volume_no}">${v.title || '卷' + v.volume_no}</option>`).join('');
        }
      } catch (e) {
        console.error('加载卷失败:', e);
      }
    },

    async onVolumeChange(volumeNo) {
      this.currentVolume = volumeNo ? parseInt(volumeNo) : null;
      if (this.currentVolume) {
        await this.loadPacingData();
      } else {
        document.getElementById('pacing-content').innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">请先选择卷</div>';
      }
    },

    async loadPacingData() {
      const container = document.getElementById('pacing-content');
      if (!this.currentVolume) return;

      container.innerHTML = '<div class="p-8 text-center text-gray-500 bg-white rounded-lg shadow">加载中...</div>';

      try {
        const projectId = window.AppState.currentProjectId || window.AppState.currentProject || '';
        
        // Load pacing data
        const [curve, blueprint] = await Promise.all([
          window.ApiClient.callTool('pacing.get_curve', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, project_id: projectId, volume_no: this.currentVolume }).catch(() => []),
          window.ApiClient.callTool('pacing.get_blueprint', { workspace: window.AppState.currentWorkspace, project: window.AppState.currentProject, project_id: projectId, volume_no: this.currentVolume }).catch(() => null)
        ]);

        const pacingData = curve && curve.data ? curve.data : (curve?.curve || (Array.isArray(curve) ? curve : []));

        container.innerHTML = `
          <div class="grid grid-cols-1 gap-6">
            <!-- 节奏蓝图 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">📋 节奏蓝图</h3>
              ${this.renderBlueprint(blueprint)}
            </div>

            <!-- 紧张度曲线 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">📈 紧张度曲线</h3>
              ${this.renderCurve(pacingData)}
            </div>

            <!-- 章节详情 -->
            <div class="bg-white rounded-lg shadow p-6">
              <h3 class="text-lg font-semibold mb-4">📝 章节节奏详情</h3>
              ${this.renderChapterDetails(pacingData)}
            </div>
          </div>
        `;
      } catch (e) {
        container.innerHTML = `<div class="p-8 text-center text-red-500 bg-white rounded-lg shadow">加载失败: ${e.message}</div>`;
      }
    },

    renderBlueprint(blueprint) {
      if (!blueprint || Object.keys(blueprint).length === 0) {
        return '<p class="text-gray-500">暂无蓝图数据</p>';
      }
      return `
        <div class="space-y-2 text-sm">
          ${blueprint.title ? `
            <div class="flex justify-between py-1 border-b border-gray-100">
              <span class="text-gray-600">标题:</span>
              <span class="font-medium text-gray-800">${blueprint.title}</span>
            </div>
          ` : ''}
          ${blueprint.target_tension ? `
            <div class="flex justify-between py-1 border-b border-gray-100">
              <span class="text-gray-600">目标紧张度:</span>
              <span class="font-medium text-gray-800">${blueprint.target_tension}</span>
            </div>
          ` : ''}
          ${Array.isArray(blueprint.goals) && blueprint.goals.length > 0 ? `
            <div class="py-1">
              <span class="text-gray-600">目标:</span>
              <ul class="mt-1 ml-4 list-disc text-gray-800">
                ${blueprint.goals.map(g => `<li>${g}</li>`).join('')}
              </ul>
            </div>
          ` : ''}
        </div>
      `;
    },

    renderCurve(data) {
      if (!data || data.length === 0) {
        return '<p class="text-gray-500">暂无节奏数据</p>';
      }

      // Simple ASCII chart
      const maxTension = Math.max(...data.map(d => d.tension || 0), 10);
      const chartHeight = 10;
      
      let chart = '<div class="font-mono text-xs bg-gray-50 p-4 rounded overflow-x-auto">';
      chart += '<div class="flex items-end gap-1" style="height: 120px;">';
      
      data.forEach(item => {
        const tension = item.tension || 0;
        const height = Math.round((tension / maxTension) * 100);
        const color = tension > 7 ? 'bg-red-400' : tension > 4 ? 'bg-yellow-400' : 'bg-green-400';
        chart += `
          <div class="flex flex-col items-center" style="min-width: 30px;">
            <div class="${color} w-6 rounded-t" style="height: ${height}px;" title="第${item.chapter_no}章: ${tension}"></div>
            <span class="text-gray-500 mt-1">${item.chapter_no}</span>
          </div>
        `;
      });
      
      chart += '</div></div>';
      
      return chart;
    },

    renderChapterDetails(data) {
      if (!data || data.length === 0) {
        return '<p class="text-gray-500">暂无章节数据</p>';
      }
      
      return `
        <div class="space-y-2 max-h-96 overflow-y-auto">
          ${data.map(item => `
            <div class="flex items-center gap-4 p-3 bg-gray-50 rounded">
              <span class="text-sm font-medium w-16">第${item.chapter_no}章</span>
              <div class="flex-1">
                <div class="flex items-center gap-2 mb-1">
                  <span class="text-xs text-gray-500">紧张度:</span>
                  <div class="flex-1 bg-gray-200 rounded-full h-2 max-w-[100px]">
                    <div class="${item.tension > 7 ? 'bg-red-400' : item.tension > 4 ? 'bg-yellow-400' : 'bg-green-400'} h-2 rounded-full" style="width: ${(item.tension || 0) * 10}%"></div>
                  </div>
                  <span class="text-xs font-medium w-8">${item.tension || 0}</span>
                </div>
                ${item.emotion ? `
                  <div class="text-xs text-gray-600">
                    情绪: ${item.emotion} ${item.emotion_intensity ? `(强度${item.emotion_intensity})` : ''}
                  </div>
                ` : ''}
              </div>
              <span class="text-xs text-gray-400">${item.pacing_type || 'normal'}</span>
            </div>
          `).join('')}
        </div>
      `;
    },

    loadData() {
      if (this.currentVolume) {
        this.loadPacingData();
      }
    }
  };
})();
