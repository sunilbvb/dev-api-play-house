import { apiClient } from '../api_client.js';

export class Studio {
  constructor(app) {
    this.app = app;
    this.currentRequest = null;
    this.currentFormat = 'builder';

    // Elements
    this.methodSelect = document.getElementById('req-method');
    this.urlInput = document.getElementById('req-url');
    this.nameInput = document.getElementById('req-name');
    this.bodyText = document.getElementById('req-body-text');
    this.headersList = document.getElementById('headers-list');
    this.extractsList = document.getElementById('extracts-list');

    this.btnSend = document.getElementById('btn-send-request');
    this.btnSave = document.getElementById('btn-save-request');
    this.btnAddHeader = document.getElementById('btn-add-header');
    this.btnAddExtract = document.getElementById('btn-add-extract');
    this.btnBeautify = document.getElementById('btn-beautify-body');

    // Copy buttons
    this.btnCopyReqBody = document.getElementById('btn-copy-req-body');
    this.btnCopyResBody = document.getElementById('btn-copy-res-body');
    this.btnCopyResHeaders = document.getElementById('btn-copy-res-headers');
    this.btnCopyFormat = document.getElementById('btn-copy-format');

    // Views
    this.builderContainer = document.getElementById('builder-container');
    this.formatPreviewContainer = document.getElementById('format-preview-container');
    this.formatCodeContent = document.getElementById('format-code-content');
    this.formatTitle = document.getElementById('format-title');

    // Response
    this.resStatus = document.getElementById('res-status');
    this.resTime = document.getElementById('res-time');
    this.resBodyCode = document.getElementById('res-body-code');
    this.resHeadersCode = document.getElementById('res-headers-code');
    this.extractedVarsView = document.getElementById('extracted-vars-view');

    this.initEvents();
  }

  initEvents() {
    this.btnSend.addEventListener('click', () => this.sendRequest());
    this.btnSave.addEventListener('click', () => this.saveRequest());
    this.btnAddHeader.addEventListener('click', () => this.addHeaderRow('', ''));
    this.btnAddExtract.addEventListener('click', () => this.addExtractRow('', 'body_json', ''));
    this.btnBeautify.addEventListener('click', () => this.beautifyJson());

    const btnFuzz = document.getElementById('btn-fuzz-sidequests');
    if (btnFuzz) {
      btnFuzz.addEventListener('click', async () => {
        if (!this.currentRequest || !this.currentRequest.id) {
          return this.app.showToast('Select an API first to generate side quests', 'error');
        }
        try {
          const res = await apiClient.generateSideQuests(this.currentRequest.id);
          this.app.showToast(`🎯 Spawned 3 boundary Side Quests! (+600 Potential XP)`, 'success');
          await this.app.explorer.loadData();
        } catch (err) {
          this.app.showToast(`Fuzzing failed: ${err.message}`, 'error');
        }
      });
    }

    // Copy handlers
    this.btnCopyReqBody.addEventListener('click', () => this.copyToClipboard(this.bodyText.value, 'Request body copied'));
    this.btnCopyResBody.addEventListener('click', () => this.copyToClipboard(this.resBodyCode.textContent, 'Response body copied'));
    this.btnCopyResHeaders.addEventListener('click', () => this.copyToClipboard(this.resHeadersCode.textContent, 'Response headers copied'));
    this.btnCopyFormat.addEventListener('click', () => this.copyToClipboard(this.formatCodeContent.textContent, 'Code copied'));

    // Format Chips switcher
    document.querySelectorAll('.chip-btn').forEach(btn => {
      btn.addEventListener('click', (e) => {
        document.querySelectorAll('.chip-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.switchFormat(btn.dataset.formatTab);
      });
    });

    // Subtab switchers (Headers, Body, Extracts)
    document.querySelectorAll('.sub-tabs .sub-tab[data-subtab]').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.sub-tabs .sub-tab[data-subtab]').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.subtab-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`subtab-${tab.dataset.subtab}`).classList.add('active');
      });
    });

    // Response Subtabs (Body, Headers, Extracted)
    document.querySelectorAll('.sub-tabs .sub-tab[data-res-tab]').forEach(tab => {
      tab.addEventListener('click', () => {
        document.querySelectorAll('.sub-tabs .sub-tab[data-res-tab]').forEach(t => t.classList.remove('active'));
        document.querySelectorAll('.res-content').forEach(c => c.classList.remove('active'));
        tab.classList.add('active');
        document.getElementById(`res-tab-${tab.dataset.res-tab}`).classList.add('active');
      });
    });
  }

  loadRequest(req) {
    this.currentRequest = req;
    this.nameInput.value = req.name || '';
    this.methodSelect.value = (req.method || 'GET').toUpperCase();
    this.urlInput.value = req.url || '';
    this.bodyText.value = req.body || '';

    // Headers
    this.headersList.innerHTML = '';
    const headers = typeof req.headers === 'object' ? req.headers : {};
    let hCount = 0;
    for (const [k, v] of Object.entries(headers)) {
      this.addHeaderRow(k, v);
      hCount++;
    }
    document.getElementById('header-count').textContent = hCount;

    // Extractions
    this.extractsList.innerHTML = '';
    const extracts = Array.isArray(req.extracts) ? req.extracts : [];
    extracts.forEach(rule => {
      this.addExtractRow(rule.target, rule.source, rule.path);
    });
    document.getElementById('extract-count').textContent = extracts.length;

    // Load documentation
    if (this.app.docs) {
      this.app.docs.loadDocumentation(req.documentation || '');
    }

    // Load test advisor strategy
    if (this.app.advisor) {
      this.app.advisor.loadTestWays(req);
    }

    // If currently viewing code format, refresh it
    if (this.currentFormat !== 'builder') {
      this.switchFormat(this.currentFormat);
    }
  }

  addHeaderRow(key = '', val = '') {
    const row = document.createElement('div');
    row.className = 'kv-row';
    row.innerHTML = `
      <input type="text" class="kv-input kv-key" placeholder="Header Name" value="${key}">
      <input type="text" class="kv-input kv-val" placeholder="Header Value" value="${val}">
      <button class="btn-xs btn-danger kv-del">✕</button>
    `;
    row.querySelector('.kv-del').addEventListener('click', () => {
      row.remove();
      this.updateCounts();
    });
    this.headersList.appendChild(row);
    this.updateCounts();
  }

  addExtractRow(target = '', source = 'body_json', path = '') {
    const row = document.createElement('div');
    row.className = 'kv-row';
    row.innerHTML = `
      <input type="text" class="kv-input ext-target" placeholder="Variable Name (e.g. token)" value="${target}">
      <select class="kv-input ext-source" style="max-width: 140px;">
        <option value="body_json" ${source === 'body_json' ? 'selected' : ''}>Body JSON</option>
        <option value="header" ${source === 'header' ? 'selected' : ''}>Header</option>
        <option value="regex" ${source === 'regex' ? 'selected' : ''}>Regex</option>
        <option value="status" ${source === 'status' ? 'selected' : ''}>Status Code</option>
      </select>
      <input type="text" class="kv-input ext-path" placeholder="Path (e.g. data.token)" value="${path}">
      <button class="btn-xs btn-danger kv-del">✕</button>
    `;
    row.querySelector('.kv-del').addEventListener('click', () => {
      row.remove();
      this.updateCounts();
    });
    this.extractsList.appendChild(row);
    this.updateCounts();
  }

  updateCounts() {
    document.getElementById('header-count').textContent = this.headersList.querySelectorAll('.kv-row').length;
    document.getElementById('extract-count').textContent = this.extractsList.querySelectorAll('.kv-row').length;
  }

  getFormData() {
    const headers = {};
    this.headersList.querySelectorAll('.kv-row').forEach(row => {
      const k = row.querySelector('.kv-key').value.trim();
      const v = row.querySelector('.kv-val').value.trim();
      if (k) headers[k] = v;
    });

    const extracts = [];
    this.extractsList.querySelectorAll('.kv-row').forEach(row => {
      const target = row.querySelector('.ext-target').value.trim();
      const source = row.querySelector('.ext-source').value;
      const path = row.querySelector('.ext-path').value.trim();
      if (target) extracts.push({ target, source, path });
    });

    const docEl = document.getElementById('api-doc-markdown');
    const docContent = docEl ? docEl.value : '';

    return {
      id: this.currentRequest ? this.currentRequest.id : null,
      name: this.nameInput.value.trim() || 'Untitled Request',
      method: this.methodSelect.value,
      url: this.urlInput.value.trim(),
      headers: headers,
      body: this.bodyText.value,
      body_type: 'json',
      extracts: extracts,
      documentation: docContent
    };
  }

  async switchFormat(format) {
    this.currentFormat = format;
    if (format === 'builder') {
      this.builderContainer.classList.remove('hidden');
      this.formatPreviewContainer.classList.add('hidden');
      return;
    }

    this.builderContainer.classList.add('hidden');
    this.formatPreviewContainer.classList.remove('hidden');

    const reqData = this.getFormData();
    try {
      const res = await apiClient.exportApis(format, [reqData]);
      this.formatTitle.textContent = `${format.toUpperCase()} Preview`;
      this.formatCodeContent.textContent = res.content || '';
    } catch (err) {
      this.formatCodeContent.textContent = `Error generating code: ${err.message}`;
    }
  }

  async sendRequest() {
    const reqData = this.getFormData();
    if (!reqData.url) {
      return this.app.showToast('Please specify a URL', 'error');
    }

    this.resStatus.className = 'status-badge status-idle';
    this.resStatus.textContent = 'Sending...';
    this.resTime.textContent = '...';

    try {
      const res = await apiClient.executeRequest({
        request_id: reqData.id,
        name: reqData.name,
        method: reqData.method,
        url: reqData.url,
        headers: reqData.headers,
        body: reqData.body,
        extracts: reqData.extracts
      });

      // Update status tag
      const code = res.status_code;
      this.resStatus.textContent = `${code} ${code >= 200 && code < 300 ? 'OK' : 'RESPONSE'}`;
      this.resStatus.className = `status-badge ${code >= 200 && code < 300 ? 'status-2xx' : code >= 400 && code < 500 ? 'status-4xx' : 'status-5xx'}`;
      this.resTime.textContent = `${res.elapsed_ms} ms`;

      // Update response body
      this.resBodyCode.textContent = res.body || (res.error ? `Error: ${res.error}` : '(Empty response)');

      // Update headers
      const formattedHeaders = Object.entries(res.headers || {})
        .map(([k, v]) => `${k}: ${v}`)
        .join('\n');
      this.resHeadersCode.textContent = formattedHeaders || '(No headers)';

      // Update extracted variables
      const ext = res.extracted_variables || {};
      const keys = Object.keys(ext);
      if (keys.length > 0) {
        this.extractedVarsView.innerHTML = keys.map(k => `
          <div style="margin-bottom:6px;">
            <strong style="color:var(--accent-green); font-family:var(--font-mono);">${k}:</strong> 
            <span style="color:var(--text-bright); font-family:var(--font-mono);">${JSON.stringify(ext[k])}</span>
          </div>
        `).join('');
        this.app.showToast(`Extracted ${keys.length} variable(s) to environment!`, 'success');
      } else {
        this.extractedVarsView.innerHTML = `<p class="muted">No variables extracted in this run.</p>`;
      }

    } catch (err) {
      this.resStatus.className = 'status-badge status-5xx';
      this.resStatus.textContent = 'ERROR';
      this.resBodyCode.textContent = `Network / Execution Error:\n${err.message}`;
    }
  }

  async saveRequest() {
    const data = this.getFormData();
    if (!data.id) {
      return this.app.showToast('No active request selected to save', 'error');
    }

    try {
      await apiClient.updateRequest(data.id, data);
      await this.app.explorer.loadData();
      this.app.showToast('API Request saved successfully', 'success');
    } catch (err) {
      this.app.showToast(`Save failed: ${err.message}`, 'error');
    }
  }

  beautifyJson() {
    try {
      const parsed = JSON.parse(this.bodyText.value);
      this.bodyText.value = JSON.stringify(parsed, null, 2);
      this.app.showToast('JSON beautified', 'success');
    } catch (e) {
      this.app.showToast('Body is not valid JSON', 'error');
    }
  }

  copyToClipboard(text, successMsg) {
    if (!text) {
      return this.app.showToast('Nothing to copy', 'error');
    }
    navigator.clipboard.writeText(text).then(() => {
      this.app.showToast(successMsg, 'success');
    }).catch(err => {
      this.app.showToast('Clipboard copy failed', 'error');
    });
  }
}
