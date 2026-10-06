import { apiClient } from '../api_client.js';

export class OmniSearch {
  constructor(app) {
    this.app = app;
    this.modalEl = document.getElementById('modal-omni-search');
    this.inputEl = document.getElementById('omni-search-input');
    this.resultsListEl = document.getElementById('omni-search-results');
    this.countEl = document.getElementById('omni-results-count');
    this.previewDrawerEl = document.getElementById('omni-preview-drawer');
    this.activeFilter = 'all';
    this.debounceTimer = null;
    this.currentResults = [];

    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // Keyboard shortcut: Ctrl+K or Cmd+K
    window.addEventListener('keydown', (e) => {
      if ((e.ctrlKey || e.metaKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        this.open();
      } else if (e.key === 'Escape' && this.isOpen()) {
        this.close();
      }
    });

    // Topbar search open button
    const btnOpenSearch = document.getElementById('btn-open-omni-search');
    if (btnOpenSearch) {
      btnOpenSearch.addEventListener('click', () => this.open());
    }

    // Modal close buttons
    document.querySelectorAll('[data-close="modal-omni-search"]').forEach(btn => {
      btn.addEventListener('click', () => this.close());
    });

    // Close on overlay backdrop click
    if (this.modalEl) {
      this.modalEl.addEventListener('click', (e) => {
        if (e.target === this.modalEl) this.close();
      });
    }

    // Search input typing with debounce
    if (this.inputEl) {
      this.inputEl.addEventListener('input', () => {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => this.performSearch(), 180);
      });
    }

    // Filter chips
    document.querySelectorAll('.search-filter-chip').forEach(chip => {
      chip.addEventListener('click', () => {
        document.querySelectorAll('.search-filter-chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        this.activeFilter = chip.dataset.filter || 'all';
        this.renderResults();
      });
    });

    // Close preview drawer button
    const btnCloseDrawer = document.getElementById('btn-close-omni-drawer');
    if (btnCloseDrawer) {
      btnCloseDrawer.addEventListener('click', () => {
        if (this.previewDrawerEl) this.previewDrawerEl.classList.add('hidden');
      });
    }
  }

  isOpen() {
    return this.modalEl && !this.modalEl.classList.contains('hidden');
  }

  open() {
    if (!this.modalEl) return;
    this.modalEl.classList.remove('hidden');
    if (this.previewDrawerEl) this.previewDrawerEl.classList.add('hidden');
    if (this.inputEl) {
      this.inputEl.value = '';
      this.inputEl.focus();
    }
    this.performSearch();
  }

  close() {
    if (!this.modalEl) return;
    this.modalEl.classList.add('hidden');
  }

  async performSearch() {
    const query = this.inputEl ? this.inputEl.value.trim() : '';
    if (this.resultsListEl) {
      this.resultsListEl.innerHTML = '<div class="omni-loading">Searching across endpoints, payloads, variables...</div>';
    }

    try {
      const data = await apiClient.searchApis(query);
      this.currentResults = data.results || [];
      this.renderResults();
    } catch (err) {
      if (this.resultsListEl) {
        this.resultsListEl.innerHTML = `<div class="omni-empty">Search error: ${err.message}</div>`;
      }
    }
  }

  renderResults() {
    if (!this.resultsListEl) return;
    this.resultsListEl.innerHTML = '';

    // Filter results based on active chip
    let filtered = this.currentResults;
    if (this.activeFilter !== 'all') {
      if (['get', 'post', 'put', 'delete', 'patch'].includes(this.activeFilter)) {
        filtered = filtered.filter(r => (r.method || '').toLowerCase() === this.activeFilter);
      } else if (this.activeFilter === 'gates') {
        filtered = filtered.filter(r => (r.category || '').toLowerCase().includes('auth') || (r.category || '').toLowerCase().includes('gate'));
      } else if (this.activeFilter === 'variables') {
        filtered = filtered.filter(r => (r.match_type || '').toLowerCase().includes('variable') || (r.extracts && r.extracts.length > 0));
      }
    }

    if (this.countEl) {
      this.countEl.textContent = `${filtered.length} API${filtered.length === 1 ? '' : 's'} found`;
    }

    if (filtered.length === 0) {
      this.resultsListEl.innerHTML = `
        <div class="omni-empty">
          <span style="font-size:24px;">🔍</span>
          <p>No APIs matched your query & filter.</p>
          <span style="font-size:11px; color:var(--text-muted);">Try searching by endpoint URL, keywords, request body JSON keys, or chained variable names.</span>
        </div>
      `;
      return;
    }

    filtered.forEach(item => {
      const el = document.createElement('div');
      el.className = 'omni-item';
      el.innerHTML = `
        <div class="omni-item-main">
          <div class="omni-item-header">
            <span class="badge-method ${item.method}">${item.method}</span>
            <span class="omni-item-name">${item.name}</span>
            <span class="omni-item-col">📁 ${item.collection_name}</span>
            ${item.category ? `<span class="omni-room-pill">${item.category}</span>` : ''}
          </div>
          <div class="omni-item-url">${item.url}</div>
          ${item.snippet ? `<div class="omni-item-snippet"><span class="match-badge">Matched:</span> ${item.match_type} &mdash; <code>${this.escapeHtml(item.snippet)}</code></div>` : ''}
        </div>
        <div class="omni-item-actions">
          <button class="btn btn-secondary btn-xs btn-omni-test" title="Quick Execute & Preview Output">⚡ Quick Test</button>
          <button class="btn btn-primary btn-xs btn-omni-select" title="Open in Studio">Open &rarr;</button>
        </div>
      `;

      // Click to select & open in Studio
      el.querySelector('.btn-omni-select').addEventListener('click', (e) => {
        e.stopPropagation();
        this.selectAndOpen(item.id);
      });

      // Quick test execution and preview
      el.querySelector('.btn-omni-test').addEventListener('click', (e) => {
        e.stopPropagation();
        this.quickExecute(item);
      });

      // Clicking anywhere on item opens it
      el.addEventListener('click', () => {
        this.selectAndOpen(item.id);
      });

      this.resultsListEl.appendChild(el);
    });
  }

  selectAndOpen(requestId) {
    this.close();
    // Switch to playground tab
    const playTab = document.querySelector('.nav-tab[data-tab="playground"]');
    if (playTab) playTab.click();

    // Select the request in explorer
    if (this.app.explorer) {
      this.app.explorer.selectRequest(requestId);
    }
    this.app.showToast('Opened API in Studio!', 'success');
  }

  async quickExecute(item) {
    if (!this.previewDrawerEl) return;
    this.previewDrawerEl.classList.remove('hidden');

    const titleEl = document.getElementById('omni-drawer-title');
    const badgeEl = document.getElementById('omni-drawer-badge');
    const timeEl = document.getElementById('omni-drawer-time');
    const statusEl = document.getElementById('omni-drawer-status');
    const bodyEl = document.getElementById('omni-drawer-body');

    if (titleEl) titleEl.textContent = `${item.method} ${item.name}`;
    if (badgeEl) badgeEl.textContent = 'Executing...';
    if (timeEl) timeEl.textContent = '...';
    if (statusEl) {
      statusEl.className = 'status-badge status-idle';
      statusEl.textContent = 'Running';
    }
    if (bodyEl) bodyEl.textContent = '// Sending request...';

    try {
      // Find full request details
      const reqObj = this.app.explorer?.requests.find(r => r.id === item.id) || item;
      const res = await apiClient.executeRequest(reqObj);

      const status = res.status_code || 0;
      const ok = status >= 200 && status < 300;
      if (statusEl) {
        statusEl.className = `status-badge ${ok ? 'status-2xx' : 'status-4xx'}`;
        statusEl.textContent = `HTTP ${status}`;
      }
      if (timeEl) timeEl.textContent = `${res.elapsed_ms || 0} ms`;
      if (badgeEl) badgeEl.textContent = ok ? 'Success' : 'Error';

      let bodyText = res.body || '';
      try {
        const parsed = JSON.parse(bodyText);
        bodyText = JSON.stringify(parsed, null, 2);
      } catch (e) {
        // keep text
      }
      if (bodyEl) bodyEl.textContent = bodyText || '// Empty response body';
    } catch (err) {
      if (statusEl) {
        statusEl.className = 'status-badge status-5xx';
        statusEl.textContent = 'Failed';
      }
      if (bodyEl) bodyEl.textContent = `Execution error: ${err.message}`;
    }
  }

  escapeHtml(str) {
    if (!str) return '';
    return str
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#039;');
  }
}
