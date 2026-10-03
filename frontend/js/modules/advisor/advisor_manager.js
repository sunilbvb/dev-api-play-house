import { apiClient } from '../api_client.js';

export class AdvisorManager {
  constructor(app) {
    this.app = app;
    this.countBadge = document.getElementById('test-ways-count-badge');
    this.containerEl = document.getElementById('test-ways-scenarios-list');
    this.btnRunAll = document.getElementById('btn-run-all-test-ways');
    this.scoreBadge = document.getElementById('test-matrix-score');

    this.initEvents();
  }

  initEvents() {
    if (this.btnRunAll) {
      this.btnRunAll.addEventListener('click', () => this.runTestMatrix());
    }
  }

  async loadTestWays(req) {
    if (!req || !req.url) return;
    try {
      const analysis = await apiClient.analyzeTestWays({
        request_id: req.id,
        request: req
      });

      if (this.countBadge) {
        this.countBadge.textContent = `${analysis.total_ways} Ways to Test`;
      }

      this.renderScenarios(analysis.scenarios);
    } catch (err) {
      console.warn('Could not load test ways:', err);
    }
  }

  renderScenarios(scenarios) {
    if (!this.containerEl) return;
    this.containerEl.innerHTML = '';

    scenarios.forEach(sc => {
      const card = document.createElement('div');
      card.className = 'test-scenario-card';
      card.id = `sc-${sc.id}`;
      card.innerHTML = `
        <div style="flex:1;">
          <div style="display:flex; align-items:center; gap:8px;">
            <span class="test-sc-title">${sc.name}</span>
            <span class="test-sc-cat">${sc.category}</span>
          </div>
          <p class="test-sc-desc">${sc.description}</p>
          <div class="test-sc-expected">🎯 Expected: <strong>${sc.expected}</strong></div>
        </div>
        <div class="sc-status-box">
          <span class="status-badge status-idle">Ready</span>
        </div>
      `;
      this.containerEl.appendChild(card);
    });
  }

  async runTestMatrix() {
    const currentReq = this.app.studio.getFormData();
    if (!currentReq || !currentReq.url) {
      return this.app.showToast('Select an API with a valid URL to run test matrix', 'error');
    }

    if (this.scoreBadge) {
      this.scoreBadge.textContent = 'Testing...';
      this.scoreBadge.className = 'status-badge status-idle';
    }

    try {
      this.app.showToast('Executing multi-way test matrix...', 'info');
      const res = await apiClient.runTestWays({
        request_id: currentReq.id,
        request: currentReq
      });

      if (this.scoreBadge) {
        this.scoreBadge.textContent = `${res.passed_count}/${res.total_ways} Passed (${res.score_percentage}%)`;
        this.scoreBadge.className = `status-badge ${res.score_percentage >= 70 ? 'status-2xx' : 'status-5xx'}`;
      }

      res.scenarios.forEach(scResult => {
        const card = document.getElementById(`sc-${scResult.id}`);
        if (card) {
          const badge = card.querySelector('.sc-status-box .status-badge');
          if (badge) {
            badge.className = `status-badge ${scResult.passed ? 'status-2xx' : 'status-5xx'}`;
            badge.textContent = `${scResult.passed ? 'PASSED ✅' : 'FAILED ❌'} (${scResult.actual})`;
          }
        }
      });

      this.app.showToast(`Test Matrix finished: ${res.passed_count}/${res.total_ways} passed!`, 'success');
    } catch (err) {
      this.app.showToast(`Test execution failed: ${err.message}`, 'error');
    }
  }
}
