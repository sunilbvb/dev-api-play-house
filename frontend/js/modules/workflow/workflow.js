import { apiClient } from '../api_client.js';

export class WorkflowManager {
  constructor(app) {
    this.app = app;
    this.analysisData = null;
    this.stepsContainer = document.getElementById('quest-steps-container');
    this.logOutput = document.getElementById('workflow-log-output');
    this.runStatus = document.getElementById('workflow-run-status');
    this.btnAnalyze = document.getElementById('btn-analyze-dag');
    this.btnRun = document.getElementById('btn-run-workflow');

    this.initEvents();
  }

  initEvents() {
    this.btnAnalyze.addEventListener('click', () => this.analyzeCurrentWorkflow());
    this.btnRun.addEventListener('click', () => this.runCurrentWorkflow());
  }

  async analyzeCurrentWorkflow() {
    const colId = this.app.explorer.activeCollectionId;
    if (!colId) {
      return this.app.showToast('Please select a collection first', 'error');
    }

    try {
      this.analysisData = await apiClient.analyzeWorkflow(colId);
      this.renderQuestMap();
      this.app.showToast('Workflow DAG analyzed', 'success');
    } catch (err) {
      this.app.showToast(`Analysis failed: ${err.message}`, 'error');
    }
  }

  renderQuestMap() {
    this.stepsContainer.innerHTML = '';
    if (!this.analysisData || !this.analysisData.ordered_requests || this.analysisData.ordered_requests.length === 0) {
      this.stepsContainer.innerHTML = '<p class="muted" style="text-align:center;">No requests found in this collection.</p>';
      return;
    }

    const nodes = this.analysisData.nodes || [];
    const ordered = this.analysisData.ordered_requests;

    ordered.forEach((req, idx) => {
      const nodeMeta = nodes.find(n => n.id === req.id) || {};
      const consumed = nodeMeta.consumed_variables || [];
      const produced = nodeMeta.produced_variables || [];

      const card = document.createElement('div');
      card.className = 'quest-card';
      card.id = `quest-step-${req.id}`;
      card.innerHTML = `
        <div style="display:flex; align-items:center; flex:1;">
          <div class="quest-step-badge">${idx + 1}</div>
          <div class="quest-info">
            <span class="quest-category">${nodeMeta.category || 'General API'}</span>
            <div class="quest-title">
              <span class="badge-method ${req.method}">${req.method}</span>
              ${req.name}
            </div>
            <div class="quest-url">${req.url}</div>
            <div class="quest-vars">
              ${consumed.map(c => `<span class="var-tag var-in">⬇ Needs: {{${c}}}</span>`).join('')}
              ${produced.map(p => `<span class="var-tag var-out">⬆ Produces: {{${p}}}</span>`).join('')}
            </div>
          </div>
        </div>
        <div class="step-status-indicator">
          <span class="status-badge status-idle">Ready</span>
        </div>
      `;

      this.stepsContainer.appendChild(card);

      if (idx < ordered.length - 1) {
        const arrow = document.createElement('div');
        arrow.className = 'quest-arrow';
        arrow.textContent = '⬇ ⚡ Chained State ⬇';
        this.stepsContainer.appendChild(arrow);
      }
    });
  }

  async runCurrentWorkflow() {
    const colId = this.app.explorer.activeCollectionId;
    if (!colId) {
      return this.app.showToast('Please select a collection first', 'error');
    }

    this.runStatus.className = 'status-badge status-idle';
    this.runStatus.textContent = 'Executing...';
    this.logOutput.textContent = `[QUEST RUNNER] Initializing Game API Pipeline for collection #${colId}...\n`;

    try {
      const result = await apiClient.runWorkflow(colId);
      
      let log = `=== GAME API QUEST COMPLETED ===\n`;
      log += `Total Steps: ${result.total_steps}\n`;
      log += `Timestamp: ${new Date().toLocaleTimeString()}\n\n`;

      result.steps.forEach(step => {
        log += `[STEP ${step.step}] ${step.method} ${step.name}\n`;
        log += `  URL: ${step.url}\n`;
        log += `  Status: ${step.status_code} (${step.elapsed_ms}ms)\n`;
        if (Object.keys(step.extracted || {}).length > 0) {
          log += `  Extracted Variables:\n`;
          for (const [k, v] of Object.entries(step.extracted)) {
            log += `    * ${k} = ${JSON.stringify(v)}\n`;
          }
        }
        if (step.error) {
          log += `  Error: ${step.error}\n`;
        }
        log += `----------------------------------------\n`;

        // Update card status badge
        const stepCard = document.getElementById(`quest-step-${step.request_id}`);
        if (stepCard) {
          const badge = stepCard.querySelector('.step-status-indicator .status-badge');
          if (badge) {
            badge.className = `status-badge ${step.status_code >= 200 && step.status_code < 300 ? 'status-2xx' : 'status-5xx'}`;
            badge.textContent = `${step.status_code} (${step.elapsed_ms}ms)`;
          }
        }
      });

      log += `\n[FINAL ENVIRONMENT VARIABLE STATE]\n`;
      log += JSON.stringify(result.final_variables, null, 2);

      this.logOutput.textContent = log;
      this.runStatus.className = 'status-badge status-2xx';
      this.runStatus.textContent = 'ALL PASSED';
      this.app.showToast(`Quest finished: ${result.total_steps} steps executed`, 'success');

    } catch (err) {
      this.runStatus.className = 'status-badge status-5xx';
      this.runStatus.textContent = 'FAILED';
      this.logOutput.textContent += `\n[FATAL ERROR]: ${err.message}`;
      this.app.showToast(`Workflow execution failed: ${err.message}`, 'error');
    }
  }
}
