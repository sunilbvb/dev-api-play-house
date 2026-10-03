import { apiClient } from '../api_client.js';

export class DocsHubManager {
  constructor(app) {
    this.app = app;
    this.currentDoc = 'readme';
    this.currentSection = 'setup';
    this.init();
  }

  init() {
    this.bindEvents();
  }

  bindEvents() {
    // Sub-nav inside Docs tab
    document.querySelectorAll('.docs-nav-item').forEach(item => {
      item.addEventListener('click', (e) => {
        document.querySelectorAll('.docs-nav-item').forEach(i => i.classList.remove('active'));
        document.querySelectorAll('.docs-section-panel').forEach(p => p.classList.remove('active'));

        const target = item.dataset.docsSection;
        item.classList.add('active');
        const panel = document.getElementById(`docs-sec-${target}`);
        if (panel) panel.classList.add('active');
        this.currentSection = target;

        if (target === 'live_docs') {
          this.loadLiveDoc(this.currentDoc);
        }
      });
    });

    // Doc pills inside live_docs section
    document.querySelectorAll('.doc-pill-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        document.querySelectorAll('.doc-pill-btn').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentDoc = btn.dataset.docFile;
        this.loadLiveDoc(this.currentDoc);
      });
    });

    // Copy live doc button
    const btnCopyDoc = document.getElementById('btn-copy-live-doc');
    if (btnCopyDoc) {
      btnCopyDoc.addEventListener('click', () => {
        const text = document.getElementById('live-doc-raw').textContent;
        navigator.clipboard.writeText(text);
        this.app.showToast('Copied document markdown to clipboard!', 'success');
      });
    }

    // Quick copy command buttons
    document.querySelectorAll('.btn-quick-copy').forEach(btn => {
      btn.addEventListener('click', () => {
        const cmd = btn.dataset.copyCmd;
        navigator.clipboard.writeText(cmd);
        this.app.showToast(`Copied: ${cmd}`, 'success');
      });
    });
  }

  async loadLiveDoc(docName) {
    const rawEl = document.getElementById('live-doc-raw');
    const titleEl = document.getElementById('live-doc-title');
    const pathEl = document.getElementById('live-doc-path');

    if (!rawEl) return;
    rawEl.textContent = 'Loading document...';

    try {
      const res = await apiClient.getDocContent(docName);
      if (titleEl) titleEl.textContent = `${docName.toUpperCase()}.md`;
      if (pathEl) pathEl.textContent = res.path || '';
      rawEl.textContent = res.content || '// Empty document';
    } catch (err) {
      rawEl.textContent = `Error loading document: ${err.message}`;
      this.app.showToast(`Failed to load ${docName}: ${err.message}`, 'error');
    }
  }
}
